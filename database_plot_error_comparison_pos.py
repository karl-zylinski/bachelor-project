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

assert verify_arguments(), "Usage: found_groups_plot_error_comparison_pos.py database"
db = sys.argv[1]
conn = sqlite3.connect(db)
all_stars = conn.execute('SELECT ra_error, distance_error, distance FROM gaia')
ra_d_errors = []
distance_errors = []

for s in all_stars:
    d = s[2]
    if d < 0:
        continue
        
    ra_d_error = s[0]*conv.deg_to_rad*d
    dist_error = s[1]

    ra_d_errors.append(ra_d_error)
    distance_errors.append(dist_error)

plt.plot(ra_d_errors, distance_errors, '.')
plt.xlabel("ra_error * d (pc)")
plt.ylabel("distance_error (pc)")
plt.show()
exit()
conn.close()