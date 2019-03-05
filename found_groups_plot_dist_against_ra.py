# Author: Karl Zylinski, Uppsala University

# Plots distance*cos(dec) against ra in polar

import sys
import os
import matplotlib.pyplot as plt
import gaia_columns
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
input_fh = open(input_filename, 'rb')
found_pairs = eval(input_fh.read())
input_fh.close()
assert type(found_pairs) is list, "Supplied file has broken format"

i_source_id = gaia_columns.index("source_id")
i_ra = gaia_columns.index("ra")
i_dec = gaia_columns.index("dec")
i_pmra = gaia_columns.index("pmra")
i_pmdec = gaia_columns.index("pmdec")
i_radial_velocity = gaia_columns.index("radial_velocity")
i_distance = gaia_columns.index("distance")
i_phot_g_mean_mag = gaia_columns.index("phot_g_mean_mag")

ras = []
dists = []
colors = []

for fp in found_pairs:
    if fp["size"] < 4:
        continue

    color = [random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1)]

    for s in fp["stars"]:
        ra = s[i_ra]
        dec = s[i_dec]
        distance_proj = s[i_distance]*math.cos(dec*conv.deg_to_rad)

        if distance_proj > 250:
            continue

        ras.append(ra*conv.deg_to_rad)
        dists.append(distance_proj)
        colors.append(color)

for i in range(0, len(ras)):
    plt.polar(ras[i], dists[i], ".", markersize=2, c=colors[i])
plt.show()
