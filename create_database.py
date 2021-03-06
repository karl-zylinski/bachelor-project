# Author: Karl Zylinski, Uppsala University

# Takes Gaia data and split it into cells.

# Each cell is given by x-y-z coordainates, which are created using
# the function cartesian_position_from_celestial in file vec3.py

# The resulting database can then be used to do quick lookups,
# see find_comoving_groups.py

import time
import os
import datetime
import utils_str
import utils_path
import sys
import math
import gaia_columns
import db_connection_cache
import vec3
import conv

cut_pmra_over_error = 10
cut_pmdec_over_error = 10
cut_radial_velocity_over_error = 10

max_dist_pc = 3000
cell_size_pc = 60
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

assert not os.path.isdir(dest_dir), "Folder already exists: %s" % dest_dir
os.mkdir(dest_dir)

assert(len(gaia_columns.columns) == len(gaia_columns.data_types))

# add extra columns not in gaia source
extra_columns = ["distance", "distance_error", "x", "y", "z", "vx", "vy", "vz"]
extra_coumns_data_type = ["real", "real", "real", "real", "real", "real", "real", "real"]

all_columns = gaia_columns.columns + extra_columns
all_columns_data_types = gaia_columns.data_types + extra_coumns_data_type

# write metadata file
metadata_fh = open("%s/metadata" % dest_dir, "w")
metadata_fh.write("cut_pmra_over_error:%d\n" % cut_pmra_over_error)
metadata_fh.write("cut_pmdec_over_error:%d\n" % cut_pmdec_over_error)
metadata_fh.write("cut_radial_velocity_over_error:%d\n" % cut_radial_velocity_over_error)
metadata_fh.write("max_distance:%d\n" % max_dist_pc)
metadata_fh.write("cell_size:%d\n" % cell_size_pc)
metadata_fh.write("columns:%s\n" % str(all_columns))
metadata_fh.write("columns_datatypes:%s" % str(all_columns_data_types))
metadata_fh.close()

# these are for quick lookups later
parallax_idx = gaia_columns.index("parallax")
parallax_error_idx = gaia_columns.index("parallax_error")
ra_idx = gaia_columns.index("ra")
pmra_idx = gaia_columns.index("pmra")
pmra_error_idx = gaia_columns.index("pmra_error")
dec_idx = gaia_columns.index("dec")
pmdec_idx = gaia_columns.index("pmdec")
pmdec_error_idx = gaia_columns.index("pmdec_error")
radial_velocity_idx = gaia_columns.index("radial_velocity")
radial_velocity_error_idx = gaia_columns.index("radial_velocity_error")
distance_idx = all_columns.index("distance")
distance_error_idx = all_columns.index("distance_error")
x_idx = all_columns.index("x")
y_idx = all_columns.index("y")
z_idx = all_columns.index("z")
vx_idx = all_columns.index("vx")
vy_idx = all_columns.index("vy")
vz_idx = all_columns.index("vz")

create_table_columns = ""

# create the columns string you'd send to a CREATE TABLE command in sql
for i in range(0, len(all_columns)):
    col_title = all_columns[i]
    col_data_type = all_columns_data_types[i]
    create_table_columns += col_title + " " + col_data_type + ","

create_table_str = "CREATE TABLE gaia (" + create_table_columns[:-1] + ")"
insert_into_table_columns = ",".join(all_columns)

# just some global state variables
skipped_no_parallax = 0
skipped_cut_pmra = 0
skipped_cut_pmdec = 0
skipped_cut_radial_velocity = 0
total_counter = 0
file_counter = 0
open_connections = {}

def is_valid(source_values):
    global skipped_no_parallax
    global skipped_cut_pmra
    global skipped_cut_pmdec
    global skipped_cut_radial_velocity

    # sanity
    if len(source_values) != len(gaia_columns.columns):
        return False

    # skip those w/o parallax
    if source_values[parallax_idx] == "":
        skipped_no_parallax = skipped_no_parallax + 1
        return False

    # pmra error cut
    pmra_over_error = math.fabs(utils_str.to_float(source_values[pmra_idx]) / utils_str.to_float(source_values[pmra_error_idx]))
    if pmra_over_error < cut_pmra_over_error:
        skipped_cut_pmra = skipped_cut_pmra + 1
        return False

    # pmdec error cut
    pmdec_over_error = math.fabs(utils_str.to_float(source_values[pmdec_idx]) / utils_str.to_float(source_values[pmdec_error_idx]))
    if pmdec_over_error < cut_pmdec_over_error:
        skipped_cut_pmdec = skipped_cut_pmdec + 1
        return False

    # radial_velocity error cut
    radial_velocity_over_error = math.fabs(utils_str.to_float(source_values[radial_velocity_idx]) / utils_str.to_float(source_values[radial_velocity_error_idx]))
    if radial_velocity_over_error < cut_radial_velocity_over_error:
        skipped_cut_radial_velocity = skipped_cut_radial_velocity + 1
        return False

    return True

def write_star(x, y, z, data):
    insertion_value_str = ",".join(data)
    insertion_str = "INSERT INTO gaia (" + insert_into_table_columns + ") VALUES (%s)" % insertion_value_str

    # Gives the names for the database folders
    x_idx = int(x/cell_size_pc)
    y_idx = int(y/cell_size_pc)
    z_idx = int(z/cell_size_pc)
    cell_dir = utils_path.append(dest_dir, "%+d/%+d/%+d" % (x_idx, y_idx, z_idx))

    if not os.path.isdir(cell_dir):
        os.makedirs(cell_dir)

    cell_db_filename = utils_path.append(cell_dir, "cell.db")
    new_db = not os.path.isfile(cell_db_filename)
    c = db_connection_cache.get(cell_db_filename, open_connections)

    if new_db:
        c.execute(create_table_str)

    c.execute(insertion_str)

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

        # throws in all columns that we take from Gaia as-is (compared to distance etc, calculated below)
        for idx, val in enumerate(source_values):
            dt = gaia_columns.data_types[idx]
            stripped_val = val.strip() # remove spaces and linebreaks!

            if stripped_val == "":
                dest_values[idx] = "NULL"
            elif dt == "text":
                dest_values[idx] = "\"%s\"" % stripped_val
            elif dt == "integer" and val == "false":
                dest_values[idx] = "0"
            elif dt == "integer" and val == "true":
                dest_values[idx] = "1"
            else:
                dest_values[idx] = stripped_val

        # Almost criminal to do abs here, but I'm only interested in distances up to 3 kpc so
        # i think its fine. Also, 1/parallax does not work for large distances, but 3kpc is kindof an upper limit.
        parallax = abs(float(dest_values[parallax_idx]))
        parallax_error = float(dest_values[parallax_error_idx])
        distance_pc = 1.0/(parallax/1000.0) # distance from parallax, parallax in mArcSec, hence conversion to ArcSec
        distance_pc_error = 1000*(parallax_error/(parallax*parallax)) # by error propagation of d = 1000/p (p in mas)
        dest_values[distance_idx] = str(distance_pc)
        dest_values[distance_error_idx] = str(distance_pc_error)

        ra = float(dest_values[ra_idx]) * conv.deg_to_rad
        dec = float(dest_values[dec_idx]) * conv.deg_to_rad
        pos_pc = vec3.cartesian_position_from_celestial(ra, dec, distance_pc)
        x = pos_pc[0]
        y = pos_pc[1]
        z = pos_pc[2]

        if (x < -max_dist_pc or x > max_dist_pc or
            y < -max_dist_pc or y > max_dist_pc or
            z < -max_dist_pc or z > max_dist_pc):
            continue

        dest_values[x_idx] = str(x)
        dest_values[y_idx] = str(y)
        dest_values[z_idx] = str(z)

        pmra = float(dest_values[pmra_idx]) * conv.mas_per_yr_to_rad_per_s
        pmdec = float(dest_values[pmdec_idx]) * conv.mas_per_yr_to_rad_per_s
        vrad = float(dest_values[radial_velocity_idx])
        vel_km_per_s = vec3.cartesian_velocity_from_celestial(ra, dec, distance_pc*conv.pc_to_km, pmra, pmdec, vrad)

        dest_values[vx_idx] = str(vel_km_per_s[0])
        dest_values[vy_idx] = str(vel_km_per_s[1])
        dest_values[vz_idx] = str(vel_km_per_s[2])

        write_star(x, y, z, dest_values)
        total_counter = total_counter + 1

        if total_counter % 1000 == 0:
            print("%d done" % total_counter)

        # Make sure no connection variables acquired before running this are used again.
        db_connection_cache.remove_unused(open_connections)
    
    file_counter = file_counter + 1
    print("Written to grid for csv: %s (%d files done, %d stars done)" % (file, file_counter, total_counter))

# Flushes out everything to disk.
db_connection_cache.remove_all(open_connections)

metadata_fh = open("%s/metadata" % dest_dir, "a")
metadata_fh.write("total_stars:%d\n" % total_counter)
metadata_fh.close()

end_time = time.time()
dt = end_time - start_time
print("Imported %d stars to gridded database" % total_counter)
print("Skipped %d because they lacked parallax" % skipped_no_parallax)
print("Skipped %d because pmra over error was under %d" % (skipped_cut_pmra, cut_pmra_over_error))
print("Skipped %d because pmdec over error was under %d" % (skipped_cut_pmdec, cut_pmdec_over_error))
print("Skipped %d because radial_velocity over error was under %d" % (skipped_cut_radial_velocity, cut_radial_velocity_over_error))
print("Finished in " + str(int(dt)) + " seconds")