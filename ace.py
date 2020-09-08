import dask.dataframe as dd
from scipy.signal import medfilt
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from tools import *
import pickle

df = dd.read_csv('comp_feedback.csv', header=0, names=('timestamp', 'values'))

ddf = df.apply(calc_amp, axis=1, meta=list).compute()
record = np.array([list(i) for i in ddf.to_numpy()]).T

angles = record.shape[1]
record_fix = np.empty((0,angles), float)

dif_index = list(itertools.permutations(np.arange(angles), 2))
# for item in tqdm(record):
#     tmp = calc_density(item,dif_index,2)
#     record_fix = np.append(record_fix, [tmp], axis=0)
# record_fix = gmm_estimate(record)

with open('back_freq.pkl', 'rb') as f:
    back_freq = pickle.load(f)

estimate(record, back_freq)

# estimate(record.T)