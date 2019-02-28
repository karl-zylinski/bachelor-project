#Author: Karl Zylinski, Uppsala University

# Compares lines of two different files, seeing if the lines exist in both (does
# not need to be in the same order)

import sys
import os

assert len(sys.argv) == 3, "Usage: compare_lines.py file1 file2"

file1 = sys.argv[1]
file2 = sys.argv[2]

assert os.path.isfile(file1) and os.path.isfile(file2), "One input argument is not a file"

l1fh = open(file1)
l1 = l1fh.readlines()
l1fh.close()

l2fh = open(file2)
l2 = l2fh.readlines()
l2fh.close()

matches = 0
for l1item in l1:
    for l2item in l2:
        if l2item == l1item:
            matches = matches + 1
            break

print("%d/%d" % (matches, len(l1)))