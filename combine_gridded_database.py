import os
import sys
import utils_str
import utils_path
import sqlite3
import metadata

def verify_arguments():
    if len(sys.argv) != 3:
        return False

    if not os.path.isdir(sys.argv[1]):
        return False

    if os.path.isfile(sys.argv[2]) or os.path.isdir(sys.argv[2]):
        return False

    return True

assert verify_arguments(), "Usage: combine_gridded_database.py db_folder output.db"
db_folder = sys.argv[1]
conn = sqlite3.connect(sys.argv[2])
conn.execute('pragma mmap_size=5000000000;')

md = metadata.get(db_folder)

create_table_columns = ""

all_columns = md["columns"]
all_columns_data_types = md["columns_datatypes"]

# create the columns string you'd send to a CREATE TABLE command in sql
for i in range(0, len(all_columns)):
    col_title = all_columns[i]
    col_data_type = all_columns_data_types[i]
    create_table_columns += col_title + " " + col_data_type + ","

create_table_str = "CREATE TABLE gaia (" + create_table_columns[:-1] + ")"
conn.execute(create_table_str)

counter = 0
for ix_str in os.listdir(db_folder):
    ix_folder = utils_path.append(db_folder, ix_str)

    if not os.path.isdir(ix_folder):
        continue

    ix = utils_str.to_int(ix_str) # ix as in integer x

    if ix == None:
        continue

    for iy_str in os.listdir(ix_folder):
        iy_folder = utils_path.append(ix_folder, iy_str)

        if not os.path.isdir(iy_folder):
            continue

        iy = utils_str.to_int(iy_str)

        if iy == None:
            continue

        for iz_str in os.listdir(iy_folder):
            iz_folder = utils_path.append(iy_folder, iz_str)

            if not os.path.isdir(iz_folder):
                continue

            iz = utils_str.to_int(iz_str)

            if iz == None:
                continue

            cell_db_filename = utils_path.append(iz_folder, "cell.db")
            
            if not os.path.isfile(cell_db_filename):
                continue

            counter = counter + 1

            if counter % 1000 == 0:
                print("%d" % counter)
                conn.commit()

            cell_db = sqlite3.connect(cell_db_filename)
            all_stars = cell_db.execute('SELECT * FROM gaia').fetchall()

            # Insert those contents into another table.
            c = conn.cursor()
            for star in all_stars:
                c.execute('INSERT INTO gaia VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', star)

            cell_db.close()



conn.commit()
conn.close()