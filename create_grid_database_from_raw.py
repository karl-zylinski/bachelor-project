# Author: Karl Zylinski, Uppsala University

# Creates a 3D grid of databases from the output of "create_grid_raw.py"
# Each database if for one cell, i.e. split into regions of (ra, dec, dist)
# the ra and dec is 1 degree each in size, the dist is configurable in
# create_grid_raw.py.

# The output is a bunch of databases inside the folder specified by db_folder
# arranged like ra/dec/dist.db. These are then used in find_stars_in_db.py,
# it does quick spatial lookups using this 3D grid.

import time
import os
import datetime
import sqlite3
import pickle
import threading
import shutil
import metadata
import dict_utils
import re

db_folder = "db_gaia_dr2_rv_2019-02-26-18-11-25"
start_time = time.time()

metadata_dict = metadata.get(db_folder)
columns = eval(dict_utils.get_or_error(metadata_dict, "columns", "columns missing in %s metadata" % db_folder))
columns_datatypes = eval(dict_utils.get_or_error(metadata_dict, "columns_datatypes", "columns_datatypes missing in %s metadata" % db_folder))
cell_depth = int(dict_utils.get_or_error(metadata_dict, "cell_depth", "cell_depth missing in %s metadata" % db_folder))
max_distance = int(dict_utils.get_or_error(metadata_dict, "max_distance", "max_distance missing in %s metadata" % db_folder))
raw_dbs_folder = "%s/raw_dbs" % db_folder

assert(len(columns) == len(columns_datatypes))

create_table_columns = ""

for i in range(0, len(columns)):
    col_title = columns[i]
    col_data_type = columns[i]
    create_table_columns += col_title + " " + col_data_type + ","

create_table_columns = create_table_columns[:-1]
insert_into_table_columns = ",".join(columns)

def get_segment_out_dir_for_raw_db(raw_db):
    ra_dec_split_idx = re.search("\-|\+", raw_db).start()
    dec_end_idx = raw_db.index(".")
    segment_ra = raw_db[0:ra_dec_split_idx]
    segment_dec = raw_db[ra_dec_split_idx:dec_end_idx]
    return "%s/%s/%s" % (db_folder, segment_ra, segment_dec)

def import_raw_dbs(raw_db_filenames):
    num = len(raw_db_filenames)
    count = 0
    for file in raw_db_filenames:
        if count % 100 == 0:
            print("%d/%d" % (count, num))

        count = count + 1
        # a segment is a angular segment on sky with cells at different depth, like a rod

        segment_fh = open("%s/%s" % (raw_dbs_folder, file), 'rb')
        segment = pickle.load(segment_fh)
        segment_fh.close()

        segment_out_dir = get_segment_out_dir_for_raw_db(file)
        insertion_value_str = ""

        for dist_idx, stars in enumerate(segment): # dist_idx is distance/cell_depth
            if len(stars) == 0:
                continue

            if not os.path.isdir(segment_out_dir):
                os.makedirs(segment_out_dir)

            cell_db = "%s/%d.db" % (segment_out_dir, dist_idx)
            conn = sqlite3.connect(cell_db)
            c = conn.cursor()
            c.execute('pragma mmap_size=589934592;')
            c.execute("CREATE TABLE gaia (" + create_table_columns + ")")

            insert_counter = 0
            insertion_value_str = ""
            for star_data in stars:
                insertion_value_str = insertion_value_str + "(" + ",".join(star_data) + "),"
                insert_counter = insert_counter + 1

            insertion_value_str = insertion_value_str[:-1]
            c.execute("INSERT INTO gaia (" + insert_into_table_columns + ") VALUES %s" % insertion_value_str)
            c.execute("CREATE INDEX index_ra ON gaia (ra)")
            c.execute("CREATE INDEX index_dec ON gaia (dec)")
            c.execute("CREATE INDEX index_parallax ON gaia (parallax)")
            c.execute("CREATE INDEX index_pmra ON gaia (pmra)")
            c.execute("CREATE INDEX index_pmdec ON gaia (pmdec)")
            c.execute("CREATE INDEX index_radial_velocity ON gaia (radial_velocity)")
            c.execute("CREATE INDEX index_distance ON gaia (distance)")
            conn.commit()
            conn.close()

num_threads = 10
raw_dbs = list(filter(lambda x: x.endswith(".raw_db"), os.listdir(raw_dbs_folder)))
num_raw_dbs = len(raw_dbs)
num_per_thread = num_raw_dbs//num_threads

for rdb in raw_dbs:
    ra_dir = "%s/%s" % (db_folder, re.split("\-|\+", rdb)[0])
    
    if os.path.isdir(ra_dir):
        shutil.rmtree(ra_dir)

threads = []

for i in range(0, num_threads):
    start = i * num_per_thread
    end = (i + 1) * num_per_thread

    if i == num_threads:
        end = num_raw_dbs

    thread = threading.Thread(target = import_raw_dbs, kwargs = {'raw_db_filenames': raw_dbs[start:end]})
    threads.append(thread)
    thread.start()

for t in threads:
    t.join()

end_time = time.time()
dt = end_time - start_time
print("Finished in " + str(int(dt)) + " seconds")