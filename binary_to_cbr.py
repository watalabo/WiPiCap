import numpy as np
import argparse
import pandas as pd
import pickle
from datetime import datetime, timedelta
from tools import *

# argparse setting
parser = argparse.ArgumentParser(description='Compressed CSI extractor')
parser.add_argument('-i', metavar='INPUT', type=str, required=True, help='Input file name')
parser.add_argument('-a', metavar='ADDRESS (with colons)', type=str, required=True,help='Mac Address (with colons)')
parser.add_argument('-s', metavar='START', type=str, required=True,help='Start time (%Y%m%d%H%M%S)')
parser.add_argument('-e', metavar='END', type=str, required=True,help='End time (%Y%m%d%H%M%S)')
args = parser.parse_args()

# Read Input CSV
pkt = pd.read_csv('{}'.format(args.i))
pkt['frame.time'] = pkt['frame.time'].apply(lambda x: datetime.strptime(x[:24], '%b %d, %Y %H:%M:%S.%f'))
pkt = pkt[pkt['wlan.ta']==args.a]

# Initialize Communication Channel
ta = pkt.at[pkt.index[1], 'wlan.ta']
nc = int(pkt.at[pkt.index[1], 'wlan.vht.mimo_control.ncindex'], 16)+1
nr = int(pkt.at[pkt.index[1], 'wlan.vht.mimo_control.nrindex'], 16)+1
codebook = int(pkt.at[pkt.index[1], 'wlan.vht.mimo_control.codebookinfo'], 16)
chanwidth = int(pkt.at[pkt.index[1], 'wlan.vht.mimo_control.chanwidth'], 16)
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

start_time = datetime.strptime(args.s, '%Y%m%d%H%M%S')
end_time = datetime.strptime(args.e, '%Y%m%d%H%M%S')

# eliminate unnecessary columns
pkt = pkt.drop(['wlan.ta','wlan.vht.mimo_control.ncindex', 'wlan.vht.mimo_control.nrindex', 'wlan.vht.mimo_control.codebookinfo', 'wlan.vht.mimo_control.chanwidth'], axis=1)
# slice target time
pkt = pkt[(pkt['frame.time']>start_time) & (pkt['frame.time']<end_time)].drop_duplicates(subset='frame.time').set_index('frame.time')

# print channel information
print('''
    [WiPiCap]
    Time: {} -> {}
    Nc: {}
    Nr: {}
    Subcarriers: {}
'''.format(start_time, end_time, nc, nr, subc))

# Intialize angles split rule
if (nr,nc) == (2,1) or (nr,nc) == (2,2):
    split_rule = [0, phi_size, phi_size+psi_size]
    data_size = phi_size+psi_size
elif (nr,nc) == (nr,nc) ==(3,1):
    split_rule = [0, phi_size, 2*phi_size, 2*phi_size+psi_size, 2*phi_size+2*psi_size]
    data_size = 2*phi_size+2*psi_size
elif (nr,nc) == (3,2) or (nr,nc) ==(3,3):
    split_rule = [0, phi_size, 2*phi_size, 2*phi_size+psi_size, 2*phi_size+2*psi_size, 3*phi_size+2*psi_size, 3*phi_size+3*psi_size]
    data_size = 3*phi_size+3*psi_size
else:
    raise Exception('Uncompatible Antenna Set')

# Convert Beamforming Report to phis and psis
def convert_beamforming_to_angles(beamforming_report, asnr, phi_size, psi_size, subc, data_size, split_rule):
    # Convert HEX Compressed Beamforming Report to full length binary
    cbr_hex = beamforming_report[asnr*2:]
    cbr_bnr_littleendian = ''.join([format(int(i, 16), '04b') for i in list(cbr_hex)])
    # Convert little endian to big endian for every 8 bits
    cbr_bnr = ''.join([cbr_bnr_littleendian[i:i+8][::-1] for i in range(0,len(cbr_bnr_littleendian),8)])
    # Get phis and psis
    max_length = subc * data_size
    cbr_bnr = cbr_bnr[:max_length]
    csis = []
    try:
        for i in range(0, max_length, data_size):
            d = cbr_bnr[i:i + data_size]
            for idx in range(len(split_rule)-1):
                angle_dec = int(d[split_rule[idx]:split_rule[(idx+1)]],2)
                csis.append(angle_dec)
    except Exception as e: # Ignore different channel width contamination
        print(e)
    finally:
        return pd.Series(csis)

angles = pkt['wlan.vht.compressed_beamforming_report'].apply(lambda x: convert_beamforming_to_angles(x, asnr, phi_size, psi_size, subc, data_size, split_rule)).values

np.savetxt('compressed_beamforming_report.csv', angles, delimiter=",", fmt='%0.0f')