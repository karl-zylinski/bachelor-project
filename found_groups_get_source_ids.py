# Author: Karl Zylinski, Uppsala University

# Plots separation agsinst velocity difference

import sys
import os
import matplotlib.pyplot as plt
import vec3
import conv
import numpy
import utils_dict

def verify_arguments():
    if len(sys.argv) != 3:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    if os.path.isfile(sys.argv[2]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_get_source_ids.py input output"
input_filename = sys.argv[1]
cg = utils_dict.read(input_filename)
output_filename = sys.argv[2]
i_source_id = cg["columns"].index("source_id")
out_fh = open(output_filename, "w")
found_grounds = cg["groups"]

for fp in found_grounds:
    for s in fp["stars"]:
        sid = s[i_source_id]
        out_fh.write("%d\n" % sid)

out_fh.close()


