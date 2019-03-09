# Author: Karl Zylinski, Uppsala University

# Keeps a bunch of sqlite3 databases going at the same time, with functions
# to close those that hasn't been used for a while.

import sqlite3

memory_map_size = 10000000
db_access_counter = 0
db_access_cleanse_peroid = 10000
db_access_counter_next_cleanse = db_access_cleanse_peroid

def get(db_name, open_connections):
    global db_access_counter
    db_access_counter = db_access_counter + 1
    existing = open_connections.get(db_name)

    if existing:
        existing["used_at"] = db_access_counter
        return existing["conn"]
    else:
        conn = sqlite3.connect(db_name)
        conn.execute('pragma mmap_size=%d;' % memory_map_size)
        conn_obj = {}
        conn_obj["used_at"] = db_access_counter
        conn_obj["conn"] = conn
        open_connections[db_name] = conn_obj
        return conn

def remove_unused(open_connections):
    global db_access_counter_next_cleanse

    if db_access_counter < db_access_counter_next_cleanse:
        return
    
    db_access_counter_next_cleanse = db_access_counter + db_access_cleanse_peroid
    to_remove = []

    for db_name, c in open_connections.items():
        if db_access_counter - c["used_at"] > db_access_cleanse_peroid:
            c["conn"].commit()
            c["conn"].close()
            to_remove.append(db_name)

    for r in to_remove:
        del open_connections[r]

def remove_all(open_connections):
    if open_connections == None and db_single != None:
        db_single.close()
        return

    for db_name, c in open_connections.items():
        c["conn"].commit()
        c["conn"].close()

    open_connections.clear()