# Author: Karl Zylinski, Uppsala University

# Goes into sqlite3 databases of Gaia stars and finds comoving ones.
# Called from other scripts (such as find_comoving_stars_grid.py)
# The data is returned back to the calling script via the state variable
# passed to function find. See function init.

import sqlite3
import vec3
import conv
import math
import datetime
import db_connection_cache
import metadata

def init(db_folder, debug_print_found, max_sep,
         max_vel_mag_diff, get_neighbour_databases):
    metadata_dict = metadata.get(db_folder)
    state = {}
    state["db_folder"] = db_folder
    state["metadata"] = metadata_dict
    state["columns_to_fetch"] = ",".join(metadata_dict["columns"])
    state["debug_print_found"] = debug_print_found
    state["max_sep"] = max_sep
    state["max_vel_mag_diff"] = max_vel_mag_diff
    state["get_neighbour_databases"] = get_neighbour_databases
    state["stars_done"] = 0
    state["comoving_groups"] = [] # index is pair identifier, each entry is an array of stars
    state["star_sid_to_comoving_group_idx"] = {} # maps star source_id to comoving_groups index, for checking for redundancies

    if get_neighbour_databases == None:
        state["open_connections"] = None
    else:
        state["open_connections"] = {} # keeps track of database connections
    return state

def deinit(state):
    db_connection_cache.remove_all(state["open_connections"])

# 1. Finds stars with similar position and velocity as this one.
# 2. Also looks in neighbouring cells if close to cell wall.
# 3. A more precise 3D velocity comparsion is done, in addition to the
#    purley tangentaial done in the SQL selection.
# 4. For any found comoving star, this function is re-run, to find comoving
#    of the comoving.
def _find_comoving_to_star(star, database_cursor, state, in_current_group):
    max_sep = state["max_sep"]
    max_vel_mag_diff = state["max_vel_mag_diff"]
    get_neighbour_databases = state["get_neighbour_databases"]

    columns = state["metadata"]["columns"]
    i_source_id = columns.index("source_id")
    i_pmra = columns.index("pmra")
    i_pmra_error = columns.index("pmra_error")
    i_pmdec = columns.index("pmdec")
    i_pmdec_error = columns.index("pmdec_error")
    i_ra = columns.index("ra")
    i_ra_error = columns.index("ra_error")
    i_dec = columns.index("dec")
    i_dec_error = columns.index("dec_error")
    i_radial_velocity = columns.index("radial_velocity")
    i_radial_velocity_error = columns.index("radial_velocity_error")
    i_distance = columns.index("distance")
    i_distance_error = columns.index("distance")

    s = star
    sid = s[i_source_id]

    if state["star_sid_to_comoving_group_idx"].get(sid) != None:
        return []

    ra = s[i_ra] # deg
    dec = s[i_dec] # deg
    pmra = s[i_pmra] # mas/yr
    pmdec = s[i_pmdec] # mas/yr
    vrad = s[i_radial_velocity] # km/s

    pmra_error = s[i_pmra_error]
    pmdec_error = s[i_pmdec_error]
    radial_velocity_error = s[i_radial_velocity_error]

    diff_limit_km_per_year = max_vel_mag_diff / conv.sec_to_year
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
    ang_vel_diff = max_vel_mag_diff / (conv.parsec_to_km * d * conv.mas_per_yr_to_rad_per_s)

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

    # This is for gridded database, we might be near edge of cell but want to look in
    # neighbour cells. The provided get_neighbour_databases is assumed find those cells
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
    pmra_deg_per_year = pmra * conv.mas_to_deg
    pmdec_deg_per_year = pmdec * conv.mas_to_deg
    vrad_km_per_year = vrad / conv.sec_to_year
    vel_km_per_year = vec3.cartesian_velocity_from_celestial(ra, dec, d, pmra_deg_per_year, pmdec_deg_per_year, vrad_km_per_year) # km/s
    found_comoving_stars = []
    found_comoving_stars_sids = []
    found_comoving_stars_database_cursors = []
    for idx, mcs in enumerate(maybe_comoving_stars):
        mcs_ra = mcs[i_ra]
        mcs_dec = mcs[i_dec]
        mcs_d = mcs[i_distance]
        mcs_pmra_deg_per_year = mcs[i_pmra] * conv.mas_to_deg
        mcs_pmdec_deg_per_year = mcs[i_pmdec] * conv.mas_to_deg
        mcs_vrad_km_per_year = mcs[i_radial_velocity] / conv.sec_to_year #km/s
        mcs_vel_km_per_year = vec3.cartesian_velocity_from_celestial(mcs_ra, mcs_dec, mcs_d, mcs_pmra_deg_per_year, mcs_pmdec_deg_per_year, mcs_vrad_km_per_year) # km/s
        vel_vec_diff_km_per_year = vec3.sub(mcs_vel_km_per_year, vel_km_per_year)
        speed_km_per_year = vec3.len(vel_vec_diff_km_per_year) 
        
        # Only keep stars within velocity limit
        if speed_km_per_year < diff_limit_km_per_year:
            found_comoving_stars.append(mcs)
            found_comoving_stars_database_cursors.append(maybe_comoving_stars_database_cursors[idx])
            found_comoving_stars_sids.append(mcs[i_source_id])

    if len(found_comoving_stars) == 0:
        return []

    in_current_group.update(found_comoving_stars_sids)
    resulting_stars = found_comoving_stars.copy()

    # This recursively runs this function for the stars comoving to the
    # current one, to see if there are any comoving to that one
    for idx, fcs in enumerate(found_comoving_stars):
        cms_database_cursor = found_comoving_stars_database_cursors[idx]
        comoving_to_comoving = _find_comoving_to_star(fcs, cms_database_cursor, state, in_current_group)
        resulting_stars.extend(comoving_to_comoving)

    return resulting_stars

# Goes through a database and runs _find_comoving_to_star for all stars in it.
# Also adds the result of _find_comoving_to_star to the comoving_groups variable
# living in the state dictionary.
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

        comoving_group = _find_comoving_to_star(s, c, state, in_group)

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
    file.write("max_vel_mag_diff:%d\n" % state["max_vel_mag_diff"])
    file.write("groups:%s" % str(comoving_groups_to_output))
    file.close()

    print("Result saved to %s" % output_name)