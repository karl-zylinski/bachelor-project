# Author: Karl Zylinski, Uppsala University

import sqlite3
import math
import datetime
import os
import metadata
import dict_utils
import keyboard
from functools import reduce

db_folder = "db_gaia_dr2_rv_2019-02-26-18-11-25"
metadata_dict = metadata.get(db_folder)
cell_depth = int(dict_utils.get_or_error(metadata_dict, "cell_depth", "cell_depth missing in %s metadata" % db_folder))

debug_print_found = False
max_sep = 5 # maximal separation of pairs, pc
max_vel_angle_diff = 1 # maximal angular difference of velocity vectors, degrees
max_vel_mag_diff = 10 # maximal velocity difference between velocity vectors, km/s
columns_to_fetch = "source_id, ra, dec, parallax, pmra, pmdec, radial_velocity, distance, phot_g_mean_mag"

# these are just in order as they appear in columns_to_fetch - used to fetch stuff from sql result arrays
i_source_id = 0
i_ra = 1
i_dec = 2
i_parallax = 3
i_pmra = 4
i_pmdec = 5
i_radial_velocity = 6
i_distance = 7
i_phot_g_mean_mag = 8

deg_to_rad = math.pi/180
rad_to_deg = 180/math.pi
year_to_sec = 365.25 * 24 * 3600
mas_to_deg = 1.0/3600000.0
mas_per_yr_to_rad_per_s = (mas_to_deg*deg_to_rad)/year_to_sec
parsec_to_km = 3.08567758 * math.pow(10, 13)

def vec3_len(v):
    return math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])

def vec3_dot(v1, v2):
    return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]

def vec3_scale(v, s):
    return [v[0] * s, v[1] * s, v[2] * s]

# converts celestial vector to cartesian (ra and dec in degrees)
def vec3_from_celestial(ra, dec, r):
    ra_rad = ra * deg_to_rad
    dec_rad = dec * deg_to_rad
    return [r * math.cos(ra_rad) * math.cos(dec_rad), # cos(ra_rad) * sin(pi/2 - dec_rad)
            r * math.sin(ra_rad) * math.cos(dec_rad), # sin(ra_rad) * sin(pi/2 - dec_rad)
            r * math.sin(dec_rad)] # cos(pi/2 - dec_rad)


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

comoving_groups = [] # index is pair identifier, each entry is an array of stars
star_sid_to_comoving_group_idx = {} # maps star source_id to comoving_groups index, for checking for redundancies

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
open_connections = {}

def get_connection(db_name, star_idx):
    existing = open_connections.get(db_name)

    if existing:
        existing["used_at"] = star_idx
        return existing["conn"]
    else:
        conn = sqlite3.connect(db_name)
        conn.execute('pragma mmap_size=10000000;')
        conn_obj = {}
        conn_obj["used_at"] = star_idx
        conn_obj["conn"] = conn
        open_connections[db_name] = conn_obj
        return conn

def remove_unused_connections(cur_idx):
    to_remove = []

    for db_name, c in open_connections.items():
        if cur_idx - c["used_at"] > 100:
            c["conn"].close()
            to_remove.append(db_name)

    for r in to_remove:
        del open_connections[r]

run = True

def quit(key):
    global run
    run = False

keyboard.hook_key('q', quit)

stars_done = 0
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

            if stars_done % 100 == 0:
                remove_unused_connections(stars_done)

            idist_idx = str_to_int(file_remove_extension(db))
            assert idist_idx != None, ".db file should have only numeric distance in name"
            idist = idist_idx * cell_depth
            db_filename = "%s/%s" % (ra_dec_folder, db)
            conn = get_connection(db_filename, stars_done)
            c = conn.cursor()
            all_stars = c.execute("SELECT %s FROM gaia" % columns_to_fetch).fetchall()

            for s in all_stars:
                sid = s[i_source_id]
                ra = s[i_ra] # deg
                dec = s[i_dec] # deg
                pmra = s[i_pmra] # mas/yr
                pmdec = s[i_pmdec] # mas/yr
                vrad = s[i_radial_velocity] # km/s
                d = s[i_distance] # distance in pc
                min_d = d - max_sep
                max_d = d + max_sep
                max_angular_sep = (max_sep*rad_to_deg)/d
                min_ra = ra - max_angular_sep
                max_ra = ra + max_angular_sep
                min_dec = dec - max_angular_sep
                max_dec = dec + max_angular_sep

                # this is a mas/yr value that corresponds to angular value for tangential speed max_vel_mag_diff/2 for this star
                ang_vel_diff = (max_vel_mag_diff/2) / (parsec_to_km * d * mas_per_yr_to_rad_per_s)

                pmra_ang_vel_min = pmra - ang_vel_diff
                pmra_ang_vel_max = pmra + ang_vel_diff
                pmdec_ang_vel_min = pmdec - ang_vel_diff
                pmdec_ang_vel_max = pmdec + ang_vel_diff

                neighbours_to_include = get_neighbour_databases(ira, idec, idist, idist_idx, min_d, max_d, min_ra, max_ra, min_dec, max_dec)

                # this is far from perfect, it just "boxes" in stars near the current, ie not a real distance check
                # but it's fast due to indexed database columns
                find_nearby_query = '''
                    SELECT source_id, ra, dec, parallax, pmra, pmdec, radial_velocity, distance, phot_g_mean_mag
                    FROM gaia
                    WHERE source_id IS NOT %d
                    AND distance > %f AND distance < %f
                    AND ra > %f AND ra < %f
                    AND dec > %f AND dec < %f
                    AND pmra > %f AND pmra < %f
                    AND pmdec > %f AND pmdec < %f''' % (
                        sid, min_d, max_d, min_ra, max_ra, min_dec,
                        max_dec, pmra_ang_vel_min, pmra_ang_vel_max,
                        pmdec_ang_vel_min, pmdec_ang_vel_max
                    )

                nearby_stars = c.execute(find_nearby_query).fetchall()

                for n in neighbours_to_include:
                    nconn = get_connection(n, stars_done)
                    nc = nconn.cursor()
                    nearby_stars.extend(nc.execute(find_nearby_query).fetchall())

                stars_done = stars_done + 1

                if len(nearby_stars) == 0:
                    continue

                # now we want to compare velocity direction and magnitude with each found nearby star
                # all proper motions are converted into rad/s and celestial velocity is converted to
                # cartesian vector with unit km/s
                pmra_rad_per_s = pmra * mas_per_yr_to_rad_per_s
                pmdec_rad_per_s = pmdec * mas_per_yr_to_rad_per_s
                vel = vec3_from_celestial(pmra_rad_per_s, pmdec_rad_per_s, vrad) # km/s
                speed = vec3_len(vel)
                vel_dir = vec3_scale(vel, 1/speed)
                nearby_stars_similar_velocity = []
                for ns in nearby_stars:
                    ns_pmra_rad_per_s = ns[i_pmra] * mas_per_yr_to_rad_per_s
                    ns_pmdec_rad_per_s = ns[i_pmdec] * mas_per_yr_to_rad_per_s
                    ns_vrad = ns[i_radial_velocity] #km/s
                    ns_vel = vec3_from_celestial(ns_pmra_rad_per_s, ns_pmdec_rad_per_s, ns_vrad) # km/s
                    ns_speed = vec3_len(ns_vel)
                    ns_vel_dir = vec3_scale(ns_vel, 1/ns_speed)
                    s_ns_dot = vec3_dot(ns_vel_dir, vel_dir)
                    s_ns_angle = math.acos(s_ns_dot)
                    
                    # only keep stars within velocity angle separation limit and below speed limit
                    if (s_ns_angle * rad_to_deg) < max_vel_angle_diff and math.fabs(ns_speed - speed) < max_vel_mag_diff:
                        nearby_stars_similar_velocity.append(ns)

                if len(nearby_stars_similar_velocity) == 0:
                    continue

                stars_in_group = set(nearby_stars_similar_velocity + [s])
                groups_to_combine = set()

                for s in stars_in_group:
                    sid = s[i_source_id]
                    group_idx = star_sid_to_comoving_group_idx.get(sid)

                    if group_idx != None:
                        groups_to_combine.add(group_idx)

                for group_idx in groups_to_combine:
                    g = comoving_groups[group_idx]
                    g["dead"] = True

                    for s in g["stars"]:
                        stars_in_group.add(s)
                        del star_sid_to_comoving_group_idx[s[i_source_id]]

                group_obj = {}
                group_obj["dead"] = False
                group_idx = len(comoving_groups)
                for s in stars_in_group:
                    group_obj["stars"] = list(stars_in_group)
                    group_obj["size"] = len(stars_in_group)
                    star_sid_to_comoving_group_idx[s[i_source_id]] = group_idx

                comoving_groups.append(group_obj)

                if debug_print_found:
                    print("Found comoving group of size %d" % len(stars_in_group))

comoving_groups_to_output = []

for g in comoving_groups:
    if g["dead"]:
        continue

    comoving_groups_to_output.append(g)

output_name = datetime.datetime.now().strftime("found-pairs-%Y-%m-%d-%H-%M-%S.txt")
file = open(output_name,"w")
file.write(str(comoving_groups_to_output))
file.close()