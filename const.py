import math

deg_to_rad = math.pi/180
rad_to_deg = 180/math.pi
year_to_sec = 365.25 * 24 * 3600
mas_to_deg = 1.0/3600000.0
mas_per_yr_to_rad_per_s = (mas_to_deg*deg_to_rad)/year_to_sec
parsec_to_km = 3.08567758 * math.pow(10, 13)