# Author: Karl Zylinski, Uppsala University

import sys
import os
import numpy
import matplotlib.pyplot as plt
import mist
import utils_dict

cg = utils_dict.read("out_no_groups.cms")
cg_cols = cg["columns"]
i_teff = cg_cols.index("teff")
i_g = cg_cols.index("phot_g_mean_mag")
i_dist = cg_cols.index("distance")
i_ext = cg_cols.index("a_g_val")
i_feh = cg_cols.index("feh")


def get_color(feh):
    if feh < -2:
        return "red"
    if feh < -1:
        return "green"

    return "gray"

def get_size(feh):
    if feh < -2:
        return 5
    if feh < -1:
        return 5

    return 2


for g in cg["groups"]:
    for s in g["stars"]:
        if s[i_teff] == None or s[i_g] == None or s[i_dist] == None or s[i_feh] == None:
            continue

        mag = s[i_g]
        dist = s[i_dist]
        ext = s[i_ext]
        feh = s[i_feh]

        if ext == None:
            ext = 0

        teff = numpy.log10(s[i_teff])
        G = mag - 5*numpy.log10(dist) + 5 - ext
        plt.plot(teff, G, '.', markersize=get_size(feh), color=get_color(feh), zorder = 10-feh)

plt.xlabel('log T_eff')
plt.ylabel('Gaia G magnitude')

iso_path = "isochrones/feh-2.0.iso"
isos_by_age = mist.load_isochrones(iso_path)
log10_age = numpy.log10(10**10) # 10 Gyr

iso_lteff = []
iso_G = []

isochrone_to_use = None

for iso in isos_by_age:
    if iso["age"] >= log10_age:
        isochrone_to_use = iso
        break

i_iso_lteff = isochrone_to_use["columns"].index("log_Teff")
i_iso_G = isochrone_to_use["columns"].index("Gaia_G_DR2Rev")

for d in isochrone_to_use["data"]:
    iso_lteff.append(d[i_iso_lteff])
    iso_G.append(d[i_iso_G])

plt.plot(iso_lteff, iso_G)
plt.axis([3.915, 3.487, 8.929, -2.826])
plt.savefig("plots/after_galah_with_iso.eps",bbox_inches='tight',pad_inches=0.0)