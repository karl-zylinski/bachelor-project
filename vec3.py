# Author: Karl Zylinski, Uppsala University

from math import sqrt, cos, sin
import conv

def mag(v):
    return sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])

def dot(v1, v2):
    return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]

def sub(v1, v2):
    return [v1[0]-v2[0], v1[1]-v2[1], v1[2]-v2[2]]

def add(v1, v2):
    return [v1[0]+v2[0], v1[1]+v2[1], v1[2]+v2[2]]

def scale(v, s):
    return [v[0] * s, v[1] * s, v[2] * s]

# ra and dec in radians
def cartesian_position_from_celestial(ra, dec, r):
    return [r * cos(ra) * cos(dec), # cos(ra) * sin(pi/2 - dec)
            r * sin(ra) * cos(dec), # sin(ra) * sin(pi/2 - dec)
            r * sin(dec)] # cos(pi/2 - dec)

# ra and dec in radians
def cartesian_velocity_from_celestial(ra, dec, r, pmra, pmdec, rv):
    return [cos(dec)*cos(ra)*rv + r*cos(dec)*sin(ra)*pmra + r*sin(dec)*cos(ra)*pmdec,
            cos(dec)*sin(ra)*rv - r*cos(dec)*cos(ra)*pmra + r*sin(dec)*sin(ra)*pmdec,
            sin(dec)*rv - r*cos(dec)*pmdec]

# calcualates |p2 - p1| based on celestial coordinates
def celestial_position_diff(ra1, dec1, r1, ra2, dec2, r2):
    return sqrt(r1*r1 + r2*r2 - 2*r1*r2*(cos(dec1)*cos(dec2)*cos(ra1 - ra2) + sin(dec1)*sin(dec2)))

# linear error propagation for difference of two celestial coordinates with errors in each component
def celestial_magnitude_of_position_difference_error(ra1, dec1, r1,
                                        ra1_error, dec1_error, r1_error,
                                        ra2, dec2, r2,
                                        ra2_error, dec2_error, r2_error):
    s = celestial_position_diff(ra1, dec1, r1, ra2, dec2, r2)
    
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

# Linearly propagates the error of a velocity given in celestial coordinates to cartesian via the
# formulas identical to the ones in function cartesian_velocity_from_celestial.
# All angles in radians. Make sure to have same units for all times and distances.
def celestial_coords_to_cartesian_error(
            ra, dec, r,
            ra_error, dec_error, r_error,
            pmra, pmdec, rv,
            pmra_error, pmdec_error, rv_error):
    dvx_dra = -cos(dec)*sin(ra)*rv + r*cos(dec)*cos(ra)*pmra - r*sin(dec)*sin(ra)*pmdec
    dvx_ddec = -sin(dec)*cos(ra)*rv - r*sin(dec)*sin(ra)*pmra + r*cos(dec)*cos(ra)*pmdec
    dvx_dr = cos(dec)*sin(ra)*pmra + sin(dec)*cos(ra)*pmdec
    dvx_dpmra = r*cos(dec)*sin(ra)
    dvx_dpmdec = r*sin(dec)*cos(ra)
    dvx_drv = cos(dec)*cos(ra)

    dvy_dra = cos(dec)*cos(ra)*rv + r*cos(dec)*sin(ra)*pmra + r*sin(dec)*cos(ra)*pmdec
    dvy_ddec = -sin(dec)*sin(ra)*rv + r*sin(dec)*cos(ra)*pmra + r*cos(dec)*sin(ra)*pmdec
    dvy_dr = -cos(dec)*cos(ra)*pmra + sin(dec)*sin(ra)*pmdec
    dvy_dpmra = -r*cos(dec)*cos(ra)
    dvy_dpmdec = r*sin(dec)*sin(ra)
    dvy_drv = cos(dec)*sin(ra)

    dvz_dra = 0
    dvz_ddec = cos(dec)*rv + r*sin(dec)*pmdec
    dvz_dr = -cos(dec)*pmdec
    dvz_dpmra = 0
    dvz_dpmdec = -r*cos(dec)
    dvz_drv = sin(dec)

    return [sqrt((dvx_dra*ra_error)**2 + (dvx_ddec*dec_error)**2 + (dvx_dr*r_error)**2 + (dvx_dpmra*pmra_error)**2 + (dvx_dpmdec*pmdec_error)**2 + (dvx_drv*rv_error)**2),
            sqrt((dvy_dra*ra_error)**2 + (dvy_ddec*dec_error)**2 + (dvy_dr*r_error)**2 + (dvy_dpmra*pmra_error)**2 + (dvy_dpmdec*pmdec_error)**2 + (dvy_drv*rv_error)**2),
            sqrt((dvz_dra*ra_error)**2 + (dvz_ddec*dec_error)**2 + (dvz_dr*r_error)**2 + (dvz_dpmra*pmra_error)**2 + (dvz_dpmdec*pmdec_error)**2 + (dvz_drv*rv_error)**2)]

# Linearly propagates the error of the expression |v2 - v1| where v2 and v1 are velocity vectors and
# the errors are given in celestial coordinates. It first propagates the error
# from celestial to cartesian velocity and then from cartesian velocity to the |v2 -v1| expression.
# All angles in radians. Make sure to have same units for all times and distances.
def celestial_magnitude_of_velocity_difference_error(
            ra1, dec1, r1,
            ra1_error, dec1_error, r1_error,
            pmra1, pmdec1, rv1,
            pmra1_error, pmdec1_error, rv1_error,
            ra2, dec2, r2,
            ra2_error, dec2_error, r2_error,
            pmra2, pmdec2, rv2,
            pmra2_error, pmdec2_error, rv2_error):
    v1_error = celestial_coords_to_cartesian_error(
        ra1, dec1, r1,
        ra1_error, dec1_error, r1_error,
        pmra1, pmdec1, rv1,
        pmra1_error, pmdec1_error, rv1_error)

    v2_error = celestial_coords_to_cartesian_error(
        ra2, dec2, r2,
        ra2_error, dec2_error, r2_error,
        pmra2, pmdec2, rv2,
        pmra2_error, pmdec2_error, rv2_error)

    v1 = cartesian_velocity_from_celestial(ra1, dec1, r1, pmra1, pmdec1, rv1)
    v2 = cartesian_velocity_from_celestial(ra2, dec2, r2, pmra2, pmdec2, rv2)
    
    s = mag(sub(v2, v1))

    # note that abs(ds_vx1) == abs(ds_vx2), so we can use same expression
    # for both since squared in error propagation also, 1/s is already
    # taken outside (see return statement)
    ds_dvx = (v2[0] - v1[0])
    ds_dvy = (v2[1] - v1[1])
    ds_dvz = (v2[2] - v1[2])

    return (1/s)*sqrt((ds_dvx*v1_error[0])**2 + (ds_dvy*v1_error[1])**2 + (ds_dvz*v1_error[2])**2 + 
                      (ds_dvx*v2_error[0])**2 + (ds_dvy*v2_error[1])**2 + (ds_dvz*v2_error[2])**2)
