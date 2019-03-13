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

# Assumes all angles in degrees. Make sure that all inputted length units are the same!!
def cartesian_velocity_from_celestial(ra, dec, r, pmra, pmdec, rv):
    ra_rad = ra * conv.deg_to_rad
    dec_rad = dec * conv.deg_to_rad
    pmra_rad = pmra * conv.deg_to_rad
    pmdec_rad = pmdec * conv.deg_to_rad

    return [cos(dec_rad)*cos(ra_rad)*rv + r*cos(dec_rad)*sin(ra_rad)*pmra_rad + r*sin(dec_rad)*cos(ra_rad)*pmdec_rad,
            cos(dec_rad)*sin(ra_rad)*rv - r*cos(dec_rad)*cos(ra_rad)*pmra_rad + r*sin(dec_rad)*sin(ra_rad)*pmdec_rad,
            sin(dec_rad)*rv - r*cos(dec_rad)*pmdec_rad]

def celestial_speed(ra, dec, r, pmra, pmdec, rv):
    ra_rad = ra * conv.deg_to_rad
    dec_rad = dec * conv.deg_to_rad
    pmra_rad = pmra * conv.deg_to_rad
    pmdec_rad = pmdec * conv.deg_to_rad

    cos_dec = cos(dec_rad)
    return sqrt(rv*rv + r*r*cos_dec*cos_dec*pmra_rad*pmra_rad + r*r*pmdec_rad*pmdec_rad)

def celestial_speed_error(ra, dec, r, pmra, pmdec, rv, pmra_error, pmdec_error, rv_error):
    v = celestial_speed(ra, dec, r, pmra, pmdec, rv)

    ra_rad = ra * conv.deg_to_rad
    dec_rad = dec * conv.deg_to_rad
    pmra_rad = pmra * conv.deg_to_rad
    pmdec_rad = pmdec * conv.deg_to_rad
    pmra_error_rad = pmra_error * conv.deg_to_rad
    pmdec_error_rad = pmdec_error * conv.deg_to_rad

    cos_dec = cos(dec_rad)
    term1 = r*r*cos_dec*cos_dec*pmra_rad*pmra_error_rad
    term2 = r*r*pmdec_rad*pmdec_error_rad
    term3 = rv*rv_error
    
    return (1/v)*sqrt(term1*term1 + term2*term2 + term3*term3)

def celestial_position_diff(ra1_deg, dec1_deg, r1, ra2_deg, dec2_deg, r2):
    ra1 = ra1_deg * conv.deg_to_rad
    dec1 = dec1_deg * conv.deg_to_rad
    ra2 = ra2_deg * conv.deg_to_rad
    dec2 = dec2_deg * conv.deg_to_rad

    return sqrt(r1*r1 + r2*r2 - 2*r1*r2*(cos(dec1)*cos(dec2)*cos(ra1 - ra2) + sin(dec1)*sin(dec2)))

# linear error propagation for difference of two celestial coordinates with errors in each component
def celestial_magnitude_of_position_difference_error(ra1_deg, dec1_deg, r1,
                                        ra1_error_deg, dec1_error_deg, r1_error,
                                        ra2_deg, dec2_deg, r2,
                                        ra2_error_deg, dec2_error_deg, r2_error):
    s = celestial_position_diff(ra1_deg, dec1_deg, r1, ra2_deg, dec2_deg, r2)

    ra1 = ra1_deg * conv.deg_to_rad
    dec1 = dec1_deg * conv.deg_to_rad
    ra1_error = ra1_error_deg * conv.deg_to_rad
    dec1_error = dec1_error_deg * conv.deg_to_rad
    ra2 = ra2_deg * conv.deg_to_rad
    dec2 = dec2_deg * conv.deg_to_rad
    ra2_error = ra2_error_deg * conv.deg_to_rad
    dec2_error = dec2_error_deg * conv.deg_to_rad
    
    # a and b are factors that appear more than once so i put them here
    a = cos(dec1)*cos(dec2)*cos(ra1 - ra2) + sin(dec1)*sin(dec2)
    b = r1*r2*cos(dec1)*cos(dec2)*sin(ra1 - ra2)

    term1 = (r1 - r2*a)*r1_error
    term2 = (r2 - r1*a)*r2_error
    term3 = b*ra1_error
    term4 = b*ra2_error
    term5 = r1*r2*(cos(dec1)*cos(dec2) - sin(dec1)*cos(dec2)*cos(ra1 - ra2))*dec1_error
    term6 = r1*r2*(sin(dec1)*cos(dec2) - cos(dec1)*cos(dec2)*cos(ra1 - ra2))*dec2_error
    return (1/s)*sqrt(term1*term1 + term2*term2 + term3*term3 + term4*term4 + term5*term5 + term6*term6)

# propagates error of |v2 - v1| where v2 and v1 are vectors and parameters are in celestial coordinates
def celestial_magnitude_of_velocity_difference_error(
            ra1_deg, dec1_deg, r1,
            ra1_error_deg, dec1_error_deg, r1_error,
            pmra1_deg_per_s, pmdec1_deg_per_s, rv1,
            pmra1_error_deg_per_s, pmdec1_error_deg_per_s, rv1_error,
            ra2_deg, dec2_deg, r2,
            ra2_error_deg, dec2_error_deg, r2_error,
            pmra2_deg_per_s, pmdec2_deg_per_s, rv2,
            pmra2_error_deg_per_s, pmdec2_error_deg_per_s, rv2_error):
    ra1 = ra1_deg * conv.deg_to_rad
    ra1_error = ra1_error_deg * conv.deg_to_rad
    dec1 = dec1_deg * conv.deg_to_rad
    dec1_error = dec1_error_deg * conv.deg_to_rad
    pmra1 = pmra1_deg_per_s * conv.deg_to_rad
    pmra1_error = pmra1_error_deg_per_s * conv.deg_to_rad
    pmdec1 = pmdec1_deg_per_s * conv.deg_to_rad
    pmdec1_error = pmdec1_error_deg_per_s * conv.deg_to_rad
    ra2 = ra2_deg * conv.deg_to_rad
    ra2_error = ra2_error_deg * conv.deg_to_rad
    dec2 = dec2_deg * conv.deg_to_rad
    dec2_error = dec2_error_deg * conv.deg_to_rad
    pmra2 = pmra2_deg_per_s * conv.deg_to_rad
    pmra2_error = pmra2_error_deg_per_s * conv.deg_to_rad
    pmdec2 = pmdec2_deg_per_s * conv.deg_to_rad
    pmdec2_error = pmdec2_error_deg_per_s * conv.deg_to_rad

    # first: error propgate to vx, vy, vz (cartesian)

    dvx1_dra = -cos(dec1)*sin(ra1)*rv1 + r1*cos(dec1)*cos(ra1)*pmra1 - r1*sin(dec1)*sin(ra1)*pmdec1
    dvx1_ddec = -sin(dec1)*cos(ra1)*rv1 - r1*sin(dec1)*sin(ra1)*pmra1 + r1*cos(dec1)*cos(ra1)*pmdec1
    dvx1_dr = cos(dec1)*sin(ra1)*pmra1 + sin(dec1)*cos(ra1)*pmdec1
    dvx1_dpmra = r1*cos(dec1)*sin(ra1)
    dvx1_dpmdec = r1*sin(dec1)*cos(ra1)
    dvx1_drv = cos(dec1)*cos(ra1)

    dvy1_dra = cos(dec1)*cos(ra1)*rv1 + r1*cos(dec1)*sin(ra1)*pmra1 + r1*sin(dec1)*cos(ra1)*pmdec1
    dvy1_ddec = -sin(dec1)*sin(ra1)*rv1 + r1*sin(dec1)*cos(ra1)*pmra1 + r1*cos(dec1)*sin(ra1)*pmdec1
    dvy1_dr = -cos(dec1)*cos(ra1)*pmra1 + sin(dec1)*sin(ra1)*pmdec1
    dvy1_dpmra = -r1*cos(dec1)*cos(ra1)
    dvy1_dpmdec = r1*sin(dec1)*sin(ra1)
    dvy1_drv = cos(dec1)*sin(ra1)

    dvz1_dra = 0
    dvz1_ddec = cos(dec1)*rv1 + r1*sin(dec1)*pmdec1
    dvz1_dr = -cos(dec1)*pmdec1
    dvz1_dpmra = 0
    dvz1_dpmdec = -r1*cos(dec1)
    dvz1_drv = sin(dec1)

    error_vx1 = sqrt((dvx1_dra*ra1_error)**2 + (dvx1_ddec*dec1_error)**2 + (dvx1_dr*r1_error)**2 + (dvx1_dpmra*pmra1_error)**2 + (dvx1_dpmdec*pmdec1_error)**2 + (dvx1_drv*rv1_error)**2)
    error_vy1 = sqrt((dvy1_dra*ra1_error)**2 + (dvy1_ddec*dec1_error)**2 + (dvy1_dr*r1_error)**2 + (dvy1_dpmra*pmra1_error)**2 + (dvy1_dpmdec*pmdec1_error)**2 + (dvy1_drv*rv1_error)**2)
    error_vz1 = sqrt((dvz1_dra*ra1_error)**2 + (dvz1_ddec*dec1_error)**2 + (dvz1_dr*r1_error)**2 + (dvz1_dpmra*pmra1_error)**2 + (dvz1_dpmdec*pmdec1_error)**2 + (dvz1_drv*rv1_error)**2)

    dvx2_dra = -cos(dec2)*sin(ra2)*rv2 + r2*cos(dec2)*cos(ra2)*pmra2 - r2*sin(dec2)*sin(ra2)*pmdec2
    dvx2_ddec = -sin(dec2)*cos(ra2)*rv2 - r2*sin(dec2)*sin(ra2)*pmra2 + r2*cos(dec2)*cos(ra2)*pmdec2
    dvx2_dr = cos(dec2)*sin(ra2)*pmra2 + sin(dec2)*cos(ra2)*pmdec2
    dvx2_dpmra = r2*cos(dec2)*sin(ra2)
    dvx2_dpmdec = r2*sin(dec2)*cos(ra2)
    dvx2_drv = cos(dec2)*cos(ra2)

    dvy2_dra = cos(dec2)*cos(ra2)*rv2 + r2*cos(dec2)*sin(ra2)*pmra2 + r2*sin(dec2)*cos(ra2)*pmdec2
    dvy2_ddec = -sin(dec2)*sin(ra2)*rv2 + r2*sin(dec2)*cos(ra2)*pmra2 + r2*cos(dec2)*sin(ra2)*pmdec2
    dvy2_dr = -cos(dec2)*cos(ra2)*pmra2 + sin(dec2)*sin(ra2)*pmdec2
    dvy2_dpmra = -r2*cos(dec2)*cos(ra2)
    dvy2_dpmdec = r2*sin(dec2)*sin(ra2)
    dvy2_drv = cos(dec2)*sin(ra2)

    dvz2_dra = 0
    dvz2_ddec = cos(dec2)*rv2 + r2*sin(dec2)*pmdec2
    dvz2_dr = -cos(dec2)*pmdec2
    dvz2_dpmra = 0
    dvz2_dpmdec = -r2*cos(dec2)
    dvz2_drv = sin(dec2)
    
    error_vx2 = sqrt((dvx2_dra*ra2_error)**2 + (dvx2_ddec*dec2_error)**2 + (dvx2_dr*r2_error)**2 + (dvx2_dpmra*pmra2_error)**2 + (dvx2_dpmdec*pmdec2_error)**2 + (dvx2_drv*rv2_error)**2)
    error_vy2 = sqrt((dvy2_dra*ra2_error)**2 + (dvy2_ddec*dec2_error)**2 + (dvy2_dr*r2_error)**2 + (dvy2_dpmra*pmra2_error)**2 + (dvy2_dpmdec*pmdec2_error)**2 + (dvy2_drv*rv2_error)**2)
    error_vz2 = sqrt((dvz2_dra*ra2_error)**2 + (dvz2_ddec*dec2_error)**2 + (dvz2_dr*r2_error)**2 + (dvz2_dpmra*pmra2_error)**2 + (dvz2_dpmdec*pmdec2_error)**2 + (dvz2_drv*rv2_error)**2)

    v1 = cartesian_velocity_from_celestial(ra1, dec1, r1, pmra1, pmdec1, rv1)
    v2 = cartesian_velocity_from_celestial(ra2, dec2, r2, pmra2, pmdec2, rv2)
    
    # now: error propagate |v2 - v1| = vdiff using vx, vy, vz errors (v2, v1 are vectors here)

    s = len(sub(v2, v1))

    # note that abs(ds_vx1) == abs(ds_vx2), so we can use same expression for both since squared in error propagation
    # also, 1/s is already taken outside (see return statement)
    ds_dvx = (v2[0] - v1[0])
    ds_dvy = (v2[1] - v1[1])
    ds_dvz = (v2[2] - v1[2])

    return (1/s)*sqrt((ds_dvx*error_vx1)**2 + (ds_dvy*error_vy1)**2 + (ds_dvz*error_vz1)**2 + 
                (ds_dvx*error_vx2)**2 + (ds_dvy*error_vy2)**2 + (ds_dvz*error_vz2)**2)
