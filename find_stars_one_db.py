# Author: Karl Zylinski, Uppsala University

import datetime
import metadata
import dict_utils
import keyboard
import os
import find_stars_in_db
from const import *
from functools import reduce

db_filename = "gaia_dr2_rv_2019-02-22-15-56-06.db"

debug_print_found = True
max_sep = 5 # maximal separation of pairs, pc
max_vel_angle_diff = 1 # maximal angular difference of velocity vectors, degrees
max_vel_mag_diff = 10 # maximal velocity difference between velocity vectors, km/s

state = find_stars_in_db.setup_state()
state["memory_map_size"] = 8589934592

find_stars_in_db.find(db_filename, state, debug_print_found,
     max_sep, max_vel_angle_diff, max_vel_mag_diff, None)

comoving_groups_to_output = []
num_pairs_of_size = {}

comoving_groups = state["comoving_groups"]
for g in comoving_groups:
    if g["dead"]:
        continue

    cur_num = num_pairs_of_size.get(g["size"])
    if cur_num == None:
        num_pairs_of_size[g["size"]] = 1
    else:
        num_pairs_of_size[g["size"]] = cur_num + 1

    del g["dead"]
    comoving_groups_to_output.append(g)

print()
print("Found:")
print("------")
for size, num in num_pairs_of_size.items():
    print("%d of size %d" % (num, size))

output_name = datetime.datetime.now().strftime("found-pairs-%Y-%m-%d-%H-%M-%S.txt")
file = open(output_name,"w")
file.write(str(comoving_groups_to_output))
file.close()