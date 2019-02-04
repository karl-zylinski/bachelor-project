import sqlite3
import time
import threading
import os

start_time = time.time()
dry_run = False
dry_run_print = True
db_name = "gaia_dr2.db"
source_dir = "gaia_bork/"
columns = ["solution_id","designation","source_id","random_index","ref_epoch","ra","ra_error","dec","dec_error","parallax","parallax_error","parallax_over_error","pmra","pmra_error","pmdec","pmdec_error","ra_dec_corr","ra_parallax_corr","ra_pmra_corr","ra_pmdec_corr","dec_parallax_corr","dec_pmra_corr","dec_pmdec_corr","parallax_pmra_corr","parallax_pmdec_corr","pmra_pmdec_corr","astrometric_n_obs_al","astrometric_n_obs_ac","astrometric_n_good_obs_al","astrometric_n_bad_obs_al","astrometric_gof_al","astrometric_chi2_al","astrometric_excess_noise","astrometric_excess_noise_sig","astrometric_params_solved","astrometric_primary_flag","astrometric_weight_al","astrometric_pseudo_colour","astrometric_pseudo_colour_error","mean_varpi_factor_al","astrometric_matched_observations","visibility_periods_used","astrometric_sigma5d_max","frame_rotator_object_type","matched_observations","duplicated_source","phot_g_n_obs","phot_g_mean_flux","phot_g_mean_flux_error","phot_g_mean_flux_over_error","phot_g_mean_mag","phot_bp_n_obs","phot_bp_mean_flux","phot_bp_mean_flux_error","phot_bp_mean_flux_over_error","phot_bp_mean_mag","phot_rp_n_obs","phot_rp_mean_flux","phot_rp_mean_flux_error","phot_rp_mean_flux_over_error","phot_rp_mean_mag","phot_bp_rp_excess_factor","phot_proc_mode","bp_rp","bp_g","g_rp","radial_velocity","radial_velocity_error","rv_nb_transits","rv_template_teff","rv_template_logg","rv_template_fe_h","phot_variable_flag","l","b","ecl_lon","ecl_lat","priam_flags","teff_val","teff_percentile_lower","teff_percentile_upper","a_g_val","a_g_percentile_lower","a_g_percentile_upper","e_bp_min_rp_val","e_bp_min_rp_percentile_lower","e_bp_min_rp_percentile_upper","flame_flags","radius_val","radius_percentile_lower","radius_percentile_upper","lum_val","lum_percentile_lower","lum_percentile_upper"]
data_types = ["integer","text","integer","integer","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","integer","integer","integer","integer","real","real","real","real","integer","integer","real","real","real","real","integer","integer","real","integer","integer","integer","integer","real","real","real","real","integer","real","real","real","real","integer","real","real","real","real","real","integer","real","real","real","real","real","integer","real","real","real","text","real","real","real","real","integer","real","real","real","real","real","real","real","real","real","integer","real","real","real","real","real","real"]
assert(len(columns) == len(data_types))
num_cols = len(columns)
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

def sql_exec(cmd):
    if dry_run == True:
        if dry_run_print:
            print(cmd)

        return

    cursor.execute(cmd)

create_table_columns = "solution_id integer, designation text, source_id integer primary key"

for i in range(3, len(columns)): # Skip 3 first since we have those above (due to primary key)
    col_title = columns[i]
    col_item = ","
    col_data_type = data_types[i]
    col_item += col_title + " " + col_data_type
    create_table_columns += col_item

sql_exec("CREATE TABLE gaia (" + create_table_columns + ")")

def import_file(file):
    csv_fh = open(source_dir + file, "r")
    csv_lines = csv_fh.readlines()
    csv_fh.close()
    insert_str = "INSERT INTO gaia (" + ",".join(columns) + ") VALUES"

    for i in range(1, len(csv_lines)): # skip header line
        csv_line = csv_lines[i]

        if (csv_line.count(",") + 1) != num_cols:
            print("In " + file + ": Skipping line " + str(i + 1) + ", not " + str(num_cols) + " cells long")
            continue

        values = csv_line.split(",")
        for i, val in enumerate(values):
            dt = data_types[i]

            if val[-1:] == "\n":
                val = val[:-1]
                values[i] = val

            if val == "":
                values[i] = "null"
            elif dt == "integer" and val == "true":
                values[i] = "1"
            elif dt == "integer" and val == "false":
                values[i] = "0"
            elif dt == "text":
                values[i] = "\"" + val + "\""

        insert_str += " (" + ",".join(values) + "),"

    insert_str = insert_str[:-1] # Remove last comma
    sql_exec(insert_str)
    conn.commit()
    print("Imported: " + file)

for file in os.listdir(source_dir):
    if not file.endswith(".csv"):
        continue

    import_file(file)

print("Creating indices")
sql_exec("CREATE INDEX index_ra ON gaia (ra)")
sql_exec("CREATE INDEX index_dec ON gaia (dec)")
sql_exec("CREATE INDEX index_parallax ON gaia (parallax)")
conn.close()
end_time = time.time()
dt = end_time - start_time
print("Finished in " + str(int(dt)) + " seconds")