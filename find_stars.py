import sqlite3

dry_run = False
dry_run_print = True
db_name = "gaia_dr2_rv.db"
conn = sqlite3.connect(db_name)
c = conn.cursor()
all_stars = c.execute("SELECT source_id, ra, dec, parallax, pmra, pmdec, radial_velocity, distance FROM gaia").fetchall()

# 0 source_id
# 1 ra
# 2 dec
# 3 parallax
# 4 pmra
# 5 pmdec
# 6 radial_velocity
# 7 distance

for s in all_stars:
    ra = s[1] # mas
    dec = s[2] # mas
    d = s[7] # distance in pc

    comoving_stars = c.execute('''
        SELECT source_id, ra, dec, parallax, pmra, pmdec, radial_velocity
        FROM gaia
        WHERE ''').fetchall()

conn.close()