# Author: Karl Zylinski, Uppsala University

# Takes a bunch of MIST isochrones and plots them at the age specified. Then overlays
# stars from a comoving-groups-file.

import sys
import os
import numpy
import matplotlib.pyplot as plt
import mist
import utils_dict

age = 10000000000
log10_age = numpy.log10(age)
iso_paths = {
    0.372: "isochrones/for_18778/feh+0.37177462.iso",
    -1.09: "isochrones/for_18778/feh-1.0870304.iso",
    -2.55: "isochrones/for_18778/feh-2.54583542.iso" }

isos = {}
for metallicty, path in iso_paths.items():
    isos[metallicty] = mist.load_isochrones(path)

distances = [1864.7306354736843, 1871.298532837807]
exts = [0, 0]
mags = [9.883364, 13.578179]

abs_mags = []
for i in range(0, len(mags)):
    abs_mags.append(mags[i] - 5*numpy.log10(distances[i]) + 5 - exts[i])

gaia_lteff = numpy.log10([3500.0, 4273.3003]) # first is from GALAH, second two from GAIA

for metallicty, isos_by_age in isos.items():
    iso_lteff = []
    iso_G = []

    isochrone_to_use = None

    for iso in isos_by_age:
        if iso["age"] >= log10_age:
            isochrone_to_use = iso
            break

    i_lteff_iso = isochrone_to_use["columns"].index("log_Teff")
    i_G_iso = isochrone_to_use["columns"].index("Gaia_G_DR2Rev")

    for d in isochrone_to_use["data"]:
        iso_lteff.append(d[i_lteff_iso])
        iso_G.append(d[i_G_iso])

    plt.plot(iso_lteff, iso_G)

plt.xlabel('log T_eff')
plt.ylabel('gaia G')
for i in range(0, len(gaia_lteff)):
    plt.plot(gaia_lteff[i], abs_mags[i], '.', markersize=5)
plt.legend(["0.372", "-1.09", "-2.55", "4241639268375965312", "4240046209156253568"])
plt.gca().invert_xaxis()
plt.gca().invert_yaxis()
plt.show()