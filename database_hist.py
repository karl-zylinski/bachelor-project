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

assert verify_arguments(), "Usage: database_hist.py database.db col bins"
db = sys.argv[1]
conn = sqlite3.connect(db)
col = sys.argv[2]
bins = None

if len(sys.argv) == 4:
    bins = int(sys.argv[3])

all_cols = conn.execute('SELECT %s FROM gaia' % col)
data_col = []

for s in all_cols:
    data_col.append(s[0])

plt.hist(data_col, 200)
plt.xlabel(col)
plt.ylabel("Count")
plt.show()
conn.close()