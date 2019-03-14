# Author: Karl Zylinski, Uppsala University

# This script finds comoving stars in a gridded database generated by create_database.py.
# It goes through the x-y-z grid folders inside the database-folder and for each x-y-z-cell it
# looks for stars within that cell which has similar position and velocity to other ones. It looks in
# nearby cells aswell if search radius requires it.

# First the comoving candidates are found by SQL queries into the gridded sqlite databases,
# this uses the variables maximum_broad_separation_pc and maximum_broad_velocity_diff_km_per_s as limits.
# After that it looks at all the found stars and is uses the smaller maximum_final_separation_pc and
# maximum_final_velocity_diff_km_per_s as limits. These are also combined with checking the errors
# of the position and velocities.

# For each found comoving star, the function that finds the comoving star is rerun, to see
# if any comoving neighbour has another comoving neighbour, potentially creating a network
# of comoving stars.

# The resulting groups of comoving stars are outputted into the by argument supplied filename.
# In this file one can find some metadata as well as the groups themselves.

import os
import sys
import conv
import sqlite3
import utils_path
import math
import vec3
import db_connection_cache
import time
import utils_str
import utils_dict

# For SQL query, does not look at errors, so has big margins!
maximum_broad_separation_pc = 20
maximum_broad_velocity_diff_km_per_s = 5

# After SQL query, a spherical comparison is done. These are then used combined with errors. We want tiny velocity difference!
maximum_final_separation_pc = 10
maximum_final_velocity_diff_km_per_s = 0.1

cut_parallax_over_error = 10

def verify_arguments():
    if len(sys.argv) != 3:
        return False

    if not os.path.isdir(sys.argv[1]):
        return False

    if os.path.isfile(sys.argv[2]) or os.path.isdir(sys.argv[2]):
        return False

    return True

assert verify_arguments(), "Usage: find_comoving_cut1.py db_folder output.cms"

db_folder = sys.argv[1]
output_filename = sys.argv[2]
start_time = time.time()

# Get metadata that was written alongside db
metadata_filename = utils_path.append(db_folder,"metadata")
assert os.path.isfile(metadata_filename), "metadata mising: %s" % metadata_filename
metadata_fh = open(metadata_filename, "r")
metadata_lines = metadata_fh.readlines()
metadata_fh.close()
metadata = {}

for mdl in metadata_lines:
    key_value_pair = mdl.split(":")

    if len(key_value_pair) != 2:
        error("metadata in %s is of incorrect format" % db_folder)

    metadata[key_value_pair[0]] = eval(key_value_pair[1])

cell_size_pc = metadata["cell_size"]
max_distance_pc = metadata["max_distance"]

# Get indiices of relavant colums (quicker lookup)
cols = metadata["columns"]
i_sid = cols.index("source_id")
i_ra = cols.index("ra")
i_dec = cols.index("dec")
i_dist = cols.index("distance")
i_pmra = cols.index("pmra")
i_pmdec = cols.index("pmdec")
i_rv = cols.index("radial_velocity")
i_x = cols.index("x")
i_y = cols.index("y")
i_z = cols.index("z")
i_vx = cols.index("vx")
i_vy = cols.index("vy")
i_vz = cols.index("vz")
i_ra_error = cols.index("ra_error")
i_dec_error = cols.index("dec_error")
i_dist_error = cols.index("distance_error")
i_pmra_error = cols.index("pmra_error")
i_pmdec_error = cols.index("pmdec_error")
i_rv_error = cols.index("radial_velocity_error")
i_parallax_over_error = cols.index("parallax_over_error")

columns_to_fetch = ",".join(cols) # Used in SQL query
comoving_groups = [] # This is where are found groups are stored
star_sid_to_comoving_group_index = {} # Lookup-table, also used to make sure no star is in two groups

# For getting data base names of cells close to current one that are within search radius.
def get_neighbouring_cell_databases(cur_x_idx, cur_y_idx, cur_z_idx, min_x, max_x, min_y, max_y, min_z, max_z):
    min_x_idx = int(min_x/cell_size_pc)
    max_x_idx = int(max_x/cell_size_pc)
    min_y_idx = int(min_y/cell_size_pc)
    max_y_idx = int(max_y/cell_size_pc)
    min_z_idx = int(min_z/cell_size_pc)
    max_z_idx = int(max_z/cell_size_pc)
    to_add = set()

    for x_idx in range(min_x_idx, max_x_idx + 1):
        for y_idx in range(min_y_idx, max_y_idx + 1):
            for z_idx in range(min_z_idx, max_z_idx + 1):
                if cur_x_idx == x_idx and cur_y_idx == y_idx and cur_z_idx == z_idx:
                    continue # Do not include self!!

                db_name = utils_path.append(db_folder, "%+d/%+d/%+d/cell.db" % (x_idx, y_idx, z_idx))

                if os.path.isfile(db_name):
                    to_add.add(db_name)

    return to_add

# Takes a star and looks around it for stars with simiar position and velocity,
# first in an over-sized box using SQL query, then it looks at smaller radii and tigther
# velocities. The function is recursive, calling it self for any found comoving star,
# creating a network of comoving stars.
def find_comoving_to_star(star, in_group_sids):
    if star_sid_to_comoving_group_index.get(star[i_sid]) != None:
        return [] # Star already in other group!

    x = star[i_x]
    y = star[i_y]
    z = star[i_z]
    x_idx = int(x/cell_size_pc)
    y_idx = int(y/cell_size_pc)
    z_idx = int(z/cell_size_pc)

    conn_filename = utils_path.append(db_folder, "%+d/%+d/%+d/cell.db" % (x_idx, y_idx, z_idx))
    conn = db_connection_cache.get(conn_filename, open_db_connections)

    min_x = max(x - maximum_broad_separation_pc, -max_distance_pc)
    max_x = min(x + maximum_broad_separation_pc, max_distance_pc)
    min_y = max(y - maximum_broad_separation_pc, -max_distance_pc)
    max_y = min(y + maximum_broad_separation_pc, max_distance_pc)
    min_z = max(z - maximum_broad_separation_pc, -max_distance_pc)
    max_z = min(z + maximum_broad_separation_pc, max_distance_pc)

    vx = star[i_vx]
    vy = star[i_vy]
    vz = star[i_vz]
    min_vx = vx - maximum_broad_velocity_diff_km_per_s
    max_vx = vx + maximum_broad_velocity_diff_km_per_s
    min_vy = vy - maximum_broad_velocity_diff_km_per_s
    max_vy = vy + maximum_broad_velocity_diff_km_per_s
    min_vz = vz - maximum_broad_velocity_diff_km_per_s
    max_vz = vz + maximum_broad_velocity_diff_km_per_s

    # Just boxes in everything in an oversized box
    # (compare value of maximum_broad_separation_pc to maximum_final_separation_pc).
    # Makes sure to not compare stars with themselves by excluding using source_ids.
    find_nearby_query = '''
        SELECT %s
        FROM gaia
        WHERE source_id NOT IN (%s)
        AND (x > %f AND x < %f)
        AND (y > %f AND y < %f)
        AND (z > %f AND z < %f)
        AND (vx > %f AND vx < %f)
        AND (vy > %f AND vy < %f)
        AND (vz > %f AND vz < %f)''' % (
            columns_to_fetch,
            ",".join(map(lambda x: str(x), in_group_sids)),
            min_x, max_x,
            min_y, max_y,
            min_z, max_z,
            min_vx, max_vx,
            min_vy, max_vy,
            min_vz, max_vz)

    maybe_comoving_to_star = conn.execute(find_nearby_query).fetchall()
    neighbour_cells_to_include = get_neighbouring_cell_databases(x_idx, y_idx, z_idx, min_x, max_x, min_y, max_y, min_z, max_z)

    for neighbour_cell_db_name in neighbour_cells_to_include:
        neighbour_conn = db_connection_cache.get(neighbour_cell_db_name, open_db_connections)
        maybe_comoving_to_star.extend(neighbour_conn.execute(find_nearby_query).fetchall())

    if len(maybe_comoving_to_star) == 0:
        return []

    comoving_to_star = []

    pos = [star[i_x], star[i_y], star[i_z]]
    vel_km_per_s = [star[i_vx], star[i_vy], star[i_vz]]

    ra = star[i_ra] * conv.deg_to_rad
    dec = star[i_dec] * conv.deg_to_rad
    dist = star[i_dist]
    ra_error = star[i_ra_error] * conv.deg_to_rad
    dec_error = star[i_dec_error] * conv.deg_to_rad
    dist_error = star[i_dist_error]
    pmra = star[i_pmra] * conv.mas_per_yr_to_rad_per_s
    pmdec = star[i_pmdec] * conv.mas_per_yr_to_rad_per_s
    rv = star[i_rv]
    pmra_error = star[i_pmra_error] * conv.mas_per_yr_to_rad_per_s
    pmdec_error = star[i_pmdec_error] * conv.mas_per_yr_to_rad_per_s
    error_rv = star[i_rv_error]

    for mcs in maybe_comoving_to_star:
        if star_sid_to_comoving_group_index.get(mcs[i_sid]) != None:
            continue

        if mcs[i_parallax_over_error] < cut_parallax_over_error:
            continue

        mcs_pos = [mcs[i_x], mcs[i_y], mcs[i_z]]
        pos_diff_len = vec3.mag(vec3.sub(mcs_pos, pos))

        mcs_ra = mcs[i_ra] * conv.deg_to_rad
        mcs_dec = mcs[i_dec] * conv.deg_to_rad
        mcs_dist = mcs[i_dist]
        mcs_ra_error = mcs[i_ra_error] * conv.deg_to_rad
        mcs_dec_error = mcs[i_dec_error] * conv.deg_to_rad
        mcs_dist_error = mcs[i_dist_error]

        pos_diff_len_error = vec3.celestial_magnitude_of_position_difference_error(
                                ra, dec, dist,
                                ra_error, dec_error, dist_error,
                                mcs_ra, mcs_dec, mcs_dist,
                                mcs_ra_error, mcs_dec_error, mcs_dist_error)

        # Position cut, with added 3*error
        if pos_diff_len > maximum_final_separation_pc + 3*pos_diff_len_error:
            continue

        mcs_pmra = mcs[i_pmra]*conv.mas_per_yr_to_rad_per_s
        mcs_pmdec = mcs[i_pmdec]*conv.mas_per_yr_to_rad_per_s
        mcs_rv = mcs[i_rv]
        mcs_pmra_error = mcs[i_pmra_error]*conv.mas_per_yr_to_rad_per_s
        mcs_pmdec_error = mcs[i_pmdec_error]*conv.mas_per_yr_to_rad_per_s
        mcs_error_rv = mcs[i_rv_error]

        mcs_vel_km_per_s = [mcs[i_vx], mcs[i_vy], mcs[i_vz]]
        speed_diff = vec3.mag(vec3.sub(mcs_vel_km_per_s, vel_km_per_s))

        speed_diff_error = vec3.celestial_magnitude_of_velocity_difference_error(
            mcs_ra, mcs_dec, mcs_dist * conv.pc_to_km,
            mcs_ra_error, mcs_dec_error, mcs_dist_error * conv.pc_to_km,
            mcs_pmra, mcs_pmdec, mcs_rv,
            mcs_pmra_error, mcs_pmdec_error, mcs_error_rv,
            ra, dec, dist * conv.pc_to_km,
            ra_error, dec_error, dist_error * conv.pc_to_km,
            pmra, pmdec, rv,
            pmra_error, pmdec_error, error_rv)
        
        # Velocity cut, with added 3*error
        if speed_diff > maximum_final_velocity_diff_km_per_s + 3*speed_diff_error:
            continue

        comoving_to_star.append(mcs)

    if len(comoving_to_star) == 0:
        return []

    # Important! Makes sure that recursive call further down does not re-use already used star.
    in_group_sids.update(map(lambda x: x[i_sid], comoving_to_star))
    resulting_stars = comoving_to_star.copy()

    # Look for comoving stars to the comoving stars, creating a network of comoving stars.
    for cm_star in comoving_to_star:
        resulting_stars.extend(find_comoving_to_star(cm_star, in_group_sids))

    return resulting_stars

total_stars = metadata["total_stars"]
total_stars_processed = 0
open_db_connections = {} # Used by db_connection_cache to keep track of living databases.

# Goes over all stars within a cell and tries to find other stars that are comoving
# to it. This and find_comoving_to_star-function makes sure to NOT include the same
# in more than one group.
def find_comoving_stars_in_cell(db_filename):
    global total_stars_processed

    conn = db_connection_cache.get(db_filename, open_db_connections)
    all_stars_select_str = "SELECT %s FROM gaia" % columns_to_fetch
    all_stars = conn.execute(all_stars_select_str).fetchall()
    
    for star in all_stars:
        total_stars_processed = total_stars_processed + 1

        sid = star[i_sid]

        if star_sid_to_comoving_group_index.get(sid) != None:
            continue # Star already in other group!

        in_group_sids = set()
        in_group_sids.add(sid)
        comoving_to_star = find_comoving_to_star(star, in_group_sids)

        if len(comoving_to_star) == 0:
            continue

        comoving_group = comoving_to_star + [star]
        group_index = len(comoving_groups)
        group_size = len(comoving_group)
        group_object = {}
        group_object["id"] = group_index
        group_object["stars"] = list(comoving_group)
        group_object["size"] = group_size

        # Add all stars in group to lookup-table so they aren't re-used
        for cms in comoving_group:
            star_sid_to_comoving_group_index[cms[i_sid]] = group_index

        comoving_groups.append(group_object)

        cur_time = time.time()
        time_elapsed = cur_time - start_time
        time_left_h = ((time_elapsed/total_stars_processed)*(total_stars - total_stars_processed))/3600
        
        print("Found comoving group of size %d. %d/%d done. Time left: %.001f hours" % (group_size, total_stars_processed, total_stars, time_left_h))

    db_connection_cache.remove_unused(open_db_connections)

# Traverse the x/y/z/cell.db directory structure and call find_comoving_stars_in_cell for each cell.db
for ix_str in os.listdir(db_folder):
    ix_folder = utils_path.append(db_folder, ix_str)

    if not os.path.isdir(ix_folder):
        continue

    ix = utils_str.to_int(ix_str) # ix as in integer x

    if ix == None:
        continue

    for iy_str in os.listdir(ix_folder):
        iy_folder = utils_path.append(ix_folder, iy_str)

        if not os.path.isdir(iy_folder):
            continue

        iy = utils_str.to_int(iy_str)

        if iy == None:
            continue

        for iz_str in os.listdir(iy_folder):
            iz_folder = utils_path.append(iy_folder, iz_str)

            if not os.path.isdir(iz_folder):
                continue

            iz = utils_str.to_int(iz_str)

            if iz == None:
                continue

            cell_db_filename = utils_path.append(iz_folder, "cell.db")
            
            if not os.path.isfile(cell_db_filename):
                continue

            find_comoving_stars_in_cell(cell_db_filename)

db_connection_cache.remove_all(open_db_connections)

output_dict = {}

for k,v in metadata.items():
    output_dict[k] = v

output_dict["max_sep"] = maximum_final_separation_pc
output_dict["max_vel_mag_diff"] = maximum_final_velocity_diff_km_per_s
output_dict["groups"] = comoving_groups
utils_dict.write(output_dict, output_filename)

print("Result saved to %s" % output_filename)