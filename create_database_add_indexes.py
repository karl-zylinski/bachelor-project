import sys
import utils_str
import sqlite3
import utils_path
import os

def verify_arguments():
    if len(sys.argv) != 2:
        return False

    if not os.path.isdir(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: create_database_add_indexes.py db_folder"

db_folder = sys.argv[1]

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
            conn = sqlite3.connect(cell_db_filename)

            try:
                conn.execute("CREATE INDEX index_x ON gaia (x)")
                conn.execute("CREATE INDEX index_y ON gaia (y)")
                conn.execute("CREATE INDEX index_z ON gaia (z)")
                conn.execute("CREATE INDEX index_vx ON gaia (vx)")
                conn.execute("CREATE INDEX index_vy ON gaia (vy)")
                conn.execute("CREATE INDEX index_vz ON gaia (vz)")
                print("Written indexes for: %s" % cell_db_filename)
            except:
                print("%s already has indexes!" % cell_db_filename)

            conn.close()

