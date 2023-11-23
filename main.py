import cProfile
import pstats
from time import perf_counter

from wipicap import get_v_matrix

vs = get_v_matrix("./20210927_01.pcap", "e0:b5:5f:ee:84:45", bw=80, verbose=True)
print(vs.shape)
