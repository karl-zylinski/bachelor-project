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
all_stars = conn.execute('SELECT distance, distance_error FROM gaia')
dists = []
dist_errors = []
num_dist_with_dist_over_error_under_10 = 0

for s in all_stars:
    dist = s[0]
    dist_error = s[1]
    if dist > 3000 or dist < 0:
        continue

    if dist_error/dist < 0.1:
        num_dist_with_dist_over_error_under_10 = num_dist_with_dist_over_error_under_10 + 1
    else:
        continue

    dists.append(dist)
    dist_errors.append(dist_error)

print(num_dist_with_dist_over_error_under_10)
plt.plot(dists, dist_errors, '.', markersize=1)
plt.xlabel("distance (pc)")
plt.ylabel("distance_error (pc)")
plt.show()
exit()
conn.close()
