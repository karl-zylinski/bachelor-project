# Author: Karl Zylinski, Uppsala University

# Plots the stars found in a group in a [ra, dec] diagram with G mag as color

import sys
import os
import matplotlib.pyplot as plt
import utils_str
import utils_dict
import conv
import sqlite3
from statistics import mean

def verify_arguments():
    if len(sys.argv) != 2:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_plot_error_comparison.py database"
db = sys.argv[1]
conn = sqlite3.connect(db)
all_stars = conn.execute('SELECT pmra_error, radial_velocity_error, distance FROM gaia')
pmra_errors = []
rv_errors = []

for s in all_stars:
    d = s[2]

    if d < 0:
        continue

    pmra_error = (s[0]/1000)*d*conv.as_pc_per_year_to_km_per_s
    rv_error = s[1]

    pmra_errors.append(pmra_error)
    rv_errors.append(rv_error)

plt.plot(pmra_errors, rv_errors, '.')
plt.xlabel("pmra_error * d (km/s)")
plt.ylabel("rv_error (km/s)")
plt.show()
exit()
