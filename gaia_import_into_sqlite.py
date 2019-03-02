# Author: Karl Zylinski, Uppsala University

# Dumps Gaia source data into a single db. Not really used,
# instead look at the creat_grid* scripts

import sqlite3
import time
import threading
import os
import datetime
import math
import utils_str

cut_parallax_over_error = 10
cut_pmra_over_error = 10
cut_pmdec_over_error = 10
cut_radial_velocity_over_error = 10
min_dist = 0 # pc
max_dist = 3000 # pc

start_time = time.time()
dry_run = False
dry_run_print = False
db_name = datetime.datetime.now().strftime("gaia_dr2_rv_%Y-%m-%d-%H-%M-%S.db")
source_dir = "gaia_source_rv/"
source_columns = ["solution_id","designation","source_id","random_index","ref_epoch","ra","ra_error","dec","dec_error","parallax","parallax_error","parallax_over_error","pmra","pmra_error","pmdec","pmdec_error","ra_dec_corr","ra_parallax_corr","ra_pmra_corr","ra_pmdec_corr","dec_parallax_corr","dec_pmra_corr","dec_pmdec_corr","parallax_pmra_corr","parallax_pmdec_corr","pmra_pmdec_corr","astrometric_n_obs_al","astrometric_n_obs_ac","astrometric_n_good_obs_al","astrometric_n_bad_obs_al","astrometric_gof_al","astrometric_chi2_al","astrometric_excess_noise","astrometric_excess_noise_sig","astrometric_params_solved","astrometric_primary_flag","astrometric_weight_al","astrometric_pseudo_colour","astrometric_pseudo_colour_error","mean_varpi_factor_al","astrometric_matched_observations","visibility_periods_used","astrometric_sigma5d_max","frame_rotator_object_type","matched_observations","duplicated_source","phot_g_n_obs","phot_g_mean_flux","phot_g_mean_flux_error","phot_g_mean_flux_over_error","phot_g_mean_mag","phot_bp_n_obs","phot_bp_mean_flux","phot_bp_mean_flux_error","phot_bp_mean_flux_over_error","phot_bp_mean_mag","phot_rp_n_obs","phot_rp_mean_flux","phot_rp_mean_flux_error","phot_rp_mean_flux_over_error","phot_rp_mean_mag","phot_bp_rp_excess_factor","phot_proc_mode","bp_rp","bp_g","g_rp","radial_velocity","radial_velocity_error","rv_nb_transits","rv_template_teff","rv_template_logg","rv_template_fe_h","phot_variable_flag","l","b","ecl_lon","ecl_lat","priam_flags","teff_val","teff_percentile_lower","teff_percentile_upper","a_g_val","a_g_percentile_lower","a_g_percentile_upper","e_bp_min_rp_val","e_bp_min_rp_percentile_lower","e_bp_min_rp_percentile_upper","flame_flags","radius_val","radius_percentile_lower","radius_percentile_upper","lum_val","lum_percentile_lower","lum_percentile_upper"]
dest_columns = ["source_id","ref_epoch","ra","ra_error","dec","dec_error","parallax","parallax_error","pmra","pmra_error","pmdec","pmdec_error", "phot_g_mean_flux","phot_g_mean_flux_error","phot_g_mean_mag","phot_rp_mean_mag","phot_bp_mean_mag","radial_velocity","radial_velocity_error", "teff_val"]
dest_data_types = ["integer primary key","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real"]
dest_source_mapping = [0] * len(dest_columns)
dest_parallax_idx = dest_columns.index("parallax")

for i, d in enumerate(dest_columns):
    dest_source_mapping[i] = source_columns.index(d)

assert(len(dest_columns) == len(dest_data_types))
conn = sqlite3.connect(db_name)
conn.execute('pragma mmap_size=8589934592;')

def sql_exec(cmd):
    if dry_run_print:
        print(cmd)

    if dry_run:
        return

    conn.execute(cmd)

create_table_columns = ""

for i in range(0, len(dest_columns)):
    col_title = dest_columns[i]
    col_data_type = dest_data_types[i]
    create_table_columns += col_title + " " + col_data_type + ","

# add extra columns not in gaia source
extra_columns = ["distance"]
extra_coumns_data_type = ["real"]
distance_col_idx = len(dest_columns)

for i in range(0, len(extra_columns)):
    col_title = extra_columns[i]
    col_data_type = extra_coumns_data_type[i]
    create_table_columns += col_title + " " + col_data_type + ","

all_columns = dest_columns + extra_columns
all_columns_text = ",".join(all_columns)

create_table_columns = create_table_columns[:-1]
sql_exec("CREATE TABLE gaia (" + create_table_columns + ")")

source_parallax_idx = source_columns.index("parallax")
source_parallax_over_error_idx = source_columns.index("parallax_over_error")
source_pmra_idx = source_columns.index("pmra")
source_pmra_error_idx = source_columns.index("pmra_error")
source_pmdec_idx = source_columns.index("pmdec")
source_pmdec_error_idx = source_columns.index("pmdec_error")
source_radial_velocity_idx = source_columns.index("radial_velocity")
source_radial_velocity_error_idx = source_columns.index("radial_velocity_error")

skipped_no_parallax = 0
skipped_cut_pmra = 0
skipped_cut_pmdec = 0
skipped_cut_radial_velocity = 0
skipped_cut_parallax = 0
total_counter = 0
invalid_lines = 0
commit_counter = 0
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

def import_file(file):
    global commit_counter
    global invalid_lines
    global total_counter
    global file_counter
    csv_fh = open(source_dir + file, "r")
    csv_lines = csv_fh.readlines()
    csv_fh.close()
    for i in range(1, len(csv_lines)): # skip header line
        csv_line = csv_lines[i]
        values = csv_line.split(",")

        if not is_valid(values):
            continue

        dest_values = [None] * len(all_columns)

        # throws in all columns that we take from Gaia as-is (compared to distance, calculated below)
        for ci in range(0, len(dest_columns)):
            val = values[dest_source_mapping[ci]]
            if val == "":
                dest_values[ci] = "NULL"
            else:
                dest_values[ci] = val

        # distance from parallax, parallax in mArcSec, hence conversion to ArcSec
        distance = 1.0/(float(dest_values[dest_parallax_idx])/1000.0)
        
        if distance < min_dist or distance > max_dist:
            continue

        dest_values[distance_col_idx] = str(distance)
        insert_str = "INSERT INTO gaia (" + all_columns_text + ") VALUES (" + ",".join(dest_values) + ")"
        sql_exec(insert_str)
        total_counter = total_counter + 1
        commit_counter = commit_counter + 1

    # relaxes harddrive
    if commit_counter > 100000:
        commit_counter = 0
        conn.commit()

    file_counter = file_counter + 1
    print("Imported: %s (%d files done, %d stars done)" % (file, file_counter, total_counter))

conn.commit()

for file in os.listdir(source_dir):
    if not file.endswith(".csv"):
        continue

    import_file(file)

print("Creating index on ra")
sql_exec("CREATE INDEX index_ra ON gaia (ra)")
print("Creating index on dec")
sql_exec("CREATE INDEX index_dec ON gaia (dec)")
print("Creating index on parallax")
sql_exec("CREATE INDEX index_parallax ON gaia (parallax)")
print("Creating index on pmra")
sql_exec("CREATE INDEX index_pmra ON gaia (pmra)")
print("Creating index on pmdec")
sql_exec("CREATE INDEX index_pmdec ON gaia (pmdec)")
print("Creating index on radial_velocity")
sql_exec("CREATE INDEX index_radial_velocity ON gaia (radial_velocity)")
print("Creating index on distance")
sql_exec("CREATE INDEX index_distance ON gaia (distance)")
conn.commit()
conn.close()
end_time = time.time()
dt = end_time - start_time
print()
print("Imported %d stars" % total_counter)
print("Skipped %d because they lacked parallax" % skipped_no_parallax)
print("Skipped %d because pmra over error was under %d" % (skipped_cut_pmra, cut_pmra_over_error))
print("Skipped %d because pmdec over error was under %d" % (skipped_cut_pmdec, cut_pmdec_over_error))
print("Skipped %d because radial_velocity over error was under %d" % (skipped_cut_radial_velocity, cut_radial_velocity_over_error))
print("Skipped %d because parallax over error was under %d" % (skipped_cut_parallax, cut_parallax_over_error))
print("Finished in " + str(int(dt)) + " seconds")