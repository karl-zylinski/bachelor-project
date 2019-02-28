# Author: Karl Zylinski

# Goes into an sqlite3 database of Gaia stars and finds comoving ones.
# Called from other scripts (such as find_comoving_stars_grid.py)
# The data is returned back to the calling script via the state variable
# passed to function find. See function setup_state.

import sqlite3
import vec3
import conv
import math

def get_connection(db_name, state):
    open_connections = state["open_connections"]
    stars_done = state["stars_done"]
    existing = open_connections.get(db_name)

    if existing:
        existing["used_at"] = stars_done
        return existing["conn"]
    else:
        conn = sqlite3.connect(db_name)
        conn.execute('pragma mmap_size=%d;' % state["memory_map_size"])
        conn_obj = {}
        conn_obj["used_at"] = stars_done
        conn_obj["conn"] = conn
        open_connections[db_name] = conn_obj
        return conn

def remove_unused_connections(state):
    open_connections = state["open_connections"]
    stars_done = state["stars_done"]
    to_remove = []

    for db_name, c in open_connections.items():
        if stars_done - c["used_at"] > 100:
            c["conn"].close()
            to_remove.append(db_name)

    for r in to_remove:
        del open_connections[r]

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

def setup_state():
    state = {}
    state["stars_done"] = 0
    state["comoving_groups"] = [] # index is pair identifier, each entry is an array of stars
    state["star_sid_to_comoving_group_idx"] = {} # maps star source_id to comoving_groups index, for checking for redundancies
    state["open_connections"] = {} # keeps track of database connections
    state["memory_map_size"] = 10000000
    return state

def find(db_filename, state, debug_print_found,
                             max_sep, max_vel_angle_diff, max_vel_mag_diff,
                             get_neighbour_databases):

    if state["stars_done"] % 100 == 0:
        remove_unused_connections(state)

    comoving_groups = state["comoving_groups"]
    star_sid_to_comoving_group_idx = state["star_sid_to_comoving_group_idx"]
    conn = get_connection(db_filename, state)
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
        max_angular_sep = (max_sep*conv.rad_to_deg)/d
        min_ra = ra - max_angular_sep
        max_ra = ra + max_angular_sep
        min_dec = dec - max_angular_sep
        max_dec = dec + max_angular_sep

        # this is a mas/yr value that corresponds to angular value for tangential speed max_vel_mag_diff/2 for this star
        ang_vel_diff = (max_vel_mag_diff/2) / (conv.parsec_to_km * d * conv.mas_per_yr_to_rad_per_s)

        pmra_ang_vel_min = pmra - ang_vel_diff
        pmra_ang_vel_max = pmra + ang_vel_diff
        pmdec_ang_vel_min = pmdec - ang_vel_diff
        pmdec_ang_vel_max = pmdec + ang_vel_diff

        neighbours_to_include = []

        if get_neighbour_databases != None:
            neighbours_to_include = get_neighbour_databases(min_d, max_d, min_ra, max_ra, min_dec, max_dec)

        # this is far from perfect, it just "boxes" in stars near the current, ie not a real distance check
        # but it's fast due to indexed database columns
        find_nearby_query = '''
            SELECT %s
            FROM gaia
            WHERE source_id IS NOT %d
            AND distance > %f AND distance < %f
            AND ra > %f AND ra < %f
            AND dec > %f AND dec < %f
            AND pmra > %f AND pmra < %f
            AND pmdec > %f AND pmdec < %f''' % (
                columns_to_fetch,
                sid, min_d, max_d, min_ra, max_ra, min_dec,
                max_dec, pmra_ang_vel_min, pmra_ang_vel_max,
                pmdec_ang_vel_min, pmdec_ang_vel_max
            )

        nearby_stars = c.execute(find_nearby_query).fetchall()

        for n in neighbours_to_include:
            nconn = get_connection(n, state)
            nc = nconn.cursor()
            nearby_stars.extend(nc.execute(find_nearby_query).fetchall())

        state["stars_done"] = state["stars_done"] + 1

        if len(nearby_stars) == 0:
            continue

        # now we want to compare velocity direction and magnitude with each found nearby star
        # all proper motions are converted into rad/s and celestial velocity is converted to
        # cartesian vector with unit km/s
        pmra_rad_per_s = pmra * conv.mas_per_yr_to_rad_per_s
        pmdec_rad_per_s = pmdec * conv.mas_per_yr_to_rad_per_s
        vel = vec3.from_celestial(pmra_rad_per_s, pmdec_rad_per_s, vrad) # km/s
        speed = vec3.len(vel)
        vel_dir = vec3.scale(vel, 1/speed)
        nearby_stars_similar_velocity = []
        for ns in nearby_stars:
            ns_pmra_rad_per_s = ns[i_pmra] * conv.mas_per_yr_to_rad_per_s
            ns_pmdec_rad_per_s = ns[i_pmdec] * conv.mas_per_yr_to_rad_per_s
            ns_vrad = ns[i_radial_velocity] #km/s
            ns_vel = vec3.from_celestial(ns_pmra_rad_per_s, ns_pmdec_rad_per_s, ns_vrad) # km/s
            ns_speed = vec3.len(ns_vel)
            ns_vel_dir = vec3.scale(ns_vel, 1/ns_speed)
            s_ns_dot = vec3.dot(ns_vel_dir, vel_dir)
            s_ns_angle = math.acos(s_ns_dot)
            
            # only keep stars within velocity angle separation limit and below speed limit
            if (s_ns_angle * conv.rad_to_deg) < max_vel_angle_diff and math.fabs(ns_speed - speed) < max_vel_mag_diff:
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