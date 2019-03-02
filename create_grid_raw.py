# Author: Karl Zylinski, Uppsala University

# The purpose os of the file is to take gaia data and split it into segments.
# Stars with the same integer part of ra and dec are grouped into a segment,
# each segment is a list of cells where each cell has depth governed by cell_depth.

# Stars are written to .raw_db files, these are later, by other scripts,
# processed into .db files, one for each cell (i.e. each .db file  is associtaed
# with a unique comibination of (ra, dec, distance).

import time
import os
import datetime
import pickle
import utils_str
import utils_path
import sys
import math

cut_parallax_over_error = 10
cut_pmra_over_error = 10
cut_pmdec_over_error = 10
cut_radial_velocity_over_error = 10

disk_bouncing = False # DONT ENABLE, ITS BROKEN. Needed if we do full DR2
min_dist = 0 # pc
max_dist = 3000 # pc
cell_depth = 60 # pc
start_time = time.time()

def verify_arguments():
    if len(sys.argv) != 3:
        return False

    if type(sys.argv[1]) != str:
        return False

    if type(sys.argv[2]) != str:
        return False

    if not os.path.isdir(sys.argv[1]):
        print("%s does not exist" % sys.argv[1])
        return False

    if os.path.isdir(sys.argv[2]):
        print("%s already exist" % sys.argv[2])
        return False

    return True

assert verify_arguments(), "Usage: create_grid_raw.py source_dir dest_dir"

source_dir = sys.argv[1]
dest_dir = sys.argv[2]

source_columns = ["solution_id","designation","source_id","random_index","ref_epoch","ra","ra_error","dec","dec_error","parallax","parallax_error","parallax_over_error","pmra","pmra_error","pmdec","pmdec_error","ra_dec_corr","ra_parallax_corr","ra_pmra_corr","ra_pmdec_corr","dec_parallax_corr","dec_pmra_corr","dec_pmdec_corr","parallax_pmra_corr","parallax_pmdec_corr","pmra_pmdec_corr","astrometric_n_obs_al","astrometric_n_obs_ac","astrometric_n_good_obs_al","astrometric_n_bad_obs_al","astrometric_gof_al","astrometric_chi2_al","astrometric_excess_noise","astrometric_excess_noise_sig","astrometric_params_solved","astrometric_primary_flag","astrometric_weight_al","astrometric_pseudo_colour","astrometric_pseudo_colour_error","mean_varpi_factor_al","astrometric_matched_observations","visibility_periods_used","astrometric_sigma5d_max","frame_rotator_object_type","matched_observations","duplicated_source","phot_g_n_obs","phot_g_mean_flux","phot_g_mean_flux_error","phot_g_mean_flux_over_error","phot_g_mean_mag","phot_bp_n_obs","phot_bp_mean_flux","phot_bp_mean_flux_error","phot_bp_mean_flux_over_error","phot_bp_mean_mag","phot_rp_n_obs","phot_rp_mean_flux","phot_rp_mean_flux_error","phot_rp_mean_flux_over_error","phot_rp_mean_mag","phot_bp_rp_excess_factor","phot_proc_mode","bp_rp","bp_g","g_rp","radial_velocity","radial_velocity_error","rv_nb_transits","rv_template_teff","rv_template_logg","rv_template_fe_h","phot_variable_flag","l","b","ecl_lon","ecl_lat","priam_flags","teff_val","teff_percentile_lower","teff_percentile_upper","a_g_val","a_g_percentile_lower","a_g_percentile_upper","e_bp_min_rp_val","e_bp_min_rp_percentile_lower","e_bp_min_rp_percentile_upper","flame_flags","radius_val","radius_percentile_lower","radius_percentile_upper","lum_val","lum_percentile_lower","lum_percentile_upper"]
dest_columns = ["source_id","ref_epoch","ra","ra_error","dec","dec_error","parallax","parallax_error","pmra","pmra_error","pmdec","pmdec_error", "phot_g_mean_flux","phot_g_mean_flux_error","phot_g_mean_mag","phot_rp_mean_mag","phot_bp_mean_mag","radial_velocity","radial_velocity_error"]
dest_data_types = ["integer primary key","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real"]
dest_source_mapping = [0] * len(dest_columns)

assert not os.path.isdir(dest_dir), "Folder already exists: %s" % dest_dir
os.mkdir(dest_dir)

raw_dbs_folder = "%s/raw_dbs" % dest_dir
assert not os.path.isdir(raw_dbs_folder), "Folder already exists: %s" % raw_dbs_folder
os.mkdir(raw_dbs_folder)

for i, d in enumerate(dest_columns):
    dest_source_mapping[i] = source_columns.index(d)

assert(len(dest_columns) == len(dest_data_types))

# add extra columns not in gaia source
extra_columns = ["distance"]
extra_coumns_data_type = ["real"]

all_columns = dest_columns + extra_columns
all_columns_data_types = dest_data_types + extra_coumns_data_type

source_parallax_idx = source_columns.index("parallax")
source_parallax_over_error_idx = source_columns.index("parallax_over_error")
source_pmra_idx = source_columns.index("pmra")
source_pmra_error_idx = source_columns.index("pmra_error")
source_pmdec_idx = source_columns.index("pmdec")
source_pmdec_error_idx = source_columns.index("pmdec_error")
source_radial_velocity_idx = source_columns.index("radial_velocity")
source_radial_velocity_error_idx = source_columns.index("radial_velocity_error")

dest_parallax_idx = all_columns.index("parallax")
dest_dec_idx = all_columns.index("dec")
dest_ra_idx = all_columns.index("ra")
dest_distance_idx = all_columns.index("distance")

num_distance_cells = (max_dist - min_dist)//cell_depth
loaded_segments = {}

def get_segment_filename(segment_coord):
    return "%s/%d%+d.raw_db" % (raw_dbs_folder, segment_coord[0], segment_coord[1])

def unload_segment(segment_coord):
    segment = loaded_segments[segment_coord]
    segment_filename = get_segment_filename(segment_coord)
    segment_fh = open(segment_filename, 'wb')
    pickle.dump(segment, segment_fh)
    segment_fh.close()

def load_segment(segment_coord):
    if loaded_segments.get(segment_coord) != None:
        return

    segment_filename = get_segment_filename(segment_coord)

    if os.path.isfile(segment_filename):
        segment_fh = open(segment_filename, 'rb')
        loaded_segments[segment_coord] = pickle.load(segment_fh)
        segment_fh.close()
    else:
        loaded_segments[segment_coord] = []
        segment = loaded_segments[segment_coord]
        
        for dist_idx in range(0, num_distance_cells):
            segment.append([])

to_keep_loaded_radius = 10
def ensure_segment_loaded(segment_coord):
    if loaded_segments.get(segment_coord) != None:
        return

    load_segment(segment_coord)

    # Disk bouncing disabled, not needed for RV catalogue. Will be needed for complete
    # gaia catalogue. Needs repairs, see below.
    if (disk_bouncing == False):
        return

    cur_ra = segment_coord[0]
    cur_dec = segment_coord[1]

    min_allowed_ra = cur_ra - to_keep_loaded_radius
    max_allowed_ra = cur_ra + to_keep_loaded_radius
    if min_allowed_ra < 0:
        min_allowed_ra = 360 + min_allowed_ra
    elif max_allowed_ra > 360:
        max_allowed_ra = max_allowed_ra - 360

    # THIS IS BROKEN FIX SO IT DOES NOT USE 180 DEC AND FLIP RA WHEN DEC GOES OVER ZENITH OR NADIR
    min_allowed_dec = cur_dec - to_keep_loaded_radius
    max_allowed_dec = cur_dec + to_keep_loaded_radius
    #if min_allowed_dec < 180:
    #    min_allowed_dec = 180 + min_allowed_dec
    #elif max_allowed_dec > 180:
    #    max_allowed_dec = max_allowed_dec - 180

    for ls_coord in loaded_segments.keys():
        ls_ra = ls_coord[0]
        ls_dec = ls_coord[1]

        if((
            (min_allowed_ra < max_allowed_ra and ls_ra > min_allowed_ra and ls_ra < max_allowed_ra)
            or
            (min_allowed_ra > max_allowed_ra and (ls_ra > min_allowed_ra or ls_ra < max_allowed_ra))
        ) and (
            (min_allowed_dec < max_allowed_dec and ls_dec > min_allowed_dec and ls_dec < max_allowed_dec)
            or
            (min_allowed_dec > max_allowed_dec and (ls_dec > min_allowed_dec or ls_dec < max_allowed_dec)))
        ):
            continue

        unload_segment(ls_coord)

skipped_no_parallax = 0
skipped_cut_pmra = 0
skipped_cut_pmdec = 0
skipped_cut_radial_velocity = 0
skipped_cut_parallax = 0
total_counter = 0
file_counter = 0

def is_valid(source_values):
    global skipped_no_parallax
    global skipped_cut_pmra
    global skipped_cut_pmdec
    global skipped_cut_radial_velocity
    global skipped_cut_parallax

    # sanity
    if len(source_values) != len(source_columns):
        return False

    # skip those w/o parallax
    if (source_values[source_parallax_idx] == ""):
        skipped_no_parallax = skipped_no_parallax + 1
        return False

    # pmra error cut
    pmra_over_error = math.fabs(utils_str.to_float(source_values[source_pmra_idx]) / utils_str.to_float(source_values[source_pmra_error_idx]))
    if pmra_over_error < cut_pmra_over_error:
        skipped_cut_pmra = skipped_cut_pmra + 1
        return False

    # pmdec error cut
    pmdec_over_error = math.fabs(utils_str.to_float(source_values[source_pmdec_idx]) / utils_str.to_float(source_values[source_pmdec_error_idx]))
    if pmdec_over_error < cut_pmdec_over_error:
        skipped_cut_pmdec = skipped_cut_pmdec + 1
        return False

    # radial_velocity error cut
    radial_velocity_over_error = math.fabs(utils_str.to_float(source_values[source_radial_velocity_idx]) / utils_str.to_float(source_values[source_radial_velocity_error_idx]))
    if radial_velocity_over_error < cut_radial_velocity_over_error:
        skipped_cut_radial_velocity = skipped_cut_radial_velocity + 1
        return False

    # parallax error cut
    parallax_over_error = utils_str.to_float(source_values[source_parallax_over_error_idx])
    if parallax_over_error < cut_parallax_over_error:
        skipped_cut_parallax = skipped_cut_parallax + 1
        return False

    return True

def write_star(ra, dec, dist, data):
    ra_idx = int(ra)
    dec_idx = int(dec)
    dist_idx = int(distance/cell_depth)
    segment_coord = (ra_idx, dec_idx)
    ensure_segment_loaded(segment_coord)
    segment = loaded_segments[segment_coord]
    segment[dist_idx].append(data)

for file in os.listdir(source_dir):
    if not file.endswith(".csv"):
        continue

    csv_fh = open(utils_path.append(source_dir, file), "r")
    csv_lines = csv_fh.readlines()
    csv_fh.close()

    for i in range(1, len(csv_lines)): # skip header line
        csv_line = csv_lines[i]
        source_values = csv_line.split(",")

        if not is_valid(source_values):
            continue

        dest_values = [None] * len(all_columns)

        # throws in all columns that we take from Gaia as-is (compared to distance, calculated below)
        for ci in range(0, len(dest_columns)):
            val = source_values[dest_source_mapping[ci]]
            if val == "":
                dest_values[ci] = "NULL"
            else:
                dest_values[ci] = val

        # distance from parallax, parallax in mArcSec, hence conversion to ArcSec
        distance = 1.0/(float(dest_values[dest_parallax_idx])/1000.0)

        if distance < min_dist or distance > max_dist:
            continue

        dest_values[dest_distance_idx] = str(distance)

        ra = float(dest_values[dest_ra_idx])
        dec = float(dest_values[dest_dec_idx])

        write_star(ra, dec, distance, dest_values)
        total_counter = total_counter + 1
    
    file_counter = file_counter + 1
    print("Written to grid for csv: %s (%d files done, %d stars done)" % (file, file_counter, total_counter))

for ls in loaded_segments:
    unload_segment(ls)

# write metadata file
metadata_fh = open("%s/metadata" % dest_dir, "w")
metadata_fh.write("max_distance:%d\n" % max_dist)
metadata_fh.write("cell_depth:%d\n" % cell_depth)
metadata_fh.write("columns:%s\n" % str(all_columns))
metadata_fh.write("columns_datatypes:%s" % str(all_columns_data_types))
metadata_fh.close()

end_time = time.time()
dt = end_time - start_time
print("Imported %d stars to raw gid databases" % total_counter)
print("Skipped %d because they lacked parallax" % skipped_no_parallax)
print("Skipped %d because pmra over error was under %d" % (skipped_cut_pmra, cut_pmra_over_error))
print("Skipped %d because pmdec over error was under %d" % (skipped_cut_pmdec, cut_pmdec_over_error))
print("Skipped %d because radial_velocity over error was under %d" % (skipped_cut_radial_velocity, cut_radial_velocity_over_error))
print("Skipped %d because parallax over error was under %d" % (skipped_cut_parallax, cut_parallax_over_error))
print("Finished in " + str(int(dt)) + " seconds")