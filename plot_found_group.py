import sys
import os
import matplotlib.pyplot as plt
from statistics import mean

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
            ras = []
            decs = []
            mags = []
            avg_ra = 0
            avg_dec = 0
            brightest = 1000 # mag
            dimmest = -1000 # mag

            stars = fp["stars"]
            stars.sort(key = lambda x: x[8], reverse = True)
        
            for s in fp["stars"]:
                ra = s[1]
                dec = s[2]
                mag = s[8]
                avg_ra = avg_ra + ra
                avg_dec = avg_dec + dec
                ras.append(ra)
                decs.append(dec)
                mags.append(mag)
                if mag > dimmest:
                    dimmest = mag
                if mag < brightest:
                    brightest = mag

            avg_ra = mean(ras)
            avg_dec = mean(decs)
            print("Average pos: %f %f" % (avg_ra, avg_dec))

            sizes = []

            for m in mags:
                mn = (m - brightest)/(dimmest-brightest)
                sizes.append(((1-mn) + 0.25) * 100)

            cm = plt.cm.get_cmap('RdYlBu')
            sc = plt.scatter(ras, decs, c=mags, vmin=dimmest, vmax=brightest, s=sizes, cmap=cm)
            plt.colorbar(sc)
            plt.xlabel("ra")
            plt.ylabel("dec")
            plt.show()
            exit()
