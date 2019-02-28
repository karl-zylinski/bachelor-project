# Author: Karl Zylinski

# Takes a random sample from source_dir and throws it into source_partial_dir

import os
import random
import shutil

source_dir = "gaia_source"
source_partial_dir = "gaia_source_partial"

csvs = []
for file in os.listdir(source_dir):
    if not file.endswith(".csv"):
        continue

    csvs.append(file)

to_copy = []
for i in range(0, 1000):
    while True:
        r = random.randint(0, len(csvs))
        if csvs[r] not in to_copy:
            to_copy.append(csvs[r])
            break

for c in to_copy:
    shutil.copyfile("%s/%s" % (source_dir, c), "%s/%s" % (source_partial_dir, c))





