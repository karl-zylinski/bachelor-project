# Author: Karl Zylinski, Uppsala University

# Plots separation agsinst velocity difference

import sys
import os
import matplotlib.pyplot as plt
import vec3
import conv
import numpy
import comoving_groups

def verify_arguments():
    if len(sys.argv) < 4:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_plot.py file col1 col2 option"
input_filename = sys.argv[1]
col1 = sys.argv[2]
col2 = sys.argv[3]

option = None
if len(sys.argv) == 5:
    option = sys.argv[4]

cg = comoving_groups.read(input_filename)

cols = cg["columns"]
i_col1 = cols.index(col1)
i_col2 = cols.index(col2)

data_col1 = []
data_col2 = []

for g in cg["groups"]:
    for s in g["stars"]:
        if s[i_col1] == None or s[i_col2] == None:
            continue

        data_col1.append(s[i_col1])
        data_col2.append(s[i_col2])

plt.plot(data_col1, data_col2, ".", markersize=5)
plt.xlabel(col1)
plt.ylabel(col2)

if option == "log":
    plt.xscale("log")
    plt.yscale("log")
plt.show()
