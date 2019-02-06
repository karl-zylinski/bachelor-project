import math

deg_to_rad = math.pi/180
rad_to_deg = 180/math.pi
mas_to_deg = 1.0/3600000.0
year_to_sec = 365.25 * 24 * 3600
mas_per_yr_to_rad_per_s = (mas_to_deg*deg_to_rad)/year_to_sec

def vec3_len(v):
    return math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])

def vec3_dot(v1, v2):
    return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]

def vec3_scale(v, s):
    return [v[0] * s, v[1] * s, v[2] * s]

# converts celestial vector to cartesian (ra and dec in degrees)
def vec3_from_celestial(ra, dec, r):
    ra_rad = ra * deg_to_rad
    dec_rad = dec * deg_to_rad
    return [r * math.cos(ra_rad) * math.cos(dec_rad), # cos(ra_rad) * sin(pi/2 - dec_rad)
            r * math.sin(ra_rad) * math.cos(dec_rad), # sin(ra_rad) * sin(pi/2 - dec_rad)
            r * math.sin(dec_rad)] # cos(pi/2 - dec_rad)

v1 = vec3_from_celestial(-7.198384969540815 * mas_per_yr_to_rad_per_s, -16.44667141905734 * mas_per_yr_to_rad_per_s, 42.2501431483888)
v2 = vec3_from_celestial(29.540255494580656 * mas_per_yr_to_rad_per_s, -30.7994721695402 * mas_per_yr_to_rad_per_s, 33.39671721859703)
print(v1)
print(v2)
print("")

s1 = vec3_len(v1)
s2 = vec3_len(v2)
print(s1)
print(s2)
print("")

vdir1 = vec3_scale(v1, 1/s1)
vdir2 = vec3_scale(v2, 1/s2)
print(vdir1)
print(vdir2)
print("")

d = vec3_dot(vdir1, vdir2)
print(d)
angle = math.acos(d)
print(angle * rad_to_deg)
print(angle * rad_to_deg < 1)


