# Author: Karl Zylinski, Uppsala University

import sys
import os
import utils_str
import utils_dict

def verify_arguments():
    if len(sys.argv) != 5:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    if not utils_str.to_float(sys.argv[2]):
        return False

    if not utils_str.to_float(sys.argv[3]):
        return False

    if not utils_str.to_float(sys.argv[4]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_find_by_avg_pos.py file ra dec radius"
input_filename = sys.argv[1]
cg = utils_dict.read(input_filename)
ra = float(sys.argv[2])
dec = float(sys.argv[3])
radius = float(sys.argv[4])
i_ra = cg["columns"].index("ra")
i_dec = cg["columns"].index("dec")

groups = cg["groups"]

for g in groups:
    sum_ra = 0
    sum_dec = 0

    for s in g["stars"]:
        sum_ra = s[i_ra]
        sum_dec = s[i_dec]

    avg_ra = sum_ra / len(g["stars"])
    avg_dec = sum_dec / len(g["stars"])

    if ra > avg_ra - radius and ra < avg_ra + radius and dec > avg_dec - radius and dec < avg_dec + radius:
        print(avg_ra)
        print(avg_dec)
        print(g["id"])

