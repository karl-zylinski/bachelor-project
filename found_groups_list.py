# Author: Karl Zylinski, Uppsala University

# Goes through the ouput from the find_comoving_stars* scripts and prints
# a list of clusters inside, how many there are of each cluster size etc.

import sys
import os
import utils_str

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
input_fh = open(input_filename, 'rb')
found_pairs = eval(input_fh.read())
input_fh.close()
assert type(found_pairs) is list, "Supplied file has broken format"

if len(sys.argv) == 3:
    input_size = int(sys.argv[2])
    print("id of groups with size %d:" % input_size)
    for fp in found_pairs:
        if int(fp["size"]) == input_size:
            print(fp["id"])
else:
    num_pairs_of_size = {}

    for fp in found_pairs:
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
