# Author: Karl Zylinski, Uppsala University

# Compares lines of two different files, seeing if the lines exist in both (does
# not need to be in the same order)

import sys
import os

assert len(sys.argv) == 3, "Usage: compare_lines.py file1 file2"

file1 = sys.argv[1]
file2 = sys.argv[2]

assert os.path.isfile(file1) and os.path.isfile(file2), "One input argument is not a file"

l1fh = open(file1)
l1 = set(l1fh.readlines())
l1fh.close()

l2fh = open(file2)
l2 = set(l2fh.readlines())
l2fh.close()

unique_to_l1 = l1.difference(l2)
unique_to_l2 = l2.difference(l1)
print("Unique to %s: %d out of %d" % (file1, len(unique_to_l1), len(l1)))
print("Unique to %s: %d out of %d" % (file2, len(unique_to_l2), len(l2)))

print(unique_to_l2)