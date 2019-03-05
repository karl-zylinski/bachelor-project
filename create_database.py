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
import gaia_columns
import db_connection_cache
import sqlite3

cut_parallax_over_error = 10
cut_pmra_over_error = 10
cut_pmdec_over_error = 10
cut_radial_velocity_over_error = 10

create_additional_single_db = True # Disable if doing complete Gaia DR2
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

assert not os.path.isdir(dest_dir), "Folder already exists: %s" % dest_dir
os.mkdir(dest_dir)

assert(len(gaia_columns.columns) == len(gaia_columns.data_types))

# add extra columns not in gaia source
extra_columns = ["distance"]
extra_coumns_data_type = ["real"]

all_columns = gaia_columns.columns + extra_columns
all_columns_data_types = gaia_columns.data_types + extra_coumns_data_type

# write metadata file
metadata_fh = open("%s/metadata" % dest_dir, "w")
metadata_fh.write("cut_parallax_over_error:%d\n" % cut_parallax_over_error)
metadata_fh.write("cut_pmra_over_error:%d\n" % cut_pmra_over_error)
metadata_fh.write("cut_pmdec_over_error:%d\n" % cut_pmdec_over_error)
metadata_fh.write("cut_radial_velocity_over_error:%d\n" % cut_radial_velocity_over_error)
metadata_fh.write("max_distance:%d\n" % max_dist)
metadata_fh.write("cell_depth:%d\n" % cell_depth)
metadata_fh.write("columns:%s\n" % str(all_columns))
metadata_fh.write("columns_datatypes:%s" % str(all_columns_data_types))
metadata_fh.close()

parallax_idx = gaia_columns.index("parallax")
parallax_over_error_idx = gaia_columns.index("parallax_over_error")
ra_idx = gaia_columns.index("ra")
pmra_idx = gaia_columns.index("pmra")
pmra_error_idx = gaia_columns.index("pmra_error")
dec_idx = gaia_columns.index("dec")
pmdec_idx = gaia_columns.index("pmdec")
pmdec_error_idx = gaia_columns.index("pmdec_error")
radial_velocity_idx = gaia_columns.index("radial_velocity")
radial_velocity_error_idx = gaia_columns.index("radial_velocity_error")
distance_idx = all_columns.index("distance")

create_table_columns = ""

# create the columns string you'd send to a CREATE TABLE command in sql
for i in range(0, len(all_columns)):
    col_title = all_columns[i]
    col_data_type = all_columns[i]
    create_table_columns += col_title + " " + col_data_type + ","

create_table_str = "CREATE TABLE gaia (" + create_table_columns[:-1] + ")"
insert_into_table_columns = ",".join(all_columns)

single_db_conn = None
single_db_cursor = None

if create_additional_single_db:
    single_db_conn = sqlite3.connect("%s/%s" % (dest_dir, "single_db.db"))
    single_db_cursor = single_db_conn.cursor()
    single_db_cursor.execute('pragma mmap_size=4294967296;')
    single_db_cursor.execute(create_table_str)

num_distance_cells = (max_dist - min_dist)//cell_depth

skipped_no_parallax = 0
skipped_cut_pmra = 0
skipped_cut_pmdec = 0
skipped_cut_radial_velocity = 0
skipped_cut_parallax = 0
total_counter = 0
file_counter = 0
open_connections = {}

def is_valid(source_values):
    global skipped_no_parallax
    global skipped_cut_pmra
    global skipped_cut_pmdec
    global skipped_cut_radial_velocity
    global skipped_cut_parallax

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

    # parallax error cut
    parallax_over_error = utils_str.to_float(source_values[parallax_over_error_idx])
    if parallax_over_error < cut_parallax_over_error:
        skipped_cut_parallax = skipped_cut_parallax + 1
        return False

    return True

def write_star(ra, dec, dist, data):
    ra_idx = int(ra)
    dec_idx = int(dec)
    dist_idx = int(distance/cell_depth)
    segment_dir = "%s/%d/%+d" % (dest_dir, ra_idx, dec_idx)

    if not os.path.isdir(segment_dir):
        os.makedirs(segment_dir)

    cell_db_filename = "%s/%d.db" % (segment_dir, dist_idx)

    new_db = not os.path.isfile(cell_db_filename)
    c = db_connection_cache.get(cell_db_filename, open_connections, total_counter)

    if new_db:
        c.execute(create_table_str)

    insertion_value_str = ",".join(data)
    insertion_str = "INSERT INTO gaia (" + insert_into_table_columns + ") VALUES (%s)" % insertion_value_str
    c.execute(insertion_str)

    if create_additional_single_db:
        single_db_cursor.execute(insertion_str)

        if total_counter % 10000 == 0:
            single_db_conn.commit()

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
        for idx, val in enumerate(source_values):
            dt = gaia_columns.data_types[idx]

            if val == "" or val == "\n":
                dest_values[idx] = "NULL"
            elif dt == "text":
                dest_values[idx] = "\"%s\"" % val
            elif dt == "integer" and val == "false":
                dest_values[idx] = "0"
            elif dt == "integer" and val == "true":
                dest_values[idx] = "1"
            else:
                dest_values[idx] = val

        # distance from parallax, parallax in mArcSec, hence conversion to ArcSec
        distance = 1.0/(float(dest_values[parallax_idx])/1000.0)

        if distance < min_dist or distance > max_dist:
            continue

        dest_values[distance_idx] = str(distance)

        ra = float(dest_values[ra_idx])
        dec = float(dest_values[dec_idx])

        write_star(ra, dec, distance, dest_values)
        total_counter = total_counter + 1

        if total_counter % 1000 == 0:
            print("%d done" % total_counter)

        if total_counter % 10000 == 0:
            db_connection_cache.remove_unused(open_connections, total_counter)
    
    file_counter = file_counter + 1
    print("Written to grid for csv: %s (%d files done, %d stars done)" % (file, file_counter, total_counter))

db_connection_cache.remove_all(open_connections)

if create_additional_single_db:
    print("Creating single db indices")
    single_db_cursor.execute("CREATE INDEX index_ra ON gaia (ra)")
    single_db_cursor.execute("CREATE INDEX index_dec ON gaia (dec)")
    single_db_cursor.execute("CREATE INDEX index_parallax ON gaia (parallax)")
    single_db_cursor.execute("CREATE INDEX index_pmra ON gaia (pmra)")
    single_db_cursor.execute("CREATE INDEX index_pmdec ON gaia (pmdec)")
    single_db_cursor.execute("CREATE INDEX index_radial_velocity ON gaia (radial_velocity)")
    single_db_cursor.execute("CREATE INDEX index_distance ON gaia (distance)")
    single_db_conn.commit()
    single_db_conn.close()

end_time = time.time()
dt = end_time - start_time
print("Imported %d stars to raw gid databases" % total_counter)
print("Skipped %d because they lacked parallax" % skipped_no_parallax)
print("Skipped %d because pmra over error was under %d" % (skipped_cut_pmra, cut_pmra_over_error))
print("Skipped %d because pmdec over error was under %d" % (skipped_cut_pmdec, cut_pmdec_over_error))
print("Skipped %d because radial_velocity over error was under %d" % (skipped_cut_radial_velocity, cut_radial_velocity_over_error))
print("Skipped %d because parallax over error was under %d" % (skipped_cut_parallax, cut_parallax_over_error))
print("Finished in " + str(int(dt)) + " seconds")