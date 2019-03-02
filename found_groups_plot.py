# Author: Karl Zylinski, Uppsala University

# Plots the stars found in a group in a [ra, dec] diagram with G mag as color

import sys
import os
import matplotlib.pyplot as plt
import utils_str
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
input_fh = open(input_filename, 'rb')
found_pairs = eval(input_fh.read())
input_fh.close()
assert type(found_pairs) is list, "Supplied file has broken format"

input_id = int(sys.argv[2])


for fp in found_pairs:
    if int(fp["id"]) != input_id:
        continue

    ras = []
    decs = []
    mags = []
    dists = []
    avg_ra = 0
    avg_dec = 0
    brightest = 1000 # mag
    dimmest = -1000 # mag

    stars = fp["stars"]
    print_velocity_info = len(stars) < 10
    stars.sort(key = lambda x: x[8], reverse = True)

    for s in fp["stars"]:
        sid = s[0]
        ra = s[1]
        dec = s[2]
        pmra = s[4]
        pmdec = s[5]
        rv = s[6]
        dist = s[7]
        mag = s[8]
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
