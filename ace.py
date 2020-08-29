import pickle
import numpy as np
from cmath import sin, cos, exp, phase, pi
import matplotlib.pyplot as plt
from tqdm import tqdm
from scipy import signal, stats, fftpack

def calc_v(sub_one):
    matrix = np.full((3,3), 0+0j)
    phi11, phi21, psi21, psi31, phi22, psi32 = sub_one

    # 量子化された値を角度に戻す
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

    # return (phase(matrix[0][0]/matrix[2][0]))
    return [phase(matrix[0][0]),phase(matrix[0][1]),phase(matrix[1][0]),phase(matrix[1][1]),phase(matrix[2][0]),phase(matrix[2][1])]

# ここからメイン
with open("csi_int.pkl", "rb") as f:
    reader = pickle.load(f)
reader = np.array(reader)

record = []
for item in tqdm(reader):
    tmp = []
    for i in range(52):
        elements = calc_v(item[i*6:(i+1)*6])
        # mat = round(calc_v(item[i*6:(i+1)*6]), 2)
        mat = round(elments[0]-elements[4], 2)
        if mat<0:
            mat = mat+3.14
        if mat==3.14:
            mat = 0
        tmp.append(mat)
    record.append(tmp)

record = np.array(record).T
print(record.shape)

result = []
for i in range(52):
    feature = record[i]
    feature = np.pad(feature, [0,1000-len(feature)], "constant")
    F = fftpack.rfft(stats.zscore(feature))
    freq = list(fftpack.rfftfreq(n=len(feature), d=0.1))

    F = abs(F)

    F = list((F-min(F))/(max(F)-min(F)))

    peak_value = sorted(F)[-1]
    peak = freq[F.index(peak_value)]
    i=-1
    while peak<0.15 or peak>2:
        i -= 1
        peak_value = sorted(F)[i]
        peak = freq[F.index(sorted(F)[i])]
    if 0.15<peak<0.3:
        tmp = []
        tmp_value = []
        for i in range(len(F)):
            if 0.95*peak_value<F[i]<peak_value and freq[i]>0.3:
                tmp.append(freq[i])
                tmp_value.append(F[i])
        try:
            peak = tmp[tmp_value.index(max(tmp_value))]
        except:
            pass

    result.append(int(peak*100))

print("median Result -> ", int(np.median(result)))
print("average Result -> ", int(np.average(result)))
print("Mode Result -> ", stats.mode(result)[0])

# plt.rcParams["font.size"] = 25
# plt.rcParams['font.family'] = 'Times New Roman'
# plt.figure(figsize=(15,4))
# plt.xticks(np.arange(0,2200,200))
# plt.xlim([0,3])
# plt.xlabel("Time(ms)")
# plt.ylabel("Subcarrier Index")
# plt.yticks(np.arange(0,52,10))
# plt.grid()
# plt.plot(freq, F)
# plt.pcolor(record, cmap="viridis")
# plt.savefig("freq.pdf", bbox_inches="tight")
