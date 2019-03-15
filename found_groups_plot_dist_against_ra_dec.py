# Author: Karl Zylinski, Uppsala University

# Plots distance*cos(dec) against ra in polar

import sys
import os
import matplotlib.pyplot as plt
import utils_dict
import vec3
import conv
import numpy
import random
import math

def verify_arguments():
    if len(sys.argv) != 2:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_plot_dist_against_ra_dec.py file"
input_filename = sys.argv[1]
cg = utils_dict.read(input_filename)

cols = cg["columns"]
i_source_id = cols.index("source_id")
i_ra = cols.index("ra")
i_dec = cols.index("dec")
i_distance = cols.index("distance")

ras = []
decs = []
dists = []
colors = []
found_groups = cg["groups"]

for g in found_groups:
    if g["size"] < 4:
        continue

    color = [random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1)]

    for s in g["stars"]:
        ra = s[i_ra]
        dec = s[i_dec]
        distance = s[i_distance]

        decs.append(dec*conv.deg_to_rad)
        ras.append(ra*conv.deg_to_rad)
        dists.append(distance)
        colors.append(color)

for i in range(0, len(ras)):
    plt.polar(ras[i], dists[i], ".", markersize=1, c=colors[i])
    plt.title("ra versus distance")
plt.figure()
for i in range(0, len(ras)):
    plt.polar(decs[i], dists[i], ".", markersize=1, c=colors[i])
    plt.title("dec versus distance")
plt.show()
