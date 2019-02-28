import sys
import os
import matplotlib.pyplot as plt
from statistics import mean

assert len(sys.argv) > 1, "Usage: find_avg_pos_in_found_groups.py file"
input_filename = sys.argv[1]
assert os.path.isfile(input_filename), "Supplied file does not exist"
input_fh = open(input_filename, 'rb')
found_groups = eval(input_fh.read())
input_fh.close()
assert type(found_groups) is list, "Supplied file has broken format"

found_groups.sort(key = lambda x: x["size"])
clusters = []

for fp in found_groups:
    size = fp["size"]
    if size < 10:
        continue

    avg_ra = 0
    avg_dec = 0
    avg_dist = 0

    for s in fp["stars"]:
        ra = s[1]
        dec = s[2]
        dist = s[7]
        avg_ra = avg_ra + ra
        avg_dec = avg_dec + dec
        avg_dist = avg_dist + dist

    avg_ra = avg_ra / size
    avg_dec = avg_dec / size
    avg_dist = avg_dist / size
    clusters.append((size, avg_ra, avg_dec, avg_dist))

clusters.sort(key = lambda x: x[3])

for c in clusters:
    print("Group of size %d pos (ra, dec, dist): (%f, %f, %f)" % (c[0], c[1], c[2], c[3]))
