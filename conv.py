# Author: Karl Zylinski, Uppsala University

# Some conversion constants

import math

deg_to_rad = math.pi/180
rad_to_deg = 1/deg_to_rad
as_pc_per_year_to_km_per_s = 4.74039259031668
year_to_sec = 365.256 * 24 * 3600
sec_to_year = 1/year_to_sec
mas_to_deg = 1.0/3600000.0
mas_per_yr_to_deg_per_s = mas_to_deg/year_to_sec
mas_per_yr_to_rad_per_s = mas_per_yr_to_deg_per_s * deg_to_rad
parsec_to_km = 3.08567758 * 10000000000000