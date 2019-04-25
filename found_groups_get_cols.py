# Author: Karl Zylinski, Uppsala University

# Goes through the ouput from the find_comoving_stars* scripts and prints
# a list of clusters inside, how many there are of each cluster size etc.

import sys
import os
import utils_str
import utils_dict

def verify_arguments():
    if len(sys.argv) < 4:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    if not utils_str.to_int(sys.argv[2]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_get_cols.py file group_id col1 col2 ..."
input_filename = sys.argv[1]
cg = utils_dict.read(input_filename)
cols_to_get = sys.argv[3:]
cols = cg["columns"]

group_id = int(sys.argv[2])

groups = cg["groups"]

for g in groups:
    p = False
    if g["id"] == group_id:
        for s in g["stars"]:
            cols_to_print = []

            for ctg in cols_to_get:
                cols_to_print.append(str(s[cols.index(ctg)]))
            
            print("\t".join(cols_to_print))
        break

