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

assert verify_arguments(), "Usage: found_groups_plot_sep_vel_diff.py file"
input_filename = sys.argv[1]
cg = utils_dict.read(input_filename)

cols = cg["columns"]
i_source_id = cols.index("source_id")
i_ra = cols.index("ra")
i_dec = cols.index("dec")
i_pmra = cols.index("pmra")
i_pmdec = cols.index("pmdec")
i_radial_velocity = cols.index("radial_velocity")
i_distance = cols.index("distance")
i_phot_g_mean_mag = cols.index("phot_g_mean_mag")

ras = []
dists = []
colors = []
found_groups = cg["groups"]

for g in found_groups:
    #if g["size"] < 3:
    #    continue

    color = [random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1)]

    for s in g["stars"]:
        ra = s[i_ra]
        dec = s[i_dec]
        distance = s[i_distance]

        if distance > 500:
            continue

        ras.append(ra*conv.deg_to_rad)
        dists.append(distance)
        colors.append(color)

for i in range(0, len(ras)):
    plt.polar(ras[i], dists[i], ".", markersize=2, c=colors[i])
plt.show()
