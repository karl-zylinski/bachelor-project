import time
import os
import datetime
import sqlite3
import pickle

db_folder = "db_gaia_dr2_rv_2019-02-22-16-04-10"
start_time = time.time()

columns_fh = open("%s/columns" % db_folder, "r")
columns = eval(columns_fh.read())
columns_fh.close()

columns_data_types_fh = open("%s/columns_data_types" % db_folder, "r")
columns_data_types = eval(columns_data_types_fh.read())
columns_data_types_fh.close()

assert(len(columns) == len(columns_data_types))

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

    grid_fh = open("%s/%s" % (db_folder, file), 'rb')
    grid = pickle.load(grid_fh)
    grid_fh.close()

    for db_name, stars in grid.items():
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