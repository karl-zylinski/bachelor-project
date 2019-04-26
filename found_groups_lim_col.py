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
    if len(sys.argv) != 4:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_lim_col.py file col lim"
input_filename = sys.argv[1]
col = sys.argv[2]
lim = float(sys.argv[3])

cg = utils_dict.read(input_filename)

cols = cg["columns"]
i_col = cols.index(col)

data_col = []

for g in cg["groups"]:
    for s in g["stars"]:
        if s[i_col] == None or s[i_col] > lim:
            continue

        print(s[cols.index("source_id")])
        print(s[cols.index("feh")])
        print(s[i_col])
        print()
        break

