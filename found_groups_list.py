# Author: Karl Zylinski, Uppsala University

# Goes through the ouput from the find_comoving_stars* scripts and prints
# a list of clusters inside, how many there are of each cluster size etc.

import sys
import os
import utils_str
import comoving_groups

def verify_arguments():
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    if len(sys.argv) == 3 and utils_str.to_int(sys.argv[2]) == None:
        return False

    return True

assert verify_arguments(), "Usage: found_groups_list.py file [size]"
input_filename = sys.argv[1]
cg = comoving_groups.read(input_filename)
cols = cg["columns"]
i_source_id = cols.index("source_id")
i_ra = cols.index("ra")
i_dec = cols.index("dec")
i_distance = cols.index("distance")
i_pmra = cols.index("pmra")
i_pmdec = cols.index("pmdec")
i_radial_velocity = cols.index("radial_velocity")
i_mag = cols.index("phot_g_mean_mag")

found_groups = cg["groups"]

if len(sys.argv) == 3:
    input_size = int(sys.argv[2])
    print("Info about groups with size %d:" % input_size)
    print()
    for fp in found_groups:
        if int(fp["size"]) == input_size:
            print("Group id: %d" % fp["id"])

            for s in fp["stars"]:
                print("sid: %d | pos: (%f, %f, %f) | vel: (%f, %f, %f) | mag: %f" % (s[i_source_id], s[i_ra], s[i_dec], s[i_distance], s[i_pmra], s[i_pmdec], s[i_radial_velocity], s[i_mag]))

            print("-----")
else:
    num_pairs_of_size = {}
    total = 0

    for fp in found_groups:
        total = total + fp["size"]
        cur_num = num_pairs_of_size.get(fp["size"])
        if cur_num == None:
            num_pairs_of_size[fp["size"]] = 1
        else:
            num_pairs_of_size[fp["size"]] = cur_num + 1

    print()
    print("Found:")
    print("------")
    for size, num in num_pairs_of_size.items():
        print("%d of size %d" % (num, size))

    print()
    print("Total: %d stars" % total)
