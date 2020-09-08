from cmath import sin, cos, exp, phase, pi, sqrt
import numpy as np
from tqdm import tqdm
from scipy import signal, stats, fftpack
import matplotlib.pyplot as plt
import itertools
from numba import jit
from sklearn.mixture import GaussianMixture
import pickle

def recon_v_phase(sub_arr):
    phi11, phi21, psi21, psi31, phi22, psi32 = sub_arr

    # 量子化された値を角度に戻す
    phi11 = (phi11/32+1/64)*pi
    phi21 = (phi21/32+1/64)*pi
    psi21 = (psi21/32+1/64)*pi
    psi31 = (psi31/32+1/64)*pi
    phi22 = (phi22/32+1/64)*pi
    psi32 = (psi32/32+1/64)*pi

    v11 = cos(psi31) * exp(1j*phi11) * cos(psi21)
    v12 = -cos(psi32) * exp(1j*phi22) * exp(1j*phi11) * sin(psi21) - sin(psi32) * sin(psi31) * exp(1j*phi11) * cos(psi21)
    v13 = sin(psi32) * exp(1j*phi22) * exp(1j*phi11) * sin(psi21) - cos(psi32) * sin(psi31) * exp(1j*phi11) * cos(psi21)
    v21 = cos(psi31) * exp(1j*phi21) * sin(psi21)
    v22 = cos(psi32) * exp(1j*phi22) * exp(1j*phi21) * cos(psi21) - sin(psi32) * sin(psi31) * exp(1j*phi21) * sin(psi21)
    v23 = -sin(psi32) * exp(1j*phi22) * exp(1j*phi21) * cos(psi21) - cos(psi32) * sin(psi31) * exp(1j*phi21) * sin(psi21)
    v31 = sin(psi31)
    v32 = cos(psi31) * sin(psi32)
    v33 = cos(psi31) * cos(psi32)

    return [phase(v11/v31), phase(v21/v31), phase(v12/v32), phase(v22/v32)]
    # return [phase(v11/v31)]

def recon_v_amp(sub_arr):
    phi11, phi21, psi21, psi31, phi22, psi32 = sub_arr

    # 量子化された値を角度に戻す
    phi11 = (phi11/32+1/64)*pi
    phi21 = (phi21/32+1/64)*pi
    psi21 = (psi21/32+1/64)*pi
    psi31 = (psi31/32+1/64)*pi
    phi22 = (phi22/32+1/64)*pi
    psi32 = (psi32/32+1/64)*pi

    v11 = cos(psi31) * exp(1j*phi11) * cos(psi21)
    v12 = -cos(psi32) * exp(1j*phi22) * exp(1j*phi11) * sin(psi21) - sin(psi32) * sin(psi31) * exp(1j*phi11) * cos(psi21)
    v13 = sin(psi32) * exp(1j*phi22) * exp(1j*phi11) * sin(psi21) - cos(psi32) * sin(psi31) * exp(1j*phi11) * cos(psi21)
    v21 = cos(psi31) * exp(1j*phi21) * sin(psi21)
    v22 = cos(psi32) * exp(1j*phi22) * exp(1j*phi21) * cos(psi21) - sin(psi32) * sin(psi31) * exp(1j*phi21) * sin(psi21)
    v23 = -sin(psi32) * exp(1j*phi22) * exp(1j*phi21) * cos(psi21) - cos(psi32) * sin(psi31) * exp(1j*phi21) * sin(psi21)
    v31 = sin(psi31)
    v32 = cos(psi31) * sin(psi32)
    v33 = cos(psi31) * cos(psi32)

    return [abs(v11), abs(v12), abs(v21), abs(v22), abs(v31), abs(v32)]

def phase_modify(phases):
    mod_phases = []
    for item in phases:
        mat = round(item, 2)
        if mat<0:
            mat = mat+3.14
        if mat==3.14:
            mat = 0
        mod_phases.append(mat)
    return mod_phases

def calc_phase(row):
    comp_values = list(map(lambda x: int(x), row['values'].replace('[','').replace(']','').split(',')))
    tmp = []
    for i in range(234):
        phases = recon_v_phase(comp_values[i*6:(i+1)*6])
        mod_phases = phase_modify(phases)
        tmp.extend(mod_phases)
    return tmp

def calc_amp(row):
    comp_values = list(map(lambda x: int(x), row['values'].replace('[','').replace(']','').split(',')))
    tmp = []
    for i in range(52):
        amps = recon_v_amp(comp_values[i*6:(i+1)*6])
        tmp.extend(amps)
    return tmp

def detrend(arr):
    tmp = np.array([])
    for i in range(10):
        med = np.median(arr[i*100:(i+1)*100])
        tmp = np.append(tmp, arr[i*100:(i+1)*100]-med)
    return tmp

@jit
def median_filter(arr, size=5):
    tmp = np.array([])
    for i in range(len(arr)):
        med = np.median(arr[i:i+size])
        tmp = np.append(tmp, med)
    return tmp

def estimate(arr, back):

    result = []
    rows = arr.shape[0]
    for i in tqdm(range(rows)):
        feature = arr[i]
        freq, F = plot_freq(feature, back[i])

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

def calc_density(arr, dif_index, thr=1.1):
    tmp = np.array([])
    cnt = list(map(lambda x: abs(arr[x[0]]-arr[x[1]]), dif_index))
    sigma = np.median(cnt)/0.68/sqrt(2)
    pr = 0+0j
    for i in range(len(arr)):
        diff = cnt[i*(len(arr)-1):(i+1)*(len(arr)-1)]
        diff = list(map(lambda x: exp(x**2/2/sigma**2), diff))
        pr = pr + sum(diff)
        pr = pr/len(arr)/sqrt(2*pi)/sigma
        if float(pr)<thr:
            tmp = np.append(tmp, float(pr))
        else: tmp = np.append(tmp, 0)
    return tmp

@jit
def gmm_estimate(mat):
    shape = mat.shape
    mat = mat.reshape(-1,1)
    gmm = GaussianMixture(n_components=3,covariance_type='spherical').fit(mat)
    # print(gmm.weights_)
    indexes = np.where(gmm.weights_>0.3)[-1]
    for i in tqdm(range(len(mat))):
        for j in indexes:
            if abs(mat[i]-gmm.means_[j][-1]) < 2.5*gmm.covariances_[j]:
                mat[i] = 0
                break
    return mat.reshape(shape)

def plot_freq(arr, back):
    feature = arr
    feature = np.pad(feature, [0,1000-len(feature)], "constant")
    F = fftpack.rfft(stats.zscore(feature))
    freq = list(fftpack.rfftfreq(n=len(feature), d=0.1))
    F = abs(F)
    print(F[-1], back[-1])
    F = F-back
    F = list((F-min(F))/(max(F)-min(F)))

    return freq, F

def calc_freq(arr):
    feature = arr
    feature = np.pad(feature, [0,1000-len(feature)], "constant")
    F = fftpack.rfft(stats.zscore(feature))
    F = abs(F)
    return F
