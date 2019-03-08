# Author: Karl Zylinski, Uppsala University

# Some conversion constants

import math

deg_to_rad = math.pi/180
rad_to_deg = 1/deg_to_rad
year_to_sec = 365.256 * 24 * 3600
sec_to_year = 1/year_to_sec
mas_to_deg = 1.0/3600000.0
mas_per_yr_to_rad_per_s = (mas_to_deg*deg_to_rad)/year_to_sec
parsec_to_km = 3.08567758 * math.pow(10, 13)