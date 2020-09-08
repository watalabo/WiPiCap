import pickle
from tqdm import tqdm
import numpy as np
import argparse
import pandas as pd
import csv
from datetime import datetime, timedelta
from cmath import sin, cos, exp, phase, pi
from math import floor
import sys

# ============================================================
# argparse setting
parser = argparse.ArgumentParser(description='Compressed CSI extractor')
parser.add_argument('-i', metavar='INPUT', type=str, required=True, help='Input file name')
parser.add_argument('-a', metavar='ADDRESS', type=str, required=True, help='MAC address of specified transmitting device')
parser.add_argument('-t', choices=['pkl','csv'], default='csv', help='Output file type including Compressed CSI or V matrix value')
parser.add_argument('--raw', action='store_true', help='the option to disable time sanitization')
args = parser.parse_args()
# ============================================================

# ============================================================
cbrs = {}

pkt = pd.read_csv(args.i, header=0)

for item in pkt.itertuples(name=None):
    timestamp = item[1]
    ta = item[2]
    nc = int(item[3], 16)+1
    nr = int(item[4], 16)+1
    if (nc, nr)!=(3,3) and (nc, nr)!=(2, 3):
        raise Exception("not compatible antenna set")
    beamforming_report = item[5]
    codebook = int(item[6], 16)
    chanwidth = int(item[8], 16)
    asnr = nc

    if codebook == 0:
        phi_size = 4
        psi_size = 2
    else:
        phi_size = 6
        psi_size = 4

    if chanwidth==0: subc=52
    elif chanwidth==1: subc=108
    elif chanwidth==2: subc=234

    cbr_hex = beamforming_report[asnr*2:]
    max_length = len(format(int("f" * len(cbr_hex), 16), 'b'))
    print(max_length)
    # cbr_bnr = format(int(cbr_hex, 16), f"0{max_length}b")
    cbr_bnr = int(cbr_hex, 16)
    cbr_bnr = bin(cbr_bnr)
    cbr_bnr = str(cbr_bnr).ljust(max_length, '0')

    if ta==args.a:
        for item in timestamp.split(" "):
            if ":" in item:
                timestamp = item
        if not args.raw:
            timestamp = timestamp[:10]
        else:
            timestamp = timestamp[:15]
        timestamp = datetime.strptime(timestamp, '%H:%M:%S.%f')
        data_size = phi_size*3 + psi_size*3
        csis = []
        for i in range(0, max_length, data_size):
            d = cbr_bnr[i:i + data_size]
            if len(d) != data_size:
                break
            csis.append(int(d[:6],2))
            csis.append(int(d[6:12],2))
            csis.append(int(d[12:16],2))
            csis.append(int(d[16:20],2))
            csis.append(int(d[20:26],2))
            csis.append(int(d[26:],2))
        cbrs[timestamp] = csis

if not args.raw:
    k = sorted(cbrs.keys())

    start_time = k[0]
    end_time = k[-1]

    value = []
    timestamp = start_time

    print(start_time, end_time)

    while timestamp!=end_time:
        print(timestamp)
        if timestamp in cbrs:
            value.append(cbrs[timestamp])
        else:
            value.append(value[-1])
            cbrs[timestamp] = value[-1]
        timestamp = timestamp + timedelta(milliseconds=100)

if args.t=='pkl':
    with open("comp_feedback.pkl", "wb") as f:
        pickle.dump(cbrs, f)
elif args.t=='csv':
    with open("comp_feedback.csv", "w") as f:
        writer = csv.writer(f)
        for k, v in sorted(cbrs.items(), key=lambda x:x[0]):
            writer.writerow([k, v])