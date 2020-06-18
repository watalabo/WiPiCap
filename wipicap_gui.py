import PySimpleGUI as sg
import subprocess
import pickle
from tqdm import tqdm
import numpy as np
import argparse
import pandas as pd
import csv
from datetime import datetime
from cmath import sin, cos, exp, phase, pi
from math import floor
import sys

# ============================================================
def conversion(file_name, address, file_type, raw_time, v_matrix):
    file_path = file_name.split(".")[-2]
    save_path = ("/").join(file_path.split("/")[:-1])
    # pcap to csv
    command = "/usr/local/bin/tshark -r {}.pcap -Y wlan.fc.type_subtype==0x000e -T fields -e frame.time -e wlan.da -e wlan.vht.mimo_control.ncindex -e wlan.vht.mimo_control.nrindex -e wlan.vht.compressed_beamforming_report -e wlan.vht.mimo_control.codebookinfo -e wlan.vht.mimo_control.grouping -e wlan.vht.mimo_control.chanwidth -E header=y -E separator=, -E quote=d".format(file_path)
    print(command)
    subprocess.run(command.split(" "), stdout=open(file_path+".csv", "w"))

    # csv analisys
    cbrs = {}

    pkt = pd.read_csv(file_path+".csv", header=0)
    pkt_size = len(pkt)

    progress_index = 0

    for item in pkt.itertuples(name=None):
        sg.OneLineProgressMeter('Executing...', progress_index+1, pkt_size, 'progmeter', orientation="h")
        progress_index += 1
        
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
        cbr_bnr = format(int(cbr_hex, 16), f"0{max_length}b")

        if ta==address:
            for item in timestamp.split(" "):
                if ":" in item:
                    timestamp = item
            if not raw_time:
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

    window.close()

    if not v_matrix:
        if file_type=='Pickle':
            with open("{}/csi_orig.pkl".format(save_path), "wb") as f:
                pickle.dump(cbrs, f)
        elif file_type=='CSV':
            with open("{}/csi_orig.csv".format(save_path), "w") as f:
                writer = csv.writer(f)
                for k, v in cbrs.items():
                    writer.writerow([k, v])

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

    if v_matrix:
        if file_type=='Pickle':
            with open("{}/vmat.pkl".format(save_path), "wb") as f:
                pickle.dump(vmat, f)
        elif file_type=='CSV':
            with open("{}/vmat.csv".format(save_path), "w") as f:
                writer = csv.writer(f)
                for item in vmat:
                    writer.writerow(item)

# ====================
# Window Setting

sg.theme('Default')

layout = [
        [sg.Text('WiPiCap', font=('Arial, 30'))],
        [sg.Text('File:', font=('Arial, 20')), sg.Input(font=('Arial, 20'), key="file_name"), sg.FileBrowse(font=('Arial, 20'))],
        [sg.Text('Address:', font=('Arial, 20')), sg.Input(font=('Arial, 20'), key="address")],
        [sg.Text('Output Type', font=('Arial, 18')), sg.Combo(['CSV', 'Pickle'], key="file_type", font=('Arial, 18'))],
        [sg.Checkbox('Raw Time', font=('Arial, 18'), key="raw_time"), sg.Checkbox('V Matrix', font=('Arial, 18'), key="v_matrix")],
        [sg.Button('Convert', font=('Arial, 18'))]
    ]

window = sg.Window('Window Title', layout)

while True:
    event, values = window.read()
    print(values)
    if event == sg.WIN_CLOSED or event == 'Cancel':
        break
    if event=="Convert":
        if values["file_name"]=="":
            sg.popup("Select file.", title="", font=('Arial, 18'))
        else:
            file_name = values["file_name"]
            address = values["address"]
            file_type = values["file_type"]
            raw_time = values["raw_time"]
            v_matrix = values["v_matrix"]

            conversion(file_name, address, file_type, raw_time, v_matrix)

window.close()