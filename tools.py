from cmath import sin, cos, exp, phase, pi, sqrt
import numpy as np
from scipy import signal, stats, fftpack
import itertools
import matplotlib.pyplot as plt
from sklearn.preprocessing import minmax_scale
import pickle
from statistics import variance, mean
from numba import jit
from scipy.stats import zscore

def recon_v_matrix(sub_arr):
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

    return [v11, v12, v13, v21, v22, v23, v31, v32, v33]

def recon_v_phase(sub_arr):
    v11, v12, v13, v21, v22, v23, v31, v32, v33 = recon_v_matrix(sub_arr)

    return [phase(v11),phase(v12),phase(v21),phase(v22),phase(v31),phase(v32)]

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
    comp_values = list(map(lambda x: int(x), row))
    tmp = []
    for i in range(234):
        phases = recon_v_phase(comp_values[i*6:(i+1)*6])
        tmp.extend(phases)
    return tmp

def estimate(arr, fs):
    result = []
    rows = arr.shape[0]
    for i in range(rows):
        feature = arr[i]
        freq, F = plot_freq(feature, fs)

        peak_value = sorted(F)[-1]
        peak = freq[F.index(peak_value)]

        result.append(peak*30)
    return result

def plot_freq(arr, fs):
    feature = zscore(arr)
    F = fftpack.rfft(feature)
    freq = list(fftpack.rfftfreq(n=len(feature), d=1/fs))
    F = list(abs(F))

    return freq, F

def hampel(x, k, thr=3):
    arraySize = len(x)
    idx = np.arange(arraySize)
    output_x = x.copy()
    output_Idx = np.zeros_like(x)
 
    for i in range(arraySize):
        mask1 = np.where( idx >= (idx[i] - k) ,True, False)
        mask2 = np.where( idx <= (idx[i] + k) ,True, False)
        kernel = np.logical_and(mask1, mask2)
        median = np.median(x[kernel])
        std = 1.4826 * np.median(np.abs(x[kernel] - median))
        if np.abs(x[i] - median) > thr * std:
            output_x[i] = median

    return output_x

def dynamic_detrend(x):
    detrended = []
    tmp = []
    array_size = len(x)
    default_window = array_size//5
    e_v = sum([variance(x[i*5:(i+1)*5]) for i in range(default_window)]) / default_window
    for i in range(array_size):
        tmp.append(x[i])
        if len(tmp)==1: continue
        if variance(tmp)>1.2*e_v or len(tmp)>10:
            tmp_mean = mean(tmp[:-1])
            det_part = [item-tmp_mean for item in tmp[:-1]]
            detrended.extend(det_part)
            tmp = [tmp[-1]]
        if i==array_size-1: detrended.extend(tmp)
    return detrended

def butter_highpass(data, cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype='high', analog=False)
    y = signal.filtfilt(b, a, data)
    return y

def butter_lowpass(data, cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    y = signal.filtfilt(b, a, data)
    return y

def ema(x, period):
    ema = np.zeros(len(x))
    ema[period-1] = x[:period].mean() # 最初だけ単純移動平均で算出
    
    for day in range(period, len(x)):
        ema[day] = ema[day-1] + (x[day] - ema[day-1]) / (period + 1) * 2
    
    return ema

def phase_calib(x):
    cp = np.empty(len(x))
    # xはサブキャリア分のarray
    tp = np.empty(len(x))
    k = np.arange(-28, 29)
    diff = 0
    eta = pi
    tp[0] = x[0]

    for i in range(1, 234):
        if x[i]-x[i-1]>eta:
            diff = diff + 1
        tp[i] = x[i]-diff*2*pi
    a = (tp[233]-tp[0])/(k[233]-k[0])
    b = sum(tp)/233

    for i in range(234):
        cp[i] = tp[i] - a*k[i] - b
    return cp

def stack(mat, step):
    phases = []
    for i in range(6):
        tmp = mat[:,i::6]
        fixed = np.empty((0,234))
        for item in tmp:
            # calib_phase = phase_calib(item)
            fixed = np.append(fixed, [item], axis=0)
        phases.append(fixed.T)
    feature = np.append(feature, phases[0]-phases[1], axis=0)
    feature = np.append(feature, phases[2]-phases[3], axis=0)

    feature = np.pad(feature, [(0,0), (0,step-len(feature[0]))], 'constant')
    return feature
    
def str2arr(x):
    x_alt = x.replace('"','').replace('[','').replace(']','').split(',')
    return list(map(int, x_alt))

def recon_phase_two(sub_arr):
    phi11, psi21 = sub_arr
    a = np.array([[exp(1j*phi11), 0],[0, 1]])
    b = np.array([[cos(psi21), -sin(psi21)],[sin(psi21), cos(psi21)]])

    v = np.dot(a,b)

    return [phase(v[0][0]), phase(v[0][1]), phase(v[1][0]), phase(v[1][1])]
    # return [abs(v[0][0]), abs(v[0][1]), abs(v[1][0]), abs(v[1][1])]
    # return [(v[0][0]), (v[0][1]), (v[1][0]), (v[1][1])]

def calc_phase_two(row):
    comp_values = list(map(lambda x: int(x), row))
    tmp = []
    for i in range(234):
        phases = recon_phase_two(comp_values[i*2:(i+1)*2])
        tmp.extend(phases)
    return tmp

def stack_two(mat, step):
    phases = []
    for i in range(4):
        tmp = mat[:,i::4]
        fixed = np.empty((0,234))
        for item in tmp:
            fixed = np.append(fixed, [item], axis=0)
        phases.append(tmp.T)
    feature = abs(phases[0] - phases[1])

    feature = np.pad(feature, [(0,0), (0,step-len(feature[0]))], 'constant')
    return feature