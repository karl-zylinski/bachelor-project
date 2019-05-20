# Author: Karl Zylinski, Uppsala University

# Cuts out the part of a comoving-groups-file that overlaps with lamost spatially.
# I.e. keeps only |b| > 10 and dec < 10

import os
import sys
import utils_dict

def verify_arguments():
    if len(sys.argv) < 3:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    if not os.path.isfile(sys.argv[2]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_combine_with_lamost_dr3.py input_cms input_lamost_csv"
input_cms = sys.argv[1]
input_lamost_csv = sys.argv[2]

cg = utils_dict.read(input_cms)
cols = cg["columns"]

i_source_id = cols.index("source_id")

ext_sids = set()
csv_fh = open(input_lamost_csv, "r")
csv_lines = csv_fh.readlines()
csv_fh.close()
ext_cols = csv_lines[0].split(",")
i_source_id_ext = ext_cols.index("source_id")

for i in range(1, len(csv_lines)): # skip header line
    csv_line = csv_lines[i]

    if csv_line[0] == "#":
        continue

    source_values = csv_line.split(",")

    if len(source_values) != len(ext_cols):
        continue

    sid = int(source_values[i_source_id_ext])
    ext_sids.add(sid)

for g in cg["groups"]:
    for s in g["stars"]:
        sid = s[i_source_id]

        if sid in ext_sids:
            print(sid)

