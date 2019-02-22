import numpy as np
import matplotlib.pyplot as plt
import sqlite3

db_name = "../gaia_dr2_rv_2019-02-22-15-56-06.db"
conn = sqlite3.connect(db_name)
c = conn.cursor()
qt = c.execute("SELECT teff_val FROM gaia WHERE teff_val IS NOT NULL").fetchall()

t = list(map(lambda r: r[0], qt))
n, bins, patches = plt.hist(t, 1000)

plt.xlabel('T_eff')
plt.ylabel('Number of stars')
plt.savefig('plot_rv_cat_teff.png')