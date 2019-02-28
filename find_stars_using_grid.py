# Author: Karl Zylinski, Uppsala University

import datetime
import metadata
import dict_utils
import keyboard
import os
import find_stars_in_db
from const import *
from functools import reduce

db_folder = "db_gaia_dr2_rv_2019-02-26-18-11-25"
metadata_dict = metadata.get(db_folder)
cell_depth = int(dict_utils.get_or_error(metadata_dict, "cell_depth", "cell_depth missing in %s metadata" % db_folder))

debug_print_found = False
max_sep = 5 # maximal separation of pairs, pc
max_vel_angle_diff = 1 # maximal angular difference of velocity vectors, degrees
max_vel_mag_diff = 10 # maximal velocity difference between velocity vectors, km/s

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

def str_to_int(str):
    try:
        return int(str)
    except ValueError:
        return None

def file_remove_extension(path):
    ext_sep = path.rfind(".")

    if ext_sep == -1:
        return path

    return path[0:ext_sep]

ras_done = 0

run = True

def quit(key):
    global run
    run = False

keyboard.hook_key('q', quit)
state = find_stars_in_db.setup_state()

for ra_entry in os.listdir(db_folder):
    if run == False:
        break

    ra_folder = "%s/%s" % (db_folder, ra_entry)
    if not os.path.isdir(ra_folder):
        continue

    ira = str_to_int(ra_entry)

    if ira == None:
        continue

    print("RAs done: %d" % ras_done)
    ras_done = ras_done + 1

    for dec_entry in os.listdir(ra_folder):
        if run == False:
            break

        ra_dec_folder = "%s/%s" % (ra_folder, dec_entry)
        
        if not os.path.isdir(ra_dec_folder):
            continue

        idec = str_to_int(dec_entry)

        if idec == None:
            continue

        for db in os.listdir(ra_dec_folder):
            if not db.endswith(".db"):
                continue

            idist_idx = str_to_int(file_remove_extension(db))
            assert idist_idx != None, ".db file should have only numeric distance in name"
            idist = idist_idx * cell_depth
            db_filename = "%s/%s" % (ra_dec_folder, db)
            find_stars_in_db.find(db_filename, state, debug_print_found,
                             max_sep, max_vel_angle_diff, max_vel_mag_diff,
                             lambda min_d, max_d, min_ra, max_ra, min_dec, max_dec: get_neighbour_databases(ira, idec, idist, idist_idx, min_d, max_d, min_ra, max_ra, min_dec, max_dec))

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