import sys
import os

assert len(sys.argv) > 1, "Usage: find_in_found_pairs.py file [size]"
input_filename = sys.argv[1]
assert os.path.isfile(input_filename), "Supplied file does not exist"
input_fh = open(input_filename, 'rb')
found_pairs = eval(input_fh.read())
input_fh.close()
assert type(found_pairs) is list, "Supplied file has broken format"

if len(sys.argv) == 3:
    input_size = int(sys.argv[2])
    for fp in found_pairs:
        if int(fp["size"]) == input_size:
            print(fp["stars"])
            dist = 0
            for s in fp["stars"]:
                dist = dist + s[7]
            dist = dist / len(fp["stars"])
            print()
            print("Distance: %f" % dist)
else:
    num_pairs_of_size = {}

    for fp in found_pairs:
        cur_num = num_pairs_of_size.get(fp["size"])
        if cur_num == None:
            num_pairs_of_size[fp["size"]] = 1
        else:
            num_pairs_of_size[fp["size"]] = cur_num + 1

    print()
    print("Found:")
    print("------")
    for size, num in num_pairs_of_size.items():
        print("%d of size %d" % (num, size))
