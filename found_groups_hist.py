# Author: Karl Zylinski, Uppsala University

# Plots separation agsinst velocity difference

import sys
import os
import matplotlib.pyplot as plt
import vec3
import conv
import numpy
import utils_dict

def verify_arguments():
    if len(sys.argv) < 3:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_hist.py file col bins log"
input_filename = sys.argv[1]
col = sys.argv[2]
log_x = len(sys.argv) == 5 and sys.argv[4] == "log"
bins = None

if len(sys.argv) == 4:
    bins = int(sys.argv[3])

cg = utils_dict.read(input_filename)

cols = cg["columns"]
i_col = cols.index(col)

data_col = []

for g in cg["groups"]:
    for s in g["stars"]:
        if s[i_col] == None:
            continue

        data_col.append(s[i_col])

plt.hist(data_col, bins)
plt.xlabel(col)
plt.ylabel("Count")

if log_x:
    plt.xscale("log")

plt.show()
