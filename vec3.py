import math
import conv

def len(v):
    return math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])

def dot(v1, v2):
    return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]

def scale(v, s):
    return [v[0] * s, v[1] * s, v[2] * s]

# converts celestial vector to cartesian (ra and dec in degrees)
def from_celestial(ra, dec, r):
    ra_rad = ra * conv.deg_to_rad
    dec_rad = dec * conv.deg_to_rad
    return [r * math.cos(ra_rad) * math.cos(dec_rad), # cos(ra_rad) * sin(pi/2 - dec_rad)
            r * math.sin(ra_rad) * math.cos(dec_rad), # sin(ra_rad) * sin(pi/2 - dec_rad)
            r * math.sin(dec_rad)] # cos(pi/2 - dec_rad)