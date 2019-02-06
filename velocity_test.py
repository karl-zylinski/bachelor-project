import math

deg_to_rad = math.pi/180
rad_to_deg = 180/math.pi
mas_to_deg = 1.0/3600000.0
mas_per_yr_to_rad_per_yr = mas_to_deg*deg_to_rad
km_per_s_to_km_per_year = 365.25 * 24 * 3600

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

v1 = vec3_from_celestial(1.36507123552316 * mas_per_yr_to_rad_per_yr, -35.42565811921144 * mas_per_yr_to_rad_per_yr, 2.2865597589737625 * km_per_s_to_km_per_year)
v2 = vec3_from_celestial(-14.163755619154164 * mas_per_yr_to_rad_per_yr, 7.36195070236888 * mas_per_yr_to_rad_per_yr, 12.184076848031015 * km_per_s_to_km_per_year)
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


