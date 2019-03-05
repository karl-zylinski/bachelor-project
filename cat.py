#Author: Karl Zylinski, Uppsala University

# Compares lines of two different files, seeing if the lines exist in both (does
# not need to be in the same order)

import sys
import os

assert len(sys.argv) == 4, "Usage: cat.py file1 file2 out_file"

file1 = sys.argv[1]
file2 = sys.argv[2]
out_file = sys.argv[3]

assert os.path.isfile(file1) and os.path.isfile(file2) and not os.path.isfile(out_file), "One input argument is not a file"

l1fh = open(file1)
l1 = l1fh.read()
l1fh.close()

l2fh = open(file2)
l2 = l2fh.read()
l2fh.close()

out = l1 + l2

out_fh = open(out_file, "w")
out_fh.write(out)
out_fh.close()
