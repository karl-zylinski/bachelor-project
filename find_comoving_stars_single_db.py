# Author: Karl Zylinski, Uppsala University

import datetime
import metadata
import os
import sys
import find_comoving_stars_internal

def verify_arguments():
    if len(sys.argv) != 2:
        return False

    if type(sys.argv[1]) != str:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: find_comoving_stars_single_db.py database.db"

db_filename = sys.argv[1]
debug_print_found = True
max_sep = 5 # maximal separation of pairs, pc
max_vel_angle_diff = 1 # maximal angular difference of velocity vectors, degrees
max_vel_mag_diff = 10 # maximal velocity difference between velocity vectors, km/s

state = find_comoving_stars_internal.setup_state()
state["memory_map_size"] = 8589934592

find_comoving_stars_internal.find(db_filename, state, debug_print_found,
     max_sep, max_vel_angle_diff, max_vel_mag_diff, None)

find_comoving_stars_internal.save_result(state)