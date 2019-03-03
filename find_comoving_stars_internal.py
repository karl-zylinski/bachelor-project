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

# The two following functions does some magical db connection
# cache where a connection that hasn't been used in like 100 star lookups
# is thrown away. It is useful for the gridded lookup so db connections aren't
# thrown out and then re-opened right after.
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

def remove_all_connections(state):
    open_connections = state["open_connections"]

    for db_name, c in open_connections.items():
        c["conn"].close()

    state["open_connections"] = []

source_columns = ["solution_id","designation","source_id","random_index","ref_epoch","ra","ra_error","dec","dec_error","parallax","parallax_error","parallax_over_error","pmra","pmra_error","pmdec","pmdec_error","ra_dec_corr","ra_parallax_corr","ra_pmra_corr","ra_pmdec_corr","dec_parallax_corr","dec_pmra_corr","dec_pmdec_corr","parallax_pmra_corr","parallax_pmdec_corr","pmra_pmdec_corr","astrometric_n_obs_al","astrometric_n_obs_ac","astrometric_n_good_obs_al","astrometric_n_bad_obs_al","astrometric_gof_al","astrometric_chi2_al","astrometric_excess_noise","astrometric_excess_noise_sig","astrometric_params_solved","astrometric_primary_flag","astrometric_weight_al","astrometric_pseudo_colour","astrometric_pseudo_colour_error","mean_varpi_factor_al","astrometric_matched_observations","visibility_periods_used","astrometric_sigma5d_max","frame_rotator_object_type","matched_observations","duplicated_source","phot_g_n_obs","phot_g_mean_flux","phot_g_mean_flux_error","phot_g_mean_flux_over_error","phot_g_mean_mag","phot_bp_n_obs","phot_bp_mean_flux","phot_bp_mean_flux_error","phot_bp_mean_flux_over_error","phot_bp_mean_mag","phot_rp_n_obs","phot_rp_mean_flux","phot_rp_mean_flux_error","phot_rp_mean_flux_over_error","phot_rp_mean_mag","phot_bp_rp_excess_factor","phot_proc_mode","bp_rp","bp_g","g_rp","radial_velocity","radial_velocity_error","rv_nb_transits","rv_template_teff","rv_template_logg","rv_template_fe_h","phot_variable_flag","l","b","ecl_lon","ecl_lat","priam_flags","teff_val","teff_percentile_lower","teff_percentile_upper","a_g_val","a_g_percentile_lower","a_g_percentile_upper","e_bp_min_rp_val","e_bp_min_rp_percentile_lower","e_bp_min_rp_percentile_upper","flame_flags","radius_val","radius_percentile_lower","radius_percentile_upper","lum_val","lum_percentile_lower","lum_percentile_upper"]
columns = source_columns + ["distance"]
columns_to_fetch = ",".join(columns)

# Used to fetch stuff from sql result arrays
i_source_id = columns.index("source_id")
i_ra = columns.index("ra")
i_dec = columns.index("dec")
i_parallax = columns.index("parallax")
i_pmra = columns.index("pmra")
i_pmdec = columns.index("pmdec")
i_radial_velocity = columns.index("radial_velocity")
i_distance = columns.index("distance")

def init():
    state = {}
    state["stars_done"] = 0
    state["comoving_groups"] = [] # index is pair identifier, each entry is an array of stars
    state["star_sid_to_comoving_group_idx"] = {} # maps star source_id to comoving_groups index, for checking for redundancies
    state["open_connections"] = {} # keeps track of database connections
    state["memory_map_size"] = 10000000
    return state

def deinit(state):
    remove_all_connections(state)

def find(db_filename, state, debug_print_found,
                             max_sep, max_vel_angle_diff, max_vel_mag_diff,
                             get_neighbour_databases):
    # 100 is 100% arbitrary
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

        # Boxes in stars near current, with similar proper motion. The complete motion
        # is then compared further down.
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

        maybe_comoving_star = c.execute(find_nearby_query).fetchall()

        for n in neighbours_to_include:
            nconn = get_connection(n, state)
            nc = nconn.cursor()
            maybe_comoving_star.extend(nc.execute(find_nearby_query).fetchall())

        state["stars_done"] = state["stars_done"] + 1

        if len(maybe_comoving_star) == 0:
            continue

        # Now we want to compare velocity direction and magnitude with each found nearby star
        # all proper motions are converted into rad/s and celestial velocity is converted to
        # cartesian vector with unit km/s.
        pmra_rad_per_s = pmra * conv.mas_per_yr_to_rad_per_s
        pmdec_rad_per_s = pmdec * conv.mas_per_yr_to_rad_per_s
        vel = vec3.from_celestial(pmra_rad_per_s, pmdec_rad_per_s, vrad) # km/s
        speed = vec3.len(vel)
        vel_dir = vec3.scale(vel, 1/speed)
        found_comoving_stars = []
        for mcs in maybe_comoving_star:
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

        if len(found_comoving_stars) == 0:
            continue

        comoving_group = set(found_comoving_stars + [s])

        # This part looks if any of the stars found are present
        # in comoving groups found previously, if so, a merge of the
        # groups is done by deleting the old groups and then making
        # one big group of them all.
        groups_to_combine = set()

        for s in comoving_group:
            sid = s[i_source_id]
            group_idx = star_sid_to_comoving_group_idx.get(sid)

            if group_idx != None:
                groups_to_combine.add(group_idx)

        for group_idx in groups_to_combine:
            g = comoving_groups[group_idx]
            g["dead"] = True

            for s in g["stars"]:
                comoving_group.add(s)
                del star_sid_to_comoving_group_idx[s[i_source_id]]

            del g["stars"]

        group_obj = {}
        group_obj["dead"] = False
        group_idx = len(comoving_groups)
        for s in comoving_group:
            group_obj["stars"] = list(comoving_group)
            group_obj["size"] = len(comoving_group)
            star_sid_to_comoving_group_idx[s[i_source_id]] = group_idx

        comoving_groups.append(group_obj)

        if debug_print_found:
            print("Found comoving group of size %d" % len(comoving_group))

def save_result(state):
    comoving_groups_to_output = []
    comoving_groups = state["comoving_groups"]
    group_id = 0 # only unique inside each comoving-groups file
    for g in comoving_groups:
        if g["dead"]:
            continue

        del g["dead"]
        g["id"] = group_id
        comoving_groups_to_output.append(g)
        group_id = group_id + 1

    output_name = datetime.datetime.now().strftime("comoving-groups-%Y-%m-%d-%H-%M-%S.txt")
    file = open(output_name,"w")
    file.write(str(comoving_groups_to_output))
    file.close()

    print("Result saved to %s" % output_name)