# Author: Karl Zylinski, Uppsala University

# Plots some isochrones, images used in report

import sys
import os
import numpy
import matplotlib.pyplot as plt
import mist
import utils_dict

isos = {}

for i in range(0, 5):
    iso_path = "isochrones/feh-%.1f.iso" % i
    isos[-i] = mist.load_isochrones(iso_path)

age = 10000000000
log10_age = numpy.log10(age)

for metallicty, isos_by_age in isos.items():
    iso_lteff = []
    iso_lum = []

    isochrone_to_use = None

    for iso in isos_by_age:
        if iso["age"] >= log10_age:
            isochrone_to_use = iso
            break

    i_lteff = isochrone_to_use["columns"].index("log_Teff")
    i_lum = isochrone_to_use["columns"].index("log_L")

    for d in isochrone_to_use["data"]:
        iso_lteff.append(d[i_lteff])
        iso_lum.append(d[i_lum])

    plt.plot(iso_lteff, iso_lum)

plt.xlabel('log T_eff')
plt.ylabel('log L/L_sun')
plt.axis([3.92, 3.46, -3.15, 1.58])
plt.legend(["Fe/H 0", "Fe/H -1", "Fe/H -1", "Fe/H -2", "Fe/H -3", "Fe/H -4"])
#plt.show()
plt.savefig("plots/iso_example.eps",bbox_inches='tight',pad_inches=0.0)