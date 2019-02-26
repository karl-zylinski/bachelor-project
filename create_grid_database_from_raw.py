import time
import os
import datetime
import sqlite3
import pickle

db_folder = "db_gaia_dr2_rv_2019-02-25-16-44-00"
start_time = time.time()

metadata_filename = "%s/metadata" % db_folder
assert os.path.isfile(metadata_filename), "metadata mising: %s" % metadata_filename
metadata_fh = open(metadata_filename, "r")
metadata = metadata_fh.readlines()
metadata_fh.close()
metadata_dict = {}

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

for file in os.listdir(db_folder):
    if not file.endswith(".raw_db"):
        continue

    # a segment is a angular segment on sky with cells at different depth, like a rod
    segment_fh = open("%s/%s" % (db_folder, file), 'rb')
    segment = pickle.load(segment_fh)
    segment_fh.close()

    for dist_idx, stars in enumerate(segment): # dist_idx is distance/cell_depth
        if len(stars) == 0:
            continue;

        db_name = file.split(".")[0] + "-%d" % dist_idx
        cell_db = "%s/%s.db" % (db_folder, db_name)
        print("Writing cell database: %s" % cell_db)
        conn = sqlite3.connect(cell_db)
        c = conn.cursor()
        c.execute("CREATE TABLE gaia (" + create_table_columns + ")")

        insert_counter = 0
        for star_data in stars:
            c.execute("INSERT INTO gaia (" + insert_into_table_columns + ") VALUES (" + ",".join(star_data) + ")")
            insert_counter = insert_counter + 1

            if insert_counter > 100000:
                insert_counter = 0
                conn.commit()

        conn.commit()
        c.execute("CREATE INDEX index_ra ON gaia (ra)")
        c.execute("CREATE INDEX index_dec ON gaia (dec)")
        c.execute("CREATE INDEX index_parallax ON gaia (parallax)")
        c.execute("CREATE INDEX index_pmra ON gaia (pmra)")
        c.execute("CREATE INDEX index_pmdec ON gaia (pmdec)")
        c.execute("CREATE INDEX index_radial_velocity ON gaia (radial_velocity)")
        c.execute("CREATE INDEX index_distance ON gaia (distance)")
        conn.commit()
        conn.close()

end_time = time.time()
dt = end_time - start_time
print("Imported %d stars to raw cell table" % total_counter)
print("Skipped %d because they lacked parallax" % no_parallax_skipped)
print("Skipped %d because csv line was of wrong length (%d)" % (invalid_lines, len(source_columns)))
print("Finished in " + str(int(dt)) + " seconds")