# Author: Karl Zylinski, Uppsala University

# Goes through the ouput of the find_comoving_stars* scripts and prints
# the avg position for each group of at least min_size (you can specify id)

import sys
import os
import matplotlib.pyplot as plt
import utils_str
import utils_dict

min_size = 1

def verify_arguments():
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    if len(sys.argv) == 3 and utils_str.to_int(sys.argv[2]) == None:
        return False

    return True

assert verify_arguments(), "Usage: found_groups_find_avg_pos.py file [id]"

input_filename = sys.argv[1]
cg = utils_dict.read(input_filename)
found_groups = cg["groups"]

cols = cg["columns"]
i_ra = cols.index("ra")
i_dec = cols.index("dec")
i_pmra = cols.index("pmra")
i_pmdec = cols.index("pmdec")
i_distance = cols.index("distance")

found_groups.sort(key = lambda x: x["size"])
clusters = []

id_to_look_for = None

if len(sys.argv) == 3: 
    id_to_look_for = utils_str.to_int(sys.argv[2])

for fp in found_groups:
    gid = fp["id"]
    if id_to_look_for != None and gid != id_to_look_for:
        continue

    size = fp["size"]
    if size < min_size:
        continue

    avg_ra = 0
    avg_dec = 0
    avg_dist = 0

    for s in fp["stars"]:
        ra = s[i_ra]
        dec = s[i_dec]
        dist = s[i_distance]
        avg_ra = avg_ra + ra
        avg_dec = avg_dec + dec
        avg_dist = avg_dist + dist

    avg_ra = avg_ra / size
    avg_dec = avg_dec / size
    avg_dist = avg_dist / size
    clusters.append((gid, size, avg_ra, avg_dec, avg_dist))

clusters.sort(key = lambda x: x[4])

for c in clusters:
    print("id %d \t size %d \t POS(ra, dec, dist): (%f, %f, %f)" % (c[0], c[1], c[2], c[3], c[4]))
