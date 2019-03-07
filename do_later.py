# Author: Karl Zylinski, Uppsala University

# Do thing x after y seconds

import sys
import time
import os
import utils_str

def verify_arguments():
    if len(sys.argv) != 3:
        return False

    return True

assert verify_arguments(), "Usage: do_later.py command seconds"

cmd = sys.argv[1]
t = utils_str.to_int(sys.argv[2])

assert t != None, "Incorrect time supplied"

time.sleep(t)
os.system(cmd)