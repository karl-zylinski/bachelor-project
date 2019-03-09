import os
import sys
import conv
import sqlite3
import utils_path
import math
import vec3
import time
import db_connection_cache

# THIS FILE DOES THE FOLLOWING CUTS
maximum_separation_pc = 20
maximum_velocity_diff_km_s = 5

maximum_velocity_diff_km_per_year = maximum_velocity_diff_km_s / conv.sec_to_year

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
output_file = sys.argv[2]

conn = sqlite3.connect(db_filename)
conn.execute('pragma mmap_size=8589934592;')

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
max_dist_pc = metadata["max_dist"]
max_cells_per_axis = int(max_dist_pc/cell_size_pc)
cols = metadata["columns"]

# Get indiices of relavant colums (quicker lookup)
i_sid = comparison_cols.index("source_id")
i_ra = comparison_cols.index("ra")
i_dec = comparison_cols.index("dec")
i_dist = comparison_cols.index("distance")
i_pmra = comparison_cols.index("pmra")
i_pmdec = comparison_cols.index("pmdec")
i_rv = comparison_cols.index("radial_velocity")
i_x = comparison_cols.index("x")
i_y = comparison_cols.index("y")
i_z = comparison_cols.index("z")
i_vx = comparison_cols.index("vx")
i_vy = comparison_cols.index("vy")
i_vz = comparison_cols.index("vz")

columns_to_fetch = ",".join(cols)
comoving_groups = []
star_sid_to_comoving_group_index = {}

def get_neighbouring_cell_databases(min_x, max_x, min_y, max_y, min_z, max_z):
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
                    continue

                db_name = utils_path.append_many(db_folder, [str(x_idx), str(y_idx), str(z_idx), "cell.db"])

                if os.path.isfile(db_name):
                    to_add.add(db_name)

    return to_add

def find_comoving_to_star(star, in_group_sids):
    if star_sid_to_comoving_group_index.get(star[i_sid]) != None:
        return []

    x = star[i_x]
    y = star[i_y]
    z = star[i_z]
    cur_x_idx = int(x/cell_size_pc)
    cur_y_idx = int(y/cell_size_pc)
    cur_z_idx = int(z/cell_size_pc)

    conn_filename = utils_path.append_many(db_folder, [str(x_idx), str(y_idx), str(z_idx), "cell.db"])
    conn = db_connection_cache.get(conn_filename, open_db_connections)

    min_x = math.max(x - maximum_separation_pc, -maximum_separation_pc)
    max_x = math.min(x + maximum_separation_pc, maximum_separation_pc)
    min_y = math.max(y - maximum_separation_pc, -maximum_separation_pc)
    max_y = math.min(y + maximum_separation_pc, maximum_separation_pc)
    min_z = math.max(z - maximum_separation_pc, -maximum_separation_pc)
    max_z = math.min(z + maximum_separation_pc, maximum_separation_pc)

    vx = star[i_vx]
    vy = star[i_vy]
    vz = star[i_vz]
    min_vx = vx - maximum_velocity_diff_km_per_year
    max_vx = vx + maximum_velocity_diff_km_per_year
    min_vy = vy - maximum_velocity_diff_km_per_year
    max_vy = vy + maximum_velocity_diff_km_per_year
    min_vz = vz - maximum_velocity_diff_km_per_year
    max_vz = vz + maximum_velocity_diff_km_per_year

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
    neighbour_cells_to_include = get_neighbouring_cell_databases(min_x, max_x, min_y, max_y, min_z, max_z)

    for neighbour_cell_db_name in neighbour_cells_to_include:
        neighbour_conn = db_connection_cache.get(neighbour_cell_db_name, open_db_connections)
        maybe_comoving_to_star.extend(neighbour_conn.execute(find_nearby_query).fetchall())

    if len(maybe_comoving_to_star) == 0:
        return []

    comoving_to_star = []
    pos = vec3.cartesian_position_from_celestial(ra, dec, dist)
    vel_km_per_year = vec3.cartesian_velocity_from_celestial(ra, dec, dist,
        pmra * conv.mas_to_deg, pmdec * conv.mas_to_deg, rv / conv.sec_to_year)

    for mcs in maybe_comoving_to_star:
        if star_sid_to_comoving_group_index.get(mcs[i_sid]) != None:
            continue

        mcs_ra = mcs[i_ra]
        mcs_dec = mcs[i_dec]
        mcs_dist = mcs[i_dist]
        mcs_pmra = mcs[i_pmra]
        mcs_pmdec = mcs[i_pmdec]
        mcs_rv = mcs[i_rv]

        mcs_pos = vec3.cartesian_position_from_celestial(mcs_ra, mcs_dec, mcs_dist)
        pos_diff_len = vec3.len(vec3.sub(mcs_pos, pos))

        if pos_diff_len > maximum_separation_pc:
            continue

        mcs_vel_km_per_year = vec3.cartesian_velocity_from_celestial(mcs_ra, mcs_dec, mcs_dist,
            mcs_pmra * conv.mas_to_deg, mcs_pmdec * conv.mas_to_deg, mcs_rv / conv.sec_to_year)

        speed_diff_km_per_year = vec3.len(vec3.sub(mcs_vel_km_per_year, vel_km_per_year)) 
        
        if speed_diff_km_per_year > maximum_velocity_diff_km_per_year:
            continue

        comoving_to_star.append(mcs)

    in_group_sids.update(map(lambda x: x[i_sid], comoving_to_star))
    resulting_stars = comoving_to_star.copy()

    for cm_star in comoving_to_star:
        resulting_stars.extend(find_comoving_to_star(cm_star, in_group_sids))

    return resulting_stars

num_done = 0
open_db_connections = {}

def find_comoving_stars_in_cell(db_filename)
    conn = db_connection_cache.get(db_filename, open_db_connections)
    all_stars_select_str = "SELECT %s FROM gaia" % columns_to_fetch
    all_stars = conn.execute(all_stars_select_str)
    
    for star in all_stars:
        num_done = num_done + 1
        sid = star[i_sid]

        if star_sid_to_comoving_group_index.get(sid) != None:
            continue

        in_group_sids = set()
        in_group_sids.add(sid)
        comoving_group = find_comoving_to_star(star, in_group_sids)

        if len(comoving_group) == 0:
            continue

        group_index = len(comoving_groups)
        group_size = len(comoving_group)
        group_object = {}
        group_object["stars"] = list(comoving_group)
        group_object["size"] = group_size

        for cms in comoving_group:
            star_sid_to_comoving_group_index[cms[i_sid]] = group_index

        comoving_groups.append(group_object)

        print("Found comoving group of size %d" % group_size)

start_time = time.time()
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
