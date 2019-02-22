import numpy as np
import matplotlib.pyplot as plt
import sqlite3

db_name = "../gaia_dr2_rv_2019-02-21-15-17-54.db"
conn = sqlite3.connect(db_name)
c = conn.cursor()
dq = c.execute("SELECT distance FROM gaia WHERE phot_g_mean_mag < 17").fetchall()

d = list(map(lambda r: r[0], dq))
n, bins, patches = plt.hist(d, 1000, range = (-100, 10000))

plt.xlabel('Distance (Pc)')
plt.ylabel('Number of stars')
plt.show()