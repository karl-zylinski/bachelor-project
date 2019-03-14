# Author: Karl Zylinski, Uppsala University

# Cuts out the part of a comoving-groups-file that overlaps with GALAH spatially.
# I.e. keeps only |b| > 10 and dec < 10

import os
import sys
import utils_dict

def verify_arguments():
    if len(sys.argv) < 3:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    if os.path.isfile(sys.argv[2]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_do_galah_cut.py input_file output_file"
input_filename = sys.argv[1]
output_filename = sys.argv[2]

cg = utils_dict.read(input_filename)
cols = cg["columns"]

i_source_id = cols.index("source_id")
i_b = cols.index("b")
i_dec = cols.index("dec")
i_g = cols.index("phot_g_mean_mag")

out_sids = []
total = 0
kept = 0

groups_within_cut = []

for g in cg["groups"]:
    size = g["size"]
    total = total + size
    avg_b = 0
    avg_dec = 0

    for s in g["stars"]:
        avg_b = avg_b + s[i_b]
        avg_dec = avg_dec + s[i_dec]

    avg_b = avg_b / size
    avg_dec = avg_dec / size

    if abs(avg_b) > 9 and avg_dec < 11: # do 1 deg more just to be safe
        groups_within_cut.append(g)
        kept = kept + size

out_cg = cg.copy()
out_cg["groups"] = groups_within_cut
utils_dict.write(out_cg, output_filename)

print("Kept %d out of %d" % (kept, total))