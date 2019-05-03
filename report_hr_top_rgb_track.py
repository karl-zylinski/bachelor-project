# Author: Karl Zylinski, Uppsala University

import sys
import os
import numpy
import matplotlib.pyplot as plt
import mist
import utils_dict


metallicity = -2.0
track = mist.parse_track("evolutionay_tracks/0.8M_feh-0.eep.cmd")

lteff = []
g = []


i_lteff = track["columns"].index("log_Teff")
i_g = track["columns"].index("Gaia_G_DR2Rev")

for d in track["track"]:
    lteff.append(d[i_lteff])
    g.append(d[i_g])

plt.plot(lteff, g, linewidth=0.5)

plt.xlabel('log $T_{eff}$')
plt.ylabel('Gaia G absolute magnitude')
plt.gca().invert_yaxis()
plt.gca().invert_xaxis()
#plt.axis([3.92, 3.46, -3.15, 2.5])
plt.show()
#plt.savefig("plots/iso_example.eps",bbox_inches='tight',pad_inches=0.0)