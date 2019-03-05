# Author: Karl Zylinski

# Goes into an sqlite3 database of Gaia stars and finds comoving ones.
# Called from other scripts (such as find_comoving_stars_grid.py)
# The data is returned back to the calling script via the state variable
# passed to function find. See function setup_state.

import sqlite3
import vec3
import conv
import math
import datetime
import db_connection_cache
import metadata

def init(db_folder, debug_print_found, max_sep, max_vel_angle_diff,
         max_vel_mag_diff, get_neighbour_databases):
    metadata_dict = metadata.get(db_folder)
    state = {}
    state["db_folder"] = db_folder
    state["metadata"] = metadata_dict
    state["columns_to_fetch"] = ",".join(metadata_dict["columns"])
    state["debug_print_found"] = debug_print_found
    state["max_sep"] = max_sep
    state["max_vel_angle_diff"] = max_vel_angle_diff
    state["max_vel_mag_diff"] = max_vel_mag_diff
    state["get_neighbour_databases"] = get_neighbour_databases
    state["stars_done"] = 0
    state["comoving_groups"] = [] # index is pair identifier, each entry is an array of stars
    state["star_sid_to_comoving_group_idx"] = {} # maps star source_id to comoving_groups index, for checking for redundancies
    state["open_connections"] = {} # keeps track of database connections
    return state

def deinit(state):
    db_connection_cache.remove_all(state["open_connections"])

def find_comoving_to_star(star, database_cursor, state, in_current_group):
    max_sep = state["max_sep"]
    max_vel_angle_diff = state["max_vel_angle_diff"]
    max_vel_mag_diff = state["max_vel_mag_diff"]
    get_neighbour_databases = state["get_neighbour_databases"]

    columns = state["metadata"]["columns"]
    i_source_id = columns.index("source_id")
    i_pmra = columns.index("pmra")
    i_pmdec = columns.index("pmdec")
    i_ra = columns.index("ra")
    i_dec = columns.index("dec")
    i_radial_velocity = columns.index("radial_velocity")
    i_distance = columns.index("distance")

    s = star
    sid = s[i_source_id]

    if state["star_sid_to_comoving_group_idx"].get(sid) != None:
        return []

    ra = s[i_ra] # deg
    dec = s[i_dec] # deg
    pmra = s[i_pmra] # mas/yr
    pmdec = s[i_pmra] # mas/yr
    vrad = s[i_radial_velocity] # km/s
    d = s[i_distance] # distance in pc
    cell_depth = state["metadata"]["cell_depth"]
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

    where = "WHERE"

    for idx, group_sid in enumerate(in_current_group):
        if idx == 0:
            where = where + " source_id IS NOT %d" % group_sid
        else:
            where = where + " AND source_id IS NOT %d" % group_sid

    # Boxes in stars near current, with similar proper motion. The complete motion
    # is then compared further down.
    find_nearby_query = '''
        SELECT %s
        FROM gaia
        %s
        AND distance > %f AND distance < %f
        AND ra > %f AND ra < %f
        AND dec > %f AND dec < %f
        AND pmra > %f AND pmra < %f
        AND pmdec > %f AND pmdec < %f''' % (
            state["columns_to_fetch"], where,
            min_d, max_d, min_ra, max_ra, min_dec,
            max_dec, pmra_ang_vel_min, pmra_ang_vel_max,
            pmdec_ang_vel_min, pmdec_ang_vel_max
        )

    maybe_comoving_stars = database_cursor.execute(find_nearby_query).fetchall()
    maybe_comoving_stars_database_cursors = [database_cursor] * len(maybe_comoving_stars)

    neighbour_cells_to_include = []
    if get_neighbour_databases != None:
        neighbour_cells_to_include = get_neighbour_databases(ra, dec, d, cell_depth, min_d, max_d, min_ra, max_ra, min_dec, max_dec)

    for n in neighbour_cells_to_include:
        nconn = db_connection_cache.get(n, state["open_connections"])
        nc = nconn.cursor()
        to_add = nc.execute(find_nearby_query).fetchall()
        maybe_comoving_stars.extend(to_add)
        maybe_comoving_stars_database_cursors.extend([nc] * len(to_add))

    if len(maybe_comoving_stars) == 0:
        return []

    # Now we want to compare velocity direction and magnitude with each found nearby star
    # all proper motions are converted into rad/s and celestial velocity is converted to
    # cartesian vector with unit km/s.
    pmra_rad_per_s = pmra * conv.mas_per_yr_to_rad_per_s
    pmdec_rad_per_s = pmdec * conv.mas_per_yr_to_rad_per_s
    vel = vec3.from_celestial(pmra_rad_per_s, pmdec_rad_per_s, vrad) # km/s
    speed = vec3.len(vel)
    vel_dir = vec3.scale(vel, 1/speed)
    found_comoving_stars = []
    found_comoving_stars_sids = []
    found_comoving_stars_database_cursors = []
    for idx, mcs in enumerate(maybe_comoving_stars):
        mcs_pmra_rad_per_s = mcs[i_pmra] * conv.mas_per_yr_to_rad_per_s
        mcs_pmdec_rad_per_s = mcs[i_pmdec] * conv.mas_per_yr_to_rad_per_s
        mcs_vrad = mcs[i_radial_velocity] #km/s
        mcs_vel = vec3.from_celestial(mcs_pmra_rad_per_s, mcs_pmdec_rad_per_s, mcs_vrad) # km/s
        mcs_speed = vec3.len(mcs_vel)
        mcs_vel_dir = vec3.scale(mcs_vel, 1/mcs_speed)
        s_mcs_dot = vec3.dot(mcs_vel_dir, vel_dir)
        s_mcs_angle = math.acos(s_mcs_dot)
        
        # Only keep stars within velocity angle separation limit and below speed limit.
        if (s_mcs_angle * conv.rad_to_deg) < max_vel_angle_diff and math.fabs(mcs_speed - speed) < max_vel_mag_diff:
            found_comoving_stars.append(mcs)
            found_comoving_stars_database_cursors.append(maybe_comoving_stars_database_cursors[idx])
            found_comoving_stars_sids.append(mcs[i_source_id])

    if len(found_comoving_stars) == 0:
        return []

    in_current_group.update(found_comoving_stars_sids)
    resulting_stars = found_comoving_stars.copy()
    for idx, fcs in enumerate(found_comoving_stars):
        cms_database_cursor = found_comoving_stars_database_cursors[idx]
        comoving_to_comoving = find_comoving_to_star(fcs, cms_database_cursor, state, in_current_group)
        resulting_stars.extend(comoving_to_comoving)

    return resulting_stars

def find(db_filename, state):
    db_connection_cache.remove_unused(state["open_connections"])
    columns = state["metadata"]["columns"]
    i_source_id = columns.index("source_id")
    comoving_groups = state["comoving_groups"]
    star_sid_to_comoving_group_idx = state["star_sid_to_comoving_group_idx"]
    conn = db_connection_cache.get(db_filename, state["open_connections"])
    c = conn.cursor()
    all_stars_select_str = "SELECT %s FROM gaia" % state["columns_to_fetch"]
    all_stars = c.execute(all_stars_select_str).fetchall()

    for s in all_stars:
        if star_sid_to_comoving_group_idx.get(s[i_source_id]) != None: # Already processed
            continue

        in_group = set()
        in_group.add(s[i_source_id])

        comoving_group = find_comoving_to_star(s, c, state, in_group)

        if len(comoving_group) == 0:
            continue

        comoving_group.append(s)
        group_idx = len(comoving_groups)
        group_obj= {}
        for s in comoving_group:
            group_obj["stars"] = list(comoving_group)
            group_obj["size"] = len(comoving_group)
            star_sid_to_comoving_group_idx[s[i_source_id]] = group_idx

        comoving_groups.append(group_obj)

        if state["debug_print_found"]:
            print("Found comoving group of size %d" % len(comoving_group))

def save_result(state):
    metadata = state["metadata"]
    comoving_groups_to_output = []
    comoving_groups = state["comoving_groups"]
    group_id = 0 # only unique inside each comoving-groups file
    for g in comoving_groups:
        g["id"] = group_id
        comoving_groups_to_output.append(g)
        group_id = group_id + 1

    output_name = datetime.datetime.now().strftime("comoving-groups-%Y-%m-%d-%H-%M-%S.txt")
    file = open(output_name,"w")

    for k,v in metadata.items():
        file.write("%s:%s\n" % (k, str(v)))

    file.write("max_sep:%d\n" % state["max_sep"])
    file.write("max_vel_angle_diff:%d\n" % state["max_vel_angle_diff"])
    file.write("max_vel_mag_diff:%d\n" % state["max_vel_mag_diff"])
    file.write("groups:%s" % str(comoving_groups_to_output))
    file.close()

    print("Result saved to %s" % output_name)