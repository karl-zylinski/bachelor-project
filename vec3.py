# Author: Karl Zylinski, Uppsala University

from math import sqrt, cos, sin
import conv

def len(v):
    return sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])

def dot(v1, v2):
    return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]

def sub(v1, v2):
    return [v1[0]-v2[0], v1[1]-v2[1], v1[2]-v2[2]]

def add(v1, v2):
    return [v1[0]+v2[0], v1[1]+v2[1], v1[2]+v2[2]]

def scale(v, s):
    return [v[0] * s, v[1] * s, v[2] * s]

# converts celestial vector to cartesian (ra and dec in degrees)
def cartesian_position_from_celestial(ra, dec, r):
    ra_rad = ra * conv.deg_to_rad
    dec_rad = dec * conv.deg_to_rad
    return [r * cos(ra_rad) * cos(dec_rad), # cos(ra_rad) * sin(pi/2 - dec_rad)
            r * sin(ra_rad) * cos(dec_rad), # sin(ra_rad) * sin(pi/2 - dec_rad)
            r * sin(dec_rad)] # cos(pi/2 - dec_rad)

def cartesian_velocity_from_celestial(ra, dec, r, pmra, pmdec, rv):
    ra_rad = ra * conv.deg_to_rad
    dec_rad = dec * conv.deg_to_rad
    pmra_rad = pmra * conv.deg_to_rad
    pmdec_rad = pmdec * conv.deg_to_rad

    return [cos(dec_rad)*cos(ra_rad)*rv + r*cos(dec_rad)*sin(ra_rad)*pmra_rad + r*sin(dec_rad)*cos(ra_rad)*pmdec_rad,
            cos(dec_rad)*sin(ra_rad)*rv - r*cos(dec_rad)*cos(ra_rad)*pmra_rad + r*sin(dec_rad)*sin(ra_rad)*pmdec_rad,
            sin(dec_rad)*rv - r*cos(dec_rad)*pmdec_rad]