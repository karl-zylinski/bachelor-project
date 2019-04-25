# Author: Karl Zylinski, Uppsala University

# Goes through the ouput from the find_comoving_stars* scripts and prints
# a list of clusters inside, how many there are of each cluster size etc.

import sys
import os
import utils_str
import utils_dict

def verify_arguments():
    if len(sys.argv) != 3:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    if not utils_str.to_int(sys.argv[2]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_get_group_id.py file gaia_source_id"
input_filename = sys.argv[1]
cg = utils_dict.read(input_filename)
i_source_id = cg["columns"].index("source_id")
sid = int(sys.argv[2])

groups = cg["groups"]

for g in groups:
    for s in g["stars"]:
        if s[i_source_id] == sid:
            print(g["id"])
            break
