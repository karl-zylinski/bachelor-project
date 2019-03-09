# Author: Karl Zylinski, Uppsala University

# Reads an output-file from the find_comoving_group.py script, puts it into a dictionary

import os

def read(filename):
    out = {}

    in_fh = open(filename, "r")
    lines = in_fh.readlines()

    for l in lines:
        sep = l.index(":")
        k = l[0:sep]
        v = l[sep+1:]
        out[k] = eval(v)

    return out