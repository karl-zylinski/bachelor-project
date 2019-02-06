import math

age_yr = 5*10^9 # 5 billion
age_sec = age_yr * 365.25 * 24 * 3600
max_sep = 3.08567758 * math.pow(10, 13) # 1pc in km
vel = 100 # km/s
dist_travelled = age_sec * vel

# separation_dist = angle * distance_travelled

angle = (max_sep / dist_travelled) * (math.pi/180)
print("for vel %f km/s: %f deg" % (vel, angle))
