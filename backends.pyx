# Author: S. Kato (Graduate School of Information Technology and Science, Osaka University)
# Version: 3.0
# License: MIT License

# cython: linetrace=True
import cython
from datetime import datetime
from loguru import logger
import re

import numpy as np
import pyshark
from tqdm import tqdm

cimport numpy as cnp
from libc.stdint cimport uint8_t

ctypedef cnp.float64_t DOUBLE
ctypedef cnp.int64_t INT64

cdef double PI = np.pi


hex_to_bin = str.maketrans(
    {
        "0": "0000",
        "1": "0001",
        "2": "0010",
        "3": "0011",
        "4": "0100",
        "5": "0101",
        "6": "0110",
        "7": "0111",
        "8": "1000",
        "9": "1001",
        "a": "1010",
        "b": "1011",
        "c": "1100",
        "d": "1101",
        "e": "1110",
        "f": "1111",
    }
)


def get_v_matrix(pcap_file, address, num_to_process=None, verbose=False):
    p = pyshark.FileCapture(
        pcap_file,
        display_filter=f"wlan.fc.type_subtype == 0x000e && wlan.ta == {address}",
        use_json=True,
        include_raw=True
    )._packets_from_tshark_sync()

    # parameter setting
    phi_psi_matching = [(4.0, 2.0), (6.0, 4.0)]

    # sequentially process packets
    ts = []
    vs = []
    p_cnt = 0

    while True:
        try:
            packet = p.__next__()
        except StopIteration:
            break

        p_cnt += 1
        if num_to_process is not None and p_cnt > num_to_process:
            break
        if verbose:
            logger.info(f"parsing {p_cnt} packets...")

        raw_hex = packet.frame_raw.value

        # get values
        timestamp = float(packet.frame_info.time_epoch)

        # check VHT or HE
        category_code = int(raw_hex[96:98], 16)
        if category_code == 21:
            # VHT
            mimo_control_end_idx = 106
            he_mimo_control = hex_flip(raw_hex[100:mimo_control_end_idx])
            he_mimo_control_bin = bin(int(he_mimo_control, 16))[2:].zfill(24)
            codebook_info = int(he_mimo_control_bin[13], 2)
            bw = int(he_mimo_control_bin[16:18], 2)
            nr = int(he_mimo_control_bin[18:21], 2) + 1
            nc = int(he_mimo_control_bin[21:], 2) + 1
        elif category_code == 30:
            # HE
            mimo_control_end_idx = 110
            he_mimo_control = hex_flip(raw_hex[100:mimo_control_end_idx])
            he_mimo_control_bin = bin(int(he_mimo_control, 16))[2:].zfill(40)
            ru_end_index = int(he_mimo_control_bin[11:17], 2)
            ru_start_index = int(he_mimo_control_bin[17:23], 2)
            codebook_info = int(he_mimo_control_bin[30], 2)
            bw = int(he_mimo_control_bin[32:34], 2)
            nr = int(he_mimo_control_bin[34:37], 2) + 1
            nc = int(he_mimo_control_bin[37:], 2) + 1

        num_snr = nc
        (phi_size, psi_size) = phi_psi_matching[codebook_info]
        cbr_hex = hex_flip(raw_hex[mimo_control_end_idx : -8])

        # calc binary splitting rule
        angle_bits_order = []
        angle_type = []
        angle_index = []
        phi_indices = [0, 0]
        psi_indices = [1, 0]

        angle_bits_order_len = min([nc, nr - 1]) * (2 * (nr - 1) - min(nc, nr - 1) + 1)
        cnt = nr - 1
        while len(angle_bits_order) < angle_bits_order_len:
            for i in range(cnt):
                angle_bits_order.append(phi_size)
                angle_type.append("phi")
                angle_index.append([phi_indices[0] + i, phi_indices[1]])
            phi_indices[0] += 1
            phi_indices[1] += 1
            for i in range(cnt):
                angle_bits_order.append(psi_size)
                angle_type.append("psi")
                angle_index.append([psi_indices[0] + i, psi_indices[1]])
            psi_indices[0] += 1
            psi_indices[1] += 1
            cnt -= 1

        num_subc = int(
            (len(cbr_hex) - num_snr * 2)
            * 4
            // (phi_size * angle_type.count("phi") + psi_size * angle_type.count("psi"))
        )

        split_rule = np.zeros(angle_bits_order_len + 1)
        split_rule[1:] = np.cumsum(angle_bits_order)
        split_rule = split_rule.astype(np.int32)
        angle_seq_len = split_rule[-1]
        cbr, snr = hex_to_quantized_angle(
            cbr_hex, num_snr, num_subc, angle_seq_len, split_rule
        )

        # V matrix recovery
        v = np.zeros((num_subc, nr, nc), dtype=complex)
        subc_len = len(angle_type)
        for subc in range(num_subc):
            angle_slice = cbr[subc * subc_len : (subc + 1) * subc_len]
            angle_slice = [quantized_angle_formulas(t, a, phi_size, psi_size) for t, a in zip(angle_type, angle_slice)]
            mat_e = inverse_givens_rotation(
                nr, nc, angle_slice, angle_type, angle_index
            )
            v[subc] = mat_e
            # check if v is unitary
            assert np.all((np.sum(np.abs(mat_e)**2, axis=0)-1)<1e-5), f"v is not unitary {np.sum(np.abs(mat_e)**2, axis=0)}"
        vs.append(v[np.newaxis])
        ts.append(timestamp)

    vs = np.concatenate(vs)
    ts = np.array(ts)

    if verbose:
        logger.info(f'{ts.shape[0]} packets are parsed.')

    return ts, vs

cdef hex_to_quantized_angle(
    str cbr_hex,
    int num_snr,
    int num_subc,
    int angle_seq_len,
    cnp.ndarray[int] split_rule,
):
    cdef:
        str cbr_bin, snr_bin
        list cbr_subc_split, angle_dec, hex_split
        list cbr = []
        list snr = []
        int snr_idx, i, start, max_length
        cnp.ndarray[int] angle_bits_order

    cbr_bin = cbr_hex.translate(hex_to_bin)[::-1]

    for i in range(num_snr):
        snr_bin = cbr_bin[i * 8 : (i + 1) * 8][::-1]
        if snr_bin[0] == "0":
            snr_idx = <int>int(snr_bin, 2)
        else:
            snr_idx = -(<int>int(snr_bin, 2) ^ 0b11111111)
        snr.append(-(-128 - snr_idx) * 0.25 - 10)

    cbr_bin = cbr_bin[num_snr * 8 :]
    max_length = num_subc * angle_seq_len
    angle_bits_order = split_rule[1:] - split_rule[:-1]

    for s in [cbr_bin[i : i + angle_seq_len] for i in range(0, max_length, angle_seq_len)]:
        if len(s) != split_rule[-1]:
            continue
        angle_dec = [None] * (len(angle_bits_order) - 1)
        start = 0
        for i in range(1, len(angle_bits_order)):
            angle_dec[i - 1] = <int>int(s[start : start + angle_bits_order[i]], 2)
            start += angle_bits_order[i]

        cbr.extend(angle_dec)

    return cbr, snr


cdef inverse_givens_rotation(int nrx, int ntx, list angles, list angle_types, list angle_indices):
    cdef:
        cnp.ndarray[complex, ndim=2] mat_e = np.eye(N=nrx, M=ntx, dtype=complex)
        cnp.ndarray[complex, ndim=2] d_li = np.eye(N=nrx, M=nrx, dtype=complex)
        cnp.ndarray[complex, ndim=2] g_li = np.eye(nrx, nrx, dtype=complex)
        INT64 d_count = 0
        INT64 d_patience = 1
        INT64 idx
        str a_t
        list a_i
        DOUBLE cos_val, sin_val

    reverse_mat = []
    for idx in reversed(range(len(angles))):
        a_t = angle_types[idx]
        a_i = angle_indices[idx]

        if a_t == "phi":
            d_li[a_i[0], a_i[0]] = np.exp(1j * angles[idx])
            d_count += 1
        elif a_t == "psi":
            cos_val = np.cos(angles[idx])
            sin_val = np.sin(angles[idx])
            g_li[a_i[1], a_i[1]] = cos_val
            g_li[a_i[1], a_i[0]] = sin_val
            g_li[a_i[0], a_i[1]] = -sin_val
            g_li[a_i[0], a_i[0]] = cos_val
            mat_e = g_li.T @ mat_e
            g_li = np.eye(nrx, nrx, dtype=complex)
        else:
            raise ValueError("inverse_givens_rotation(): invalid angle type")
        
        if d_count == d_patience:
            mat_e = d_li.T @ mat_e
            d_patience += 1
            d_count = 0
            d_li = np.eye(nrx, nrx, dtype=complex)

    return mat_e


cdef quantized_angle_formulas(str angle_type, int angle, int phi_size, int psi_size):
    angle_funcs = {
        "phi": lambda x: PI * x / (2.0 ** (phi_size - 1.0)) + PI / (2.0 ** (phi_size)),
        "psi": lambda x: PI * x / (2.0 ** (psi_size + 1.0))
        + PI / (2.0 ** (psi_size + 2.0)),
    }
    return angle_funcs[angle_type](angle)


cdef hex_flip(str hex_str):
    return "".join(reversed([hex_str[i : i + 2] for i in range(0, len(hex_str), 2)]))