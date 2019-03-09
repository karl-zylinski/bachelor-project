import os
import sys
import conv
import sqlite3
import utils_path
import math
import vec3
import time

# THIS FILE DOES THE FOLLOWING CUTS
maximum_separation_pc = 15
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
db_filename = utils_path.append(db_folder, "single_db.db")
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

comparison_cols = ["source_id", "ra", "dec", "distance", "pmra", "pmdec", "radial_velocity"]

# Get indiices of relavant colums (quicker lookup)
i_sid = comparison_cols.index("source_id")
i_ra = comparison_cols.index("ra")
i_dec = comparison_cols.index("dec")
i_dist = comparison_cols.index("distance")
i_pmra = comparison_cols.index("pmra")
i_pmdec = comparison_cols.index("pmdec")
i_rv = comparison_cols.index("radial_velocity")

columns_to_fetch = ",".join(comparison_cols)
columns_to_save = ",".join(metadata["columns"])
comoving_groups = []
star_sid_to_comoving_group_index = {}

def find_comoving_to_star(star, in_group_sids):
    if star_sid_to_comoving_group_index.get(star[i_sid]) != None:
        return []

    ### Position min/max
    dist = star[i_dist]
    ra = star[i_ra]
    dec = star[i_dec]
    max_angular_sep = (maximum_separation_pc/dist)*conv.rad_to_deg

    # ra becomes smaller the further up we look
    ra_angular_sep_scaling = math.cos(conv.deg_to_rad*abs(dec))

    if ra_angular_sep_scaling > 10000:
        ra_angular_sep_scaling = 10000

    min_ra = ra - max_angular_sep/ra_angular_sep_scaling
    max_ra = ra + max_angular_sep/ra_angular_sep_scaling
    min_dec = dec - max_angular_sep
    max_dec = dec + max_angular_sep
    min_dist = dist - maximum_separation_pc
    max_dist = dist + maximum_separation_pc

    ra_where_op = "AND"
    if min_ra < 0 and max_ra < 360:
        min_ra = 360 + min_ra

        if min_ra > max_ra:
            ra_where_op = "OR"
    
    if min_ra > 0 and max_ra >= 360:
        max_ra = max_ra - 360

        if min_ra > max_ra:
            ra_where_op = "OR"

    ### Velocity min/max
    pmra = star[i_pmra]
    pmdec = star[i_pmdec]
    rv = star[i_rv]
    ang_vel_diff = maximum_velocity_diff_km_s / (conv.parsec_to_km * dist * conv.mas_per_yr_to_rad_per_s)
    min_pmra = pmra - ang_vel_diff
    max_pmra = pmra + ang_vel_diff
    min_pmdec = pmdec - ang_vel_diff
    max_pmdec = pmdec + ang_vel_diff
    min_rv = rv - maximum_velocity_diff_km_s
    max_rv = rv + maximum_velocity_diff_km_s

    find_nearby_query = '''
        SELECT %s
        FROM gaia
        WHERE source_id NOT IN (%s)
        AND (distance > %f AND distance < %f)
        AND (ra > %f %s ra < %f)
        AND (dec > %f AND dec < %f)
        AND (pmra > %f AND pmra < %f)
        AND (pmdec > %f AND pmdec < %f)
        AND (radial_velocity > %f AND radial_velocity < %f)''' % (
            columns_to_fetch,
            ",".join(map(lambda x: str(x), in_group_sids)),
            min_dist, max_dist,
            min_ra, ra_where_op, max_ra,
            min_dec, max_dec,
            min_pmra, max_pmra,
            min_pmdec, max_pmdec,
            min_rv, max_rv)

    maybe_comoving_to_star = conn.execute(find_nearby_query).fetchall()

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

    for cm_star in comoving_to_star:
        find_comoving_to_star(cm_star, in_group_sids)

num_stars = int(conn.execute("SELECT count(source_id) FROM gaia").fetchone()[0])
num_done = 1
all_stars_select_str = "SELECT %s FROM gaia" % columns_to_fetch
all_stars = conn.execute(all_stars_select_str)

start_time = time.time()

for star in all_stars:
    cur_time = time.time()
    time_elapsed = cur_time - start_time
    time_left_h = ((time_elapsed/num_done)*(num_stars - num_done))/3600/24
    print("%d/%d (%.1f percent, time left: %.001f days)" % (num_done, num_stars, num_done/num_stars, time_left_h))
    num_done = num_done + 1

    sid = star[i_sid]

    if star_sid_to_comoving_group_index.get(sid) != None:
        continue

    in_group_sids = set()
    in_group_sids.add(sid)

    find_comoving_to_star(star, in_group_sids)

    if len(in_group_sids) == 1:
        continue

    comoving_group = conn.execute("SELECT %s FROM gaia WHERE source_id IN (%s)" % (
        columns_to_save, ",".join(map(lambda x: str(x), in_group_sids)))).fetchall()

    group_index = len(comoving_groups)
    group_size = len(comoving_group)
    group_object = {}
    group_object["stars"] = list(comoving_group)
    group_object["size"] = group_size

    for cms in comoving_group:
        star_sid_to_comoving_group_index[cms[i_sid]] = group_index

    comoving_groups.append(group_object)

    print("Found comoving group of size %d" % group_size)
