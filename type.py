import os
import sys

def verify_arguments():
    if len(sys.argv) != 3:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: type.py file limit"
fh = open(sys.argv[1])
data = fh.read(int(sys.argv[2]))
fh.close()

print(data)