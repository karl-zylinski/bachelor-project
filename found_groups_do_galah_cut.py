# Author: Karl Zylinski

# Cuts out the part of a comoving-groups-file that overlaps with GALAH spatially.
# I.e. keeps only |b| > 10 and dec < 10

import os
import sys
import comoving_groups

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

cg = comoving_groups.read(input_filename)
cols = cg["columns"]

i_source_id = cols.index("source_id")
i_b = cols.index("b")
i_dec = cols.index("dec")

out_sids = []
total = 0
kept = 0

for g in cg["groups"]:
    for s in g["stars"]:
        total = total + 1
        sid = s[i_source_id]
        b = s[i_b]
        dec = s[i_dec]
        assert b != None and dec != None

        if abs(b) > 9 and dec < 11: # do 1 deg more just to be safe
            kept = kept + 1
            out_sids.append(str(sid))

out_fh = open(output_filename, "w")
out_fh.write("\n".join(out_sids))
out_fh.close()

print("Kept %d out of %d" % (kept, total))