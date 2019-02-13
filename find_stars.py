import sqlite3
import math
import datetime

db_name = "gaia_dr2_2019-02-08-21-46-12.db"
max_sep = 1 # maximal separation of pairs, pc
max_vel_angle_diff = 1 # maximal angular difference of velocity vectors, degrees
max_vel_mag_diff = 10 # maximal velocity difference between velocity vectors, km/s
columns_to_fetch = "source_id, ra, dec, parallax, pmra, pmdec, radial_velocity, distance, phot_g_mean_mag"

# these are just in order as they appear in columns_to_fetch - used to fetch stuff from sql result arrays
i_source_id = 0
i_ra = 1
i_dec = 2
i_parallax = 3
i_pmra = 4
i_pmdec = 5
i_radial_velocity = 6
i_distance = 7
i_phot_g_mean_mag = 8

c = sqlite3.connect(db_name)
c.execute('pragma mmap_size=8589934592;')

deg_to_rad = math.pi/180
rad_to_deg = 180/math.pi
year_to_sec = 365.25 * 24 * 3600
mas_to_deg = 1.0/3600000.0
mas_per_yr_to_rad_per_s = (mas_to_deg*deg_to_rad)/year_to_sec
parsec_to_km = 3.08567758 * math.pow(10, 13)

# ACTUAL SCRIPT STARTS HERE

comoving_pairs = [] # index is pair identifier, each entry is an array of stars
star_sid_to_pair_idx = {} # maps star source_id to comoving_pairs index, for checking for redundancies

# will need to slice this up when doing full dr2 search
all_stars = c.execute("SELECT %s FROM gaia" % columns_to_fetch).fetchall() 
counter = 0
total_stars = len(all_stars)

for s in all_stars:
    counter = counter + 1
    done_str = "%s done of %s" % (counter, total_stars)
    sid = s[i_source_id]
    ra = s[i_ra] # deg
    dec = s[i_dec] # deg
    pmra = s[i_pmra] # mas/yr
    pmdec = s[i_pmdec] # mas/yr
    vrad = s[i_radial_velocity] # km/s
    d = s[i_distance] # distance in pc
    min_d = d - max_sep
    max_d = d + max_sep
    min_ra = ra - (max_sep*rad_to_deg)/d
    max_ra = ra + (max_sep*rad_to_deg)/d
    min_dec = dec - (max_sep*rad_to_deg)/d
    max_dec = dec + (max_sep*rad_to_deg)/d

    # this is a mas/yr value that corresponds to angular value for tangential speed max_vel_mag_diff/2 for this star
    ang_vel_diff = (max_vel_mag_diff/2) / (parsec_to_km * d * mas_per_yr_to_rad_per_s)

    pmra_ang_vel_min = pmra - ang_vel_diff
    pmra_ang_vel_max = pmra + ang_vel_diff
    pmdec_ang_vel_min = pmdec - ang_vel_diff
    pmdec_ang_vel_max = pmdec + ang_vel_diff

    # this is far from perfect, it just "boxes" in stars near the current, ie not a real distance check
    # but it's fast due to indexed database columns
    find_nearby_query = '''
        SELECT source_id, ra, dec, parallax, pmra, pmdec, radial_velocity, distance, phot_g_mean_mag
        FROM gaia
        WHERE source_id IS NOT %d
        AND distance > %f AND distance < %f
        AND ra > %f AND ra < %f
        AND dec > %f AND dec < %f
        AND pmra > %f AND pmra < %f
        AND pmdec > %f AND pmdec < %f''' % (sid, min_d, max_d, min_ra, max_ra, min_dec, max_dec, pmra_ang_vel_min, pmra_ang_vel_max, pmdec_ang_vel_min, pmdec_ang_vel_max)

    nearby_stars_similar_pm = c.execute(find_nearby_query).fetchall()

    if len(nearby_stars_similar_pm) == 0:
        continue

    # dont care about non-binary systems for now
    if len(nearby_stars_similar_pm) != 1:
        print("(%s) Skipping non-binary (%d):" % (done_str, len(nearby_stars_similar_pm)))
        continue

    nearby_stars_similar_pm.append(s)
    # nearby_stars_similar_pm should always be length 2 at this point, i.e we only look after pairs
    s1 = nearby_stars_similar_pm[0]
    s2 = nearby_stars_similar_pm[1]
    sid1 = s1[i_source_id]
    sid2 = s2[i_source_id]
    pair_idx1 = star_sid_to_pair_idx.get(sid1)
    pair_idx2 = star_sid_to_pair_idx.get(sid2)

    # pair already exists?
    if pair_idx1 != None and pair_idx2 != None and pair_idx1 == pair_idx2:
        continue

    new_idx = len(comoving_pairs)
    comoving_pairs.append([s1, s2])
    star_sid_to_pair_idx[sid1] = new_idx
    star_sid_to_pair_idx[sid2] = new_idx

    print("(%s) found neighbours:" % done_str)
    print(nearby_stars_similar_pm[0])
    print(nearby_stars_similar_pm[1])
    print("")
c.close()

output_name = datetime.datetime.now().strftime("found-pairs-from-" + db_name + "-%Y-%m-%d-%H-%M-%S.txt")
file = open(output_name,"w")
file.write(str(comoving_pairs))
file.close()