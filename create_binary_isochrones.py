# Author: Karl Zylinski, Uppsala University

# Parses all isochrones and dumps to disk

import os
import mist

path = "isochrones/for_2330"
for file in os.listdir(path):
    if not file.endswith(".iso.cmd"):
        continue

    output_name = file[0:-4]
    iso = mist.parse_isochrones("%s/%s" % (path, file))
    mist.save_isochrones(iso, "%s/%s" % (path, output_name))
