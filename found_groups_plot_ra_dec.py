# Author: Karl Zylinski, Uppsala University

# Plots the stars found in a group in a [ra, dec] diagram with G mag as color

import sys
import os
import matplotlib.pyplot as plt
import utils_str
import utils_dict
from statistics import mean

def verify_arguments():
    if len(sys.argv) != 3:
        return False

    if utils_str.to_int(sys.argv[2]) == None:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_list.py file id"
input_filename = sys.argv[1]
cg = utils_dict.read(input_filename)

input_id = int(sys.argv[2])

cols = cg["columns"]
i_source_id = cols.index("source_id")
i_ra = cols.index("ra")
i_dec = cols.index("dec")
i_pmra = cols.index("pmra")
i_pmdec = cols.index("pmdec")
i_radial_velocity = cols.index("radial_velocity")
i_distance = cols.index("distance")
i_phot_g_mean_mag = cols.index("phot_g_mean_mag")
found_groups = cg["groups"]

for g in found_groups:
    if int(g["id"]) != input_id:
        continue

    ras = []
    decs = []
    mags = []
    dists = []
    avg_ra = 0
    avg_dec = 0
    brightest = 1000 # mag
    dimmest = -1000 # mag

    stars = g["stars"]
    print_velocity_info = len(stars) < 10
    stars.sort(key = lambda x: x[i_phot_g_mean_mag], reverse = True)

    for s in g["stars"]:
        sid = s[i_source_id]
        ra = s[i_ra]
        dec = s[i_dec]
        pmra = s[i_pmra]
        pmdec = s[i_pmdec]
        rv = s[i_radial_velocity]
        dist = s[i_distance]
        mag = s[i_phot_g_mean_mag]
        avg_ra = avg_ra + ra
        avg_dec = avg_dec + dec
        ras.append(ra)
        decs.append(dec)
        mags.append(mag)
        dists.append(dist)
        if mag > dimmest:
            dimmest = mag
        if mag < brightest:
            brightest = mag

        if print_velocity_info:
            print("Velocity of %d (pmra, pmdec, rv): (%f, %f, %f)" % (sid, pmra, pmdec, rv))

    avg_ra = mean(ras)
    avg_dec = mean(decs)
    avg_dist = mean(dists)
    print("Average pos (ra, dec, dist): (%f, %f, %f)" % (avg_ra, avg_dec, avg_dist))

    sizes = []

    for m in mags:
        mn = (m - brightest)/(dimmest-brightest)
        sizes.append(((1-mn) + 0.25) * 100)

    cm = plt.cm.get_cmap('RdYlBu')
    sc = plt.scatter(ras, decs, c=mags, vmin=dimmest, vmax=brightest, s=sizes, cmap=cm)
    plt.colorbar(sc)
    plt.xlabel("ra")
    plt.ylabel("dec")
    plt.show()
    exit()
