import sqlite3
import math

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

max_sep = 1 # maximal separation, pc
deg_to_rad = math.pi/180

for s in all_stars:
    sid = s[0]
    ra = s[1] # mas
    dec = s[2] # mas
    d = s[7] # distance in pc
    min_d = d - max_sep
    max_d = d + max_sep
    ra_rad = ra * deg_to_rad
    dec_rad = dec * deg_to_rad
    min_radir_sep = (ra_rad - max_sep/d)/deg_to_rad;
    max_radir_sep = (ra_rad + max_sep/d)/deg_to_rad;
    min_decdir_sep = (dec_rad - max_sep/d)/deg_to_rad;
    max_decdir_sep = (dec_rad + max_sep/d)/deg_to_rad;

    comoving_stars = c.execute('''
        SELECT source_id, phot_g_mean_mag
        FROM gaia
        WHERE source_id IS NOT %d
        AND distance > %d AND distance < %d
        AND ra > %d AND ra < %d
        AND dec > %d AND dec < %d''' % (sid, min_d, max_d, min_radir_sep, max_radir_sep, min_decdir_sep, max_decdir_sep)).fetchall()

    if len(comoving_stars) > 0:
        print(comoving_stars)

conn.close()