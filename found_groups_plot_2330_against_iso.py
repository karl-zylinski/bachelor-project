# Author: Karl Zylinski, Uppsala University

# Takes a bunch of MIST isochrones and plots them at the age specified. Then overlays
# stars from a comoving-groups-file.

import sys
import os
import numpy
import matplotlib.pyplot as plt
import mist
import utils_dict

ages = numpy.arange(5*10**9, 14*10**9+1, 5*10**8)
log10_ages = numpy.log10(ages)
iso_paths = {
    0.0313: "isochrones/for_2330/feh+0.0313.iso",
    -1.578: "isochrones/for_2330/feh-1.578.iso",
    -3.19: "isochrones/for_2330/feh-3.19.iso" }

all_isos = {}
for metallicty, path in iso_paths.items():
    all_isos[metallicty] = mist.load_isochrones(path)


def find_iso_with_age(isos, age_log10):
    for iso in isos:
        if iso["age"] < age_log10:
            continue

        return iso

    return isos[-1]

isos_by_age = []
for l10age in log10_ages:
    isos_per_metallicity = {}
    for metallicity, isos in all_isos.items():
        isos_per_metallicity[str(metallicity)] = find_iso_with_age(isos, l10age)
        
    iso_by_age = {
        "age": l10age,
        "isos_per_metallicity": isos_per_metallicity
    }
    isos_by_age.append(iso_by_age)

distances = [97.80464222185262, 107.93788932831916]
exts = [0.503, 0.0253]
mags = [11.25518, 10.083699]

abs_mags = []
for i in range(0, len(mags)):
    abs_mags.append(mags[i] - 5*numpy.log10(distances[i]) + 5 - exts[i])

gaia_lteff = numpy.log10([4985.3335, 5648.0])

file_index = 0
for iba in isos_by_age:
    age = iba["age"]
    isos_per_metallicity = iba["isos_per_metallicity"]

    plt.clf()
    legend = []
    for metallicity, iso in isos_per_metallicity.items():
        iso_lteff = []
        iso_gaia_G = []
        iso_index_log_Teff = iso["columns"].index("log_Teff")
        iso_index_gaia_G = iso["columns"].index("Gaia_G_DR2Rev")

        for d in iso["data"]:
            iso_lteff.append(d[iso_index_log_Teff])
            iso_gaia_G.append(d[iso_index_gaia_G])

        plt.plot(iso_lteff, iso_gaia_G)
        plt.xlabel('log T_eff')
        plt.ylabel('gaia G')
        legend.append(str(metallicity))

    for i in range(0, len(gaia_lteff)):
        plt.plot(gaia_lteff[i], abs_mags[i], '.', markersize=5)

    legend.extend(["5281825062636445696", "5213358473574080896"])
    plt.title("Age: 10^%f (%s) years" % (age, str(int(10**age))))
    plt.legend(legend)
    plt.gca().invert_xaxis()
    plt.gca().invert_yaxis()
    plt.savefig("%d_%s.png" % (file_index,str(age)))
    file_index = file_index + 1
