# cython: linetrace=True
from collections import deque
import cython
from datetime import datetime
import logging
import math
import re

import numpy as np
import pandas as pd
import pyshark
from tqdm import tqdm

cimport numpy as cnp
from libc.stdint cimport uint8_t

ctypedef cnp.float64_t DOUBLE
ctypedef cnp.int64_t INT64

cdef double PI = np.pi

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)



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


def pcap_to_data_columns(pcap_file, address, bw):
    p = pyshark.FileCapture(
        pcap_file,
        display_filter=f"wlan.fc.type_subtype == 0x000e && wlan.ta == {address}",
    )
    logging.info(f'{pcap_file} load succeed.')

    # parameter setting
    phi_psi_matching = [(4.0, 2.0), (6.0, 4.0)]
    subc_matching = [52, 108, 234]
    bw_matching = [20, 40, 80]

    # sequentially process packets
    (
        timestamp_l,
        nr_l,
        nc_l,
        phi_size_l,
        psi_size_l,
        num_subc_l,
        cbr_l,
        angle_type_l,
        angle_index_l,
        snr_l,
    ) = ([], [], [], [], [], [], [], [], [], [])
    logging.info("loading packet data")
    for i, packet in enumerate(tqdm(p)):
        # get values
        timestamp = datetime.fromtimestamp(float(packet.frame_info.time_epoch))
        nc = int(packet["wlan.mgt"].wlan_vht_mimo_control_ncindex, 16) + 1
        nr = int(packet["wlan.mgt"].wlan_vht_mimo_control_nrindex, 16) + 1
        codebook = int(packet["wlan.mgt"].wlan_vht_mimo_control_codebookinfo, 16)
        chanwidth = int(packet["wlan.mgt"].wlan_vht_mimo_control_chanwidth, 16)
        if bw_matching[chanwidth]!=bw:
            continue
        num_snr = nc
        (phi_size, psi_size) = phi_psi_matching[codebook]
        num_subc = subc_matching[chanwidth]
        cbr_hex = packet["wlan.mgt"].wlan_vht_compressed_beamforming_report.replace(
            ":", ""
        )

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

        split_rule = np.zeros(angle_bits_order_len + 1)
        split_rule[1:] = np.cumsum(angle_bits_order)
        split_rule = split_rule.astype(np.int32)
        angle_seq_len = split_rule[-1]
        cbr, snr = binary_to_quantized_angle(
            cbr_hex, num_snr, num_subc, angle_seq_len, split_rule
        )

        # append
        timestamp_l.append(timestamp)
        nc_l.append(nc)
        nr_l.append(nr)
        num_subc_l.append(num_subc)
        cbr_l.append(cbr)
        snr_l.append(snr)
        phi_size_l.append(phi_size)
        psi_size_l.append(psi_size)
        angle_type_l.append(angle_type)
        angle_index_l.append(angle_index)

    return (
            timestamp_l,
            nr_l,
            nc_l,
            phi_size_l,
            psi_size_l,
            num_subc_l,
            angle_type_l,
            angle_index_l,
            cbr_l,
            snr_l,
    )


cdef binary_to_quantized_angle(
    str binary,
    int num_snr,
    int num_subc,
    int angle_seq_len,
    cnp.ndarray[int] split_rule,
):
    cdef:
        str cbr_hex_join, cbr_bin, snr_bin
        list cbr_subc_split, angle_dec, hex_split
        list cbr = []
        list snr = []
        int snr_idx, i, start, max_length
        cnp.ndarray[int] angle_bits_order

    hex_split = re.findall(r"..", binary)[::-1]
    cbr_hex_join = "".join(hex_split)
    cbr_bin = cbr_hex_join.translate(hex_to_bin)[::-1]

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


def get_v_matrix(pcap_file, address, bw, verbose=False):
    
    (
        timestamp_l,
        nr_l,
        nc_l,
        phi_size_l,
        psi_size_l,
        num_subc_l,
        angle_type_l,
        angle_index_l,
        cbr_l,
        snr_l,
    ) = pcap_to_data_columns(pcap_file, address, bw)

    if verbose:
        print(f'{len(timestamp_l)} packets parsed')

    logging.info("Extracting V matrix")
    vs = []
    for c in tqdm(range(len(timestamp_l))):
        num_subc, nr, nc = num_subc_l[c], nr_l[c], nc_l[c]
        phi_size, psi_size = phi_size_l[c], psi_size_l[c]
        angle_type, angle_index = angle_type_l[c], angle_index_l[c]
        v = np.zeros((num_subc, nr, nc), dtype=complex)
        subc_len = len(angle_type)
        cbr = cbr_l[c]
        for subc in range(num_subc):
            angle_slice = cbr[subc * subc_len : (subc + 1) * subc_len]
            angle_slice = [quantized_angle_formulas(t, a, phi_size, psi_size) for t, a in zip(angle_type, angle_slice)]
            mat_e = inverse_givens_rotation(
                nr, nc, angle_slice, angle_type, angle_index
            )
            v[subc, ...] = mat_e
            # check if v is unitary
            assert np.all((np.sum(np.abs(mat_e)**2, axis=0)-1)<1e-5), f"v is not unitary {np.sum(np.abs(mat_e)**2, axis=0)}"
        vs.append(v[np.newaxis, ...])

    vs = np.concatenate([v for v in vs], axis=0)
    return vs
