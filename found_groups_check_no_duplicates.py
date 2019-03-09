# Author: Karl Zylinski, Uppsala University

import sys
import os
import utils_str
import utils_dict

def verify_arguments():
    if len(sys.argv) != 2:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_check_no_duplicates.py file"
input_filename = sys.argv[1]
cg = utils_dict.read(input_filename)
cols = cg["columns"]
i_source_id = cols.index("source_id")
source_ids_used = set()
found_groups = cg["groups"]

for g in found_groups:
    for s in g["stars"]:
        assert s[i_source_id] not in source_ids_used, "DUPLICATE"
        source_ids_used.add(s[i_source_id])