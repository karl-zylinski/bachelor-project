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
i_x = cols.index("x")
i_y = cols.index("y")
i_z = cols.index("z")
i_vx = cols.index("vx")
i_vy = cols.index("vy")
i_vz = cols.index("vz")
i_phot_g_mean_mag = cols.index("phot_g_mean_mag")

seps = []
vel_diffs = []

for g in cg["groups"]:
    if g["size"] != 2:
        continue

    x1 = g["stars"][0][i_x]
    y1 = g["stars"][0][i_y]
    z1 = g["stars"][0][i_z]
    vx1 = g["stars"][0][i_vx]
    vy1 = g["stars"][0][i_vy]
    vz1 = g["stars"][0][i_vz]
    x2 = g["stars"][1][i_x]
    y2 = g["stars"][1][i_y]
    z2 = g["stars"][1][i_z]
    vx2 = g["stars"][1][i_vx]
    vy2 = g["stars"][1][i_vy]
    vz2 = g["stars"][1][i_vz]


    pos1 = [x1, y1, z1]
    pos2 = [x2, y2, z2]
    sep = vec3.mag(vec3.sub(pos2, pos1))
    v1 = [vx1, vy1, vz1]
    v2 = [vx2, vy2, vz2]
    vel_diff = vec3.mag(vec3.sub(v2, v1))

    seps.append(sep)
    vel_diffs.append(vel_diff)

plt.plot(seps, vel_diffs, ".", markersize=2)
plt.xlabel("Sepration (pc)")
plt.ylabel("Velocity difference (km/s)")
plt.xscale("log")
plt.show()
