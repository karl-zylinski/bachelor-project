import time
import os
import datetime
import sqlite3
import pickle
import threading
import shutil

db_folder = "db_gaia_dr2_rv_2019-02-25-16-44-00"
start_time = time.time()

metadata_filename = "%s/metadata" % db_folder
assert os.path.isfile(metadata_filename), "metadata mising: %s" % metadata_filename
metadata_fh = open(metadata_filename, "r")
metadata = metadata_fh.readlines()
metadata_fh.close()
metadata_dict = {}
raw_dbs_folder = "%s/raw_dbs" % db_folder

for mdi in metadata:
    key_value_pair = mdi.split(":")

    if len(key_value_pair) != 2:
        error("metadata in %s is of incorrect format" % db_folder)

    metadata_dict[key_value_pair[0]] = key_value_pair[1]

def dict_get_or_error(d, key, err):
    val = d.get(key)
    assert val != None, err
    return val

columns = eval(dict_get_or_error(metadata_dict, "columns", "columns missing in %s" % metadata_filename))
columns_datatypes = eval(dict_get_or_error(metadata_dict, "columns_datatypes", "columns_datatypes missing in %s" % metadata_filename))
cell_depth = int(dict_get_or_error(metadata_dict, "cell_depth", "cell_depth missing in %s" % metadata_filename))
max_distance = int(dict_get_or_error(metadata_dict, "max_distance", "max_distance missing in %s" % metadata_filename))

assert(len(columns) == len(columns_datatypes))

create_table_columns = ""

for i in range(0, len(columns)):
    col_title = columns[i]
    col_data_type = columns[i]
    create_table_columns += col_title + " " + col_data_type + ","

create_table_columns = create_table_columns[:-1]
insert_into_table_columns = ",".join(columns)

def get_segment_out_dir_for_raw_db(raw_db):
    segment_dec_ra = raw_db.split(".")[0].split("-")
    segment_dec = segment_dec_ra[0]
    segment_ra = segment_dec_ra[1]
    return "%s/%s/%s" % (db_folder, segment_dec, segment_ra)

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
    dec_dir = "%s/%s" % (db_folder, rdb.split("-")[0])
    
    if os.path.isdir(dec_dir):
        shutil.rmtree(dec_dir)

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