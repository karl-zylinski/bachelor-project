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
    if len(sys.argv) != 2:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_plot_sep_vel_diff.py file"
input_filename = sys.argv[1]
cg = comoving_groups.read(input_filename)

cols = cg["columns"]
i_source_id = cols.index("source_id")
i_ra = cols.index("ra")
i_dec = cols.index("dec")
i_pmra = cols.index("pmra")
i_pmdec = cols.index("pmdec")
i_radial_velocity = cols.index("radial_velocity")
i_distance = cols.index("distance")
i_phot_g_mean_mag = cols.index("phot_g_mean_mag")

seps = []
vel_diffs = []

for g in cg["groups"]:
    if g["size"] != 2:
        continue

    ra1 = g["stars"][0][i_ra]
    dec1 = g["stars"][0][i_dec]
    distance1 = g["stars"][0][i_distance]
    pmra1 = g["stars"][0][i_pmra]
    pmdec1 = g["stars"][0][i_pmdec]
    rv1 = g["stars"][0][i_radial_velocity]
    ra2 = g["stars"][1][i_ra]
    dec2 = g["stars"][1][i_dec]
    distance2 = g["stars"][1][i_distance]
    pmra2 = g["stars"][1][i_pmra]
    pmdec2 = g["stars"][1][i_pmdec]
    rv2 = g["stars"][1][i_radial_velocity]


    pos1 = vec3.from_celestial(ra1*conv.deg_to_rad, dec1*conv.deg_to_rad, distance1)
    pos2 = vec3.from_celestial(ra2*conv.deg_to_rad, dec2*conv.deg_to_rad, distance2)
    sep = vec3.len(vec3.sub(pos2, pos1))
    v1 = vec3.from_celestial(pmra1*conv.mas_per_yr_to_rad_per_s, pmdec1*conv.mas_per_yr_to_rad_per_s, rv1)
    v2 = vec3.from_celestial(pmra2*conv.mas_per_yr_to_rad_per_s, pmdec2*conv.mas_per_yr_to_rad_per_s, rv2)
    vel_diff = vec3.len(vec3.sub(v2, v1))

    seps.append(sep)
    vel_diffs.append(vel_diff)

plt.plot(seps, vel_diffs, ".", markersize=2)
plt.xlabel("Sepration (pc)")
plt.ylabel("Velocity difference (km/s)")
plt.xscale("log")
plt.show()
