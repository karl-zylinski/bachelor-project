import time
import os
import datetime
import pickle

min_dist = 0
max_dist = 3000
stars_per_raw_db_file = 500000
start_time = time.time()
db_folder = datetime.datetime.now().strftime("db_gaia_dr2_rv_%Y-%m-%d-%H-%M-%S")

source_dir = "gaia_source_rv/"
source_columns = ["solution_id","designation","source_id","random_index","ref_epoch","ra","ra_error","dec","dec_error","parallax","parallax_error","parallax_over_error","pmra","pmra_error","pmdec","pmdec_error","ra_dec_corr","ra_parallax_corr","ra_pmra_corr","ra_pmdec_corr","dec_parallax_corr","dec_pmra_corr","dec_pmdec_corr","parallax_pmra_corr","parallax_pmdec_corr","pmra_pmdec_corr","astrometric_n_obs_al","astrometric_n_obs_ac","astrometric_n_good_obs_al","astrometric_n_bad_obs_al","astrometric_gof_al","astrometric_chi2_al","astrometric_excess_noise","astrometric_excess_noise_sig","astrometric_params_solved","astrometric_primary_flag","astrometric_weight_al","astrometric_pseudo_colour","astrometric_pseudo_colour_error","mean_varpi_factor_al","astrometric_matched_observations","visibility_periods_used","astrometric_sigma5d_max","frame_rotator_object_type","matched_observations","duplicated_source","phot_g_n_obs","phot_g_mean_flux","phot_g_mean_flux_error","phot_g_mean_flux_over_error","phot_g_mean_mag","phot_bp_n_obs","phot_bp_mean_flux","phot_bp_mean_flux_error","phot_bp_mean_flux_over_error","phot_bp_mean_mag","phot_rp_n_obs","phot_rp_mean_flux","phot_rp_mean_flux_error","phot_rp_mean_flux_over_error","phot_rp_mean_mag","phot_bp_rp_excess_factor","phot_proc_mode","bp_rp","bp_g","g_rp","radial_velocity","radial_velocity_error","rv_nb_transits","rv_template_teff","rv_template_logg","rv_template_fe_h","phot_variable_flag","l","b","ecl_lon","ecl_lat","priam_flags","teff_val","teff_percentile_lower","teff_percentile_upper","a_g_val","a_g_percentile_lower","a_g_percentile_upper","e_bp_min_rp_val","e_bp_min_rp_percentile_lower","e_bp_min_rp_percentile_upper","flame_flags","radius_val","radius_percentile_lower","radius_percentile_upper","lum_val","lum_percentile_lower","lum_percentile_upper"]
dest_columns = ["source_id","ref_epoch","ra","ra_error","dec","dec_error","parallax","parallax_error","pmra","pmra_error","pmdec","pmdec_error", "phot_g_mean_flux","phot_g_mean_flux_error","phot_g_mean_mag","phot_rp_mean_mag","phot_bp_mean_mag","radial_velocity","radial_velocity_error"]
dest_data_types = ["integer primary key","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real"]
dest_source_mapping = [0] * len(dest_columns)
dest_parallax_idx = dest_columns.index("parallax")

def error(msg):
    print(msg)
    exit(1)

if os.path.isdir(db_folder):
    error("Folder already exists: %s" % db_folder)

os.mkdir(db_folder)

for i, d in enumerate(dest_columns):
    dest_source_mapping[i] = source_columns.index(d)

assert(len(dest_columns) == len(dest_data_types))

def sql_exec(cmd):
    if dry_run_print:
        print(cmd)

    if dry_run:
        return

    conn.execute(cmd)

# add extra columns not in gaia source
extra_columns = ["distance"]
extra_coumns_data_type = ["real"]
distance_col_idx = len(dest_columns)

all_columns = dest_columns + extra_columns
all_columns_data_types = dest_data_types + extra_coumns_data_type

columns_fh = open("%s/columns" % db_folder, "w")
columns_fh.write(str(all_columns))
columns_fh.close()

columns_dt_fh = open("%s/columns_data_types" % db_folder, "w")
columns_dt_fh.write(str(all_columns_data_types))
columns_dt_fh.close()

i_dec = all_columns.index("dec")
i_ra = all_columns.index("ra")
i_distance = all_columns.index("distance")

num_distance_cells = max_dist - min_dist
num_ra_cells = 360
num_dec_cells = 180

grid = {}

stars_in_cur_raw_db = 0
raw_db_num = 0
def write_star(idec_180, ira, idist, data):
    global stars_in_cur_raw_db
    global raw_db_num
    global grid

    cell_id = "%d-%d-%d" % (idec_180, ira, idist)
    cell = grid.get(cell_id)

    if cell == None:
        cell = []
        grid[cell_id] = cell

    stars_in_cur_raw_db = stars_in_cur_raw_db + 1
    cell.append(data)

    if stars_in_cur_raw_db > stars_per_raw_db_file:
        raw_db_name = "%s/raw_db_%d.raw_db" % (db_folder, raw_db_num)
        print("Saving raw database %d to %s" % (raw_db_num, raw_db_name))
        f = open(raw_db_name, 'wb')
        pickle.dump(grid, f)
        f.close()
        grid = {}
        raw_db_num = raw_db_num + 1
        stars_in_cur_raw_db = 0

invalid_lines = 0
no_parallax_skipped = 0
total_counter = 0
file_counter = 0
for file in os.listdir(source_dir):
    if not file.endswith(".csv"):
        continue

    csv_fh = open(source_dir + file, "r")
    csv_lines = csv_fh.readlines()
    csv_fh.close()

    for i in range(1, len(csv_lines)): # skip header line
        csv_line = csv_lines[i]

        # sanity check
        if (csv_line.count(",") + 1) != len(source_columns):
            invalid_lines = invalid_lines + 1
            print("In " + file + ": Skipping line " + str(i + 1) + ", not " + str(len(source_columns)) + " cells long")
            continue

        values = csv_line.split(",")

        # skip those w/o parallax
        if (values[dest_source_mapping[dest_parallax_idx]] == ""):
            no_parallax_skipped = no_parallax_skipped + 1
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

        ra = float(dest_values[i_ra])
        dec = float(dest_values[i_dec])

        ira = int(ra)
        idec_180 = int(dec + 90) # gonna use as index, must be in 0 -  180 range
        idist = int(distance)

        write_star(idec_180, ira, idist, dest_values)
        total_counter = total_counter + 1
    
    file_counter = file_counter + 1
    print("Written to grid for csv: %s (%d files done, %d stars done)" % (file, file_counter, total_counter))

end_time = time.time()
dt = end_time - start_time
print("Imported %d stars to raw cell table" % total_counter)
print("Skipped %d because they lacked parallax" % no_parallax_skipped)
print("Skipped %d because csv line was of wrong length (%d)" % (invalid_lines, len(source_columns)))
print("Finished in " + str(int(dt)) + " seconds")