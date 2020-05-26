import pickle
from tqdm import tqdm
import numpy as np
import argparse
import pandas as pd
import csv
from datetime import datetime
from cmath import sin, cos, exp, phase, pi
from math import floor

# ============================================================
# argparse setting
parser = argparse.ArgumentParser(description='Compressed CSI extractor')
parser.add_argument('-i', metavar='INPUT', type=str, required=True, help='Input file name')
parser.add_argument('-a', metavar='ADDRESS', type=str, required=True, help='MAC address of specified transmitting device')
parser.add_argument('-t', choices=['pkl','csv'], default='csv', help='Output file type including Compressed CSI or V matrix value')
parser.add_argument('--raw', action='store_true', help='the option to disable time sanitization')
parser.add_argument('-v', action='store_true', help='the option to get V matrix value')
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
    cbr_bnr = format(int(cbr_hex, 16), f"0{max_length}b")

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

if not args.v:
    if args.t=='pkl':
        with open("csi_orig.pkl", "wb") as f:
            pickle.dump(record, f)
    elif args.t=='csv':
        with open("csi_orig.csv", "a") as f:
            writer = csv.writer(f)
            for k, v in record.items():
                writer.writerow([k, v])
# ============================================================

# ============================================================
# V matrix reconstruction
def calc_v(arr):
    matrix = np.full((3,3), 0+0j)
    phi11, phi21, psi21, psi31, phi22, psi32 = arr

    phi11 = (phi11/32+1/64)*pi
    phi21 = (phi21/32+1/64)*pi
    psi21 = (psi21/32+1/64)*pi
    psi31 = (psi31/32+1/64)*pi
    phi22 = (phi22/32+1/64)*pi
    psi32 = (psi32/32+1/64)*pi

    matrix[0][0] = cos(psi31) * exp(1j*phi11) * cos(psi21)
    matrix[0][1] = -cos(psi32) * exp(1j*phi22) * exp(1j*phi11) * sin(psi21) - sin(psi32) * sin(psi31) * exp(1j*phi11) * cos(psi21)
    matrix[0][2] = sin(psi32) * exp(1j*phi22) * exp(1j*phi11) * sin(psi21) - cos(psi32) * sin(psi31) * exp(1j*phi11) * cos(psi21)
    matrix[1][0] = cos(psi31) * exp(1j*phi21) * sin(psi21)
    matrix[1][1] = cos(psi32) * exp(1j*phi22) * exp(1j*phi21) * cos(psi21) - sin(psi32) * sin(psi31) * exp(1j*phi21) * sin(psi21)
    matrix[1][2] = -sin(psi32) * exp(1j*phi22) * exp(1j*phi21) * cos(psi21) - cos(psi32) * sin(psi31) * exp(1j*phi21) * sin(psi21)
    matrix[2][0] = sin(psi31)
    matrix[2][1] = cos(psi31) * sin(psi32)
    matrix[2][2] = cos(psi31) * cos(psi32)

    return (phase(matrix[0][0]/matrix[0][1]))

vmat = []
for k, v in cbrs.items():
    tmp = []
    for i in range(subc):
        mat = round(calc_v(v[i*6:(i+1)*6]), 2)
        if mat<0:
            mat = mat+3.14
        if mat==3.14:
            mat = 0
        mat = floor(mat * 100) / 100
        tmp.append(mat)
    vmat.append([k,tmp])

if args.t=='pkl':
    with open("vmat.pkl", "wb") as f:
        pickle.dump(vmat, f)
elif args.t=='csv':
    with open("vmat.csv", "w") as f:
        writer = csv.writer(f)
        for item in vmat:
            writer.writerow(item)
