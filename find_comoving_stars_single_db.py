# Author: Karl Zylinski, Uppsala University

import datetime
import metadata
import os
import sys
import find_comoving_stars_internal
import db_connection_cache
import utils_path

def verify_arguments():
    if len(sys.argv) != 2:
        return False

    if not os.path.isdir(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: find_comoving_stars_single_db.py db_folder"

db_folder = sys.argv[1]
db_filename = utils_path.append(db_folder, "single_db.db")
debug_print_found = True
max_sep = 10 # maximal separation of pairs, pc
max_vel_mag_diff = 1 # maximal velocity difference between velocity vectors, km/s

db_connection_cache.set_memory_map_size(8589934592)

state = find_comoving_stars_internal.init(db_folder, debug_print_found, max_sep, max_vel_mag_diff, None)
find_comoving_stars_internal.find(db_filename, state)
find_comoving_stars_internal.save_result(state)
find_comoving_stars_internal.deinit(state)