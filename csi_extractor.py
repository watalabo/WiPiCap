import pickle
from tqdm import tqdm
import numpy as np
import argparse
import pandas as pd
import csv
from datetime import datetime
from time import perf_counter

start = perf_counter()

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', type=str, required=True)
parser.add_argument('--address', type=str)
parser.add_argument('-t', '--type', default='pkl', type=str)
parser.add_argument('--raw', action='store_true')
args = parser.parse_args()

record = {}

pkt = pd.read_csv(args.input, header=0)

for item in tqdm(pkt.itertuples(name=None)):
    timestamp = item[1]
    ta = item[2]
    nc = int(item[3], 16)+1
    nr = int(item[4], 16)+1
    beamforming_report = item[5]
    codebook = int(item[6], 16)
    asnr = nc

    if codebook == 0:
        phi_size = 4
        psi_size = 2
    else:
        phi_size = 6
        psi_size = 4

    cbr_hex = beamforming_report[asnr*2:]
    max_length = len(format(int("f" * len(cbr_hex), 16), 'b'))
    cbr_int = int(cbr_hex, 16)
    cbr_bnr = format(int(cbr_hex, 16), f"0{max_length}b")

    if ta==args.address:
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
        record[timestamp] = csis

if args.type=='pkl':
    with open("csi_orig.pkl", "wb") as f:
        pickle.dump(record, f)
elif args.type=='csv':
    with open("csi_orig.csv", "w") as f:
        writer = csv.writer(f)
        for k, v in record.items():
            writer.writerow([k, v])

print(perf_counter()-start)
