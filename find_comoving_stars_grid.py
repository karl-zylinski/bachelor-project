# Author: Karl Zylinski, Uppsala University

# Takes a grid generated by create_grid_database_from_raw.py (specified by argument
# and for each cell-database it calls find_comoving_stars_internal.py. The result is
# then saved to a file.

import datetime
import metadata
import utils_dict
import keyboard
import os
import find_comoving_stars_internal
import sys
import utils_file
import utils_str
import conv
from functools import reduce

def verify_arguments():
    if len(sys.argv) != 2:
        return False

    if type(sys.argv[1]) != str:
        return False

    if not os.path.isdir(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: find_comoving_stars_grid.py database_folder"

db_folder = sys.argv[1]
metadata_dict = metadata.get(db_folder)
cell_depth = int(utils_dict.get_or_error(metadata_dict, "cell_depth", "cell_depth missing in %s metadata" % db_folder))

debug_print_found = False
max_sep = 5 # maximal separation of pairs, pc
max_vel_angle_diff = 1 # maximal angular difference of velocity vectors, degrees
max_vel_mag_diff = 10 # maximal velocity difference between velocity vectors, km/s

# This uses the max/min_xxx variables to look if those fall outside the current
# cell. The current cell is specified by (ira, idec, idist), i for integer.
# If the max/min_xxx do fall outside the cell, the neighbour is found and
# added to a list. The list is returned at the end.
def get_neighbour_databases(ira, idec, idist, idist_idx, min_d, max_d, min_ra, max_ra, min_dec, max_dec):
    min_delta_depth = 0
    max_delta_depth = 0
    min_delta_ra = 0
    max_delta_ra = 0
    min_delta_dec = 0
    max_delta_dec = 0

    if max_ra > (ira + 1):
        max_delta_ra = 1
    
    if min_ra < ira:
        min_delta_ra = -1

    if max_dec > (idec + 1):
        max_delta_dec = 1
    
    if min_dec < idec:
        min_delta_dec = -1

    if max_d > (idist + cell_depth):
        max_delta_depth = 1
    
    if min_d < idist:
        min_delta_depth = -1

    to_add = []

    for delta_ra in range(min_delta_ra, max_delta_ra + 1):
        for delta_dec in range(min_delta_dec, max_delta_dec + 1):
            for delta_dist in range(min_delta_depth, max_delta_depth + 1):
                if delta_ra == 0 and delta_dec == 0 and delta_dist == 0:
                    continue

                coord_ra = ira + delta_ra
                coord_dec = idec + delta_dec
                coord_dist = idist_idx + delta_dist

                if coord_dec < -89:
                    coord_ra = coord_ra + 180
                    coord_dec = -90 - (coord_dec + 89)

                if coord_dec > 89:
                    coord_ra = coord_ra + 180
                    coord_dec = 90 - (coord_dec - 89)

                if coord_ra < 0:
                    coord_ra = 360 + coord_ra

                if coord_ra > 359:
                    coord_ra = coord_ra - 360

                if coord_dist < 0:
                    continue # no wrap around for distance

                db_name = "%s/%d/%+d/%d.db" % (db_folder, coord_ra, coord_dec, coord_dist)

                if os.path.isfile(db_name):
                    to_add.append(db_name)

    return to_add

ras_done = 0
state = find_comoving_stars_internal.setup_state()

# goes through ra/dec/dist.db structure inside db_folder
for ra_entry in os.listdir(db_folder):
    ra_folder = "%s/%s" % (db_folder, ra_entry)
    if not os.path.isdir(ra_folder):
        continue

    ira = utils_str.to_int(ra_entry)
    if ira == 1:
        break
        
    if ira == None:
        continue

    print("RAs done: %d" % ras_done)
    ras_done = ras_done + 1

    for dec_entry in os.listdir(ra_folder):
        ra_dec_folder = "%s/%s" % (ra_folder, dec_entry)
        
        if not os.path.isdir(ra_dec_folder):
            continue

        idec = utils_str.to_int(dec_entry)

        if idec == None:
            continue

        for db in os.listdir(ra_dec_folder):
            if not db.endswith(".db"):
                continue

            idist_idx = utils_str.to_int(utils_file.remove_extension(db))
            assert idist_idx != None, ".db file should have only numeric distance in name"
            idist = idist_idx * cell_depth
            db_filename = "%s/%s" % (ra_dec_folder, db)

            # Runs the meat of the comoving-star-finder. The big lambda
            # is there to pass on info to get_neighbour_databases,
            # which find_comoving_stars_internal.find calls before doing
            # any sql queries.
            find_comoving_stars_internal.find(db_filename, state, debug_print_found,
                             max_sep, max_vel_angle_diff, max_vel_mag_diff,
                             lambda min_d, max_d, min_ra, max_ra, min_dec, max_dec: get_neighbour_databases(ira, idec, idist, idist_idx, min_d, max_d, min_ra, max_ra, min_dec, max_dec))

find_comoving_stars_internal.save_result(state)
