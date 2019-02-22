import time
import os
import datetime
import sqlite3

db_folder = "db_gaia_dr2_rv_2019-02-22-15-21-18"
start_time = time.time()

for file in os.listdir(db_folder):
    if not file.endswith(".raw_db"):
        continue

    grid_fh = open("%s/%s" % (db_folder, file), 'r')
    grid = eval(grid_fh.read())
    grid_fh.close()

    for db_name, stars in grid.items():
        cell_db = "%s/%s.db" % (db_folder, db_name)
        print("Writing cell database: %s" % cell_db)
        conn = sqlite3.connect(cell_db)
        c = conn.cursor()
        c.execute('pragma mmap_size=4000000000;')
        c.execute("CREATE TABLE gaia (" + create_table_columns + ")")

        insert_counter = 0
        for star_data in stars:
            c.execute("INSERT INTO gaia (" + all_columns_text + ") VALUES (" + ",".join(star_data) + ")")
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