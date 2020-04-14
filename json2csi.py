from json import JSONDecoder
import pickle
import collections
from glob import glob
from tqdm import tqdm
import numpy as np
import sys

argvs = sys.argv
ta_addr = argvs[1]    # transmitter address refered like "XX:XX:XX:XX:XX:XX"
# ===============================
# wlanという重複したキーが存在するのでそれに対処するための関数
def make_unique(key, dct):
    counter = 0
    unique_key = key

    while unique_key in dct:
        counter += 1
        unique_key = '{}_{}'.format(key, counter)
    return unique_key


def parse_object_pairs(pairs):
    dct = {}
    for key, value in pairs:
        if key in dct:
            key = make_unique(key, dct)
        dct[key] = value

    return dct
# ================================

decoder = JSONDecoder(object_pairs_hook=parse_object_pairs)
file_list = sorted(glob('./*.json'))

record = []

for item in tqdm(file_list):
    print("Now processing --> ",item)
    with open(item, "r") as f:
        raw = f.read()
        data_list = decoder.decode(raw)

    for data in data_list:
        try:
            wlan_da = data["_source"]["layers"]["wlan"]["wlan.da"]  # dst
            wlan_ta = data["_source"]["layers"]["wlan"]["wlan.ta"]  # src
            captured_at = data["_source"]["layers"]["frame"]["frame.time"]
            nc_index = data["_source"]["layers"]["wlan_mgt"][
                "Fixed parameters"]["wlan.vht.mimo_control.control_tree"][
                    "wlan.vht.mimo_control.ncindex"]
            nr_index = data["_source"]["layers"]["wlan_mgt"][
                "Fixed parameters"]["wlan.vht.mimo_control.control_tree"][
                    "wlan.vht.mimo_control.nrindex"]
            compressed_beamforming_report = data["_source"]["layers"][
                "wlan_mgt"]["Fixed parameters"][
                    "wlan.vht.compressed_beamforming_report"]
            asnr = data["_source"]["layers"]["wlan_mgt"]["Fixed parameters"][
                "wlan.vht.compressed_beamforming_report_tree"][
                    "Average Signal to Noise Ratio"]
        except Exception:
            nc_index = data["_source"]["layers"]["wlan_1"]["Fixed parameters"][
                "wlan.vht.mimo_control.control_tree"][
                    "wlan.vht.mimo_control.ncindex"]
            nr_index = data["_source"]["layers"]["wlan_1"]["Fixed parameters"][
                "wlan.vht.mimo_control.control_tree"][
                    "wlan.vht.mimo_control.nrindex"]
            compressed_beamforming_report = data["_source"]["layers"][
                "wlan_1"]["Fixed parameters"][
                    "wlan.vht.compressed_beamforming_report"]
            asnr = data["_source"]["layers"]["wlan_1"]["Fixed parameters"][
                "wlan.vht.compressed_beamforming_report_tree"][
                    "Average Signal to Noise Ratio"]
        asnr_count = len(asnr.keys())

        nc_index = int(nc_index, 16) + 1
        nr_index = int(nr_index, 16) + 1

        if nc_index == 1 and nr_index == 2:
            phi_size = 4
            psi_size = 2
        elif nc_index == 2 and nr_index == 3:
            phi_size = 6
            psi_size = 4
        elif nc_index == 3 and nr_index == 3:
            phi_size = 6
            psi_size = 4
        else:
            continue

        cbr_hex = ''.join(compressed_beamforming_report.split(':')[asnr_count:])
        max_length = len(format(int("f" * len(cbr_hex), 16), 'b'))
        cbr_int = int(cbr_hex, 16)
        cbr_bnr = format(int(cbr_hex, 16), f"0{max_length}b")

        if wlan_ta==ta_addr:
            timestamp = data["_source"]["layers"]["frame"]["frame.time"]
            timestamp = timestamp.split(" ")[3][:10]
            print(timestamp)
            data_size = phi_size*3 + psi_size*3
            csis = []
            for i in range(0, max_length, data_size):
                d = cbr_bnr[i:i + data_size]
                if len(d) != data_size:
                    break
                csis.append(int(d[:6],2)/63)
                csis.append(int(d[6:12],2)/63)
                csis.append(int(d[12:16],2)/15)
                csis.append(int(d[16:20],2)/15)
                csis.append(int(d[20:26],2)/63)
                csis.append(int(d[26:],2)/15)

            record.append([timestamp, csis])

record.sort()

with open("csi_orig.pkl", "wb") as f:
    pickle.dump(record, f)
