import numpy as np
import matplotlib.pyplot as plt
import sqlite3

db_name = "../gaia_dr2_rv_2019-02-21-15-17-54.db"
conn = sqlite3.connect(db_name)
c = conn.cursor()
qg = c.execute("SELECT phot_g_mean_mag FROM gaia WHERE phot_g_mean_mag IS NOT NULL").fetchall()
#qrp = c.execute("SELECT phot_rp_mean_mag FROM gaia WHERE phot_rp_mean_mag IS NOT NULL").fetchall()
#qbp = c.execute("SELECT phot_bp_mean_mag FROM gaia WHERE phot_bp_mean_mag IS NOT NULL").fetchall()

g = list(map(lambda r: r[0], qg))
#rp = list(map(lambda r: r[0], qrp))
#bp = list(map(lambda r: r[0], qbp))
n, bins, patches = plt.hist(g, 1000)
#n, bins, patches = plt.hist(rp, 40, facecolor = 'r', alpha=0.5)
#n, bins, patches = plt.hist(bp, 40, facecolor = 'b', alpha=0.5)

plt.xlabel('Magnitude')
plt.ylabel('Number of stars')
plt.show()