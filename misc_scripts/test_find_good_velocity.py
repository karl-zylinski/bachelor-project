import math

age_yr = 10*10^9 # 10 billion
age_sec = age_yr * 365.25 * 24 * 3600
max_sep = 3.08567758 * math.pow(10, 13) # 3pc in km
vel = 10 # km/s
dist_travelled = age_sec * vel

# separation_dist = angle * distance_travelled

angle = (max_sep / dist_travelled) * (math.pi/180)
print("for vel %f km/s: %f deg" % (vel, angle))
