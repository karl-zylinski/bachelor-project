# Author: Karl Zylinski, Uppsala University

import sys
import os
import matplotlib.pyplot as plt
import vec3
import conv
import numpy
import sqlite3
import utils_dict

def verify_arguments():
    if len(sys.argv) < 3:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: database_hist.py database.db col bins log"
db = sys.argv[1]
conn = sqlite3.connect(db)
col = sys.argv[2]
log_x = len(sys.argv) == 5 and sys.argv[4] == "log"
bins = None

if len(sys.argv) >= 4:
    bins = int(sys.argv[3])

all_cols = conn.execute('SELECT %s FROM gaia' % col)
data_col = []

for s in all_cols:
    data_col.append(s[0])

plt.hist(data_col, bins)
plt.xlabel(col)
plt.ylabel("Count")

if log_x:
    plt.xscale("log")

plt.show()
conn.close()