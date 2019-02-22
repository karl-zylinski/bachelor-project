import numpy as np
import matplotlib.pyplot as plt
import sqlite3

db_name = "../gaia_dr2_rv_2019-02-21-15-17-54.db"
conn = sqlite3.connect(db_name)
c = conn.cursor()
q = c.execute("SELECT phot_g_mean_mag, distance FROM gaia WHERE phot_g_mean_mag IS NOT NULL").fetchall()

g = list(map(lambda r: r[0], q))
d = list(map(lambda r: r[1], q))
#bp = list(map(lambda r: r[0], qbp))
#n, bins, patches = plt.hist(g, 1000)
plt.plot(g, d, 'o')
#n, bins, patches = plt.hist(rp, 40, facecolor = 'r', alpha=0.5)
#n, bins, patches = plt.hist(bp, 40, facecolor = 'b', alpha=0.5)

plt.xlabel('Gaia G magnitude')
plt.ylabel('Distance (Pc)')
plt.axes((8, 0, 6, 5000))
plt.show()