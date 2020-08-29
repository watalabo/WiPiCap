import pickle
from datetime import datetime, timedelta
import numpy as np
from scipy.interpolate import interp1d
from time import perf_counter

with open("csi_orig.pkl", "rb") as f:
    reader = pickle.load(f)

k = sorted(reader.keys())
# print(k)

start_time = k[0]
end_time = k[-1]

print(start_time, end_time)

value = []
timestamp = start_time

cnt = 0
al = 0
while timestamp!=end_time:
    if timestamp in reader:
        value.append(reader[timestamp])
        cnt += 1
    else:
        value.append(value[-1])
    timestamp = timestamp + timedelta(milliseconds=100)
    al += 1

print(cnt/al)
# print(np.array(value).shape)
with open("csi_int.pkl", "wb") as f:
    pickle.dump(value, f)
