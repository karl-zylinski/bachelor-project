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
    -1.23: "isochrones/for_5921751752101964416/feh-1.23.iso",
    -2.03: "isochrones/for_5921751752101964416/feh-2.03.iso",
    -2.83: "isochrones/for_5921751752101964416/feh-2.83.iso" }

isos = {}
for metallicty, path in iso_paths.items():
    isos[metallicty] = mist.load_isochrones(path)

distances = [2491.7314261117835, 2501.035153173595, 2501.622896865134]
exts = [0,0,0] # only one of these had extinction, assuming same for all
mags = [12.256209, 12.265655, 10.72475]

abs_mags = []
for i in range(0, len(mags)):
    abs_mags.append(mags[i] - 5*numpy.log10(distances[i]) + 5 - exts[i])

gaia_lteff = numpy.log10([4870.7466, 4813.5, 4692.3667]) # first is from GALAH, second two from GAIA

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
plt.plot(gaia_lteff, abs_mags, '.', markersize=5)
plt.legend(["-1.23", "-2.03", "-2.83", "Found stars"])
plt.gca().invert_xaxis()
plt.gca().invert_yaxis()
plt.show()