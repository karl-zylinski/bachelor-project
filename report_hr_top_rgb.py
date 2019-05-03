# Author: Karl Zylinski, Uppsala University

import sys
import os
import numpy
import matplotlib.pyplot as plt
import mist
import utils_dict


age = 10000000000
log10_age = numpy.log10(age)
metallicity = -1.0
isos_by_age = mist.load_isochrones("isochrones/feh-1.0.iso")

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

plt.plot(iso_lteff, iso_lum, linewidth=0.5)

plt.xlabel('log T_eff')
plt.ylabel('log L/L_sun')
plt.axis([3.92, 3.46, -3.15, 2.5])
plt.show()
#plt.savefig("plots/iso_example.eps",bbox_inches='tight',pad_inches=0.0)