# Author: Karl Zylinski, Uppsala University

# Parses all isochrones and dumps to disk

import os
import mist

for file in os.listdir("isochrones"):
    if not file.endswith(".iso.cmd"):
        continue

    output_name = file[0:-4]
    iso = mist.parse_isochrones("isochrones/%s" % file)
    mist.save_isochrones(iso, "isochrones/%s" % output_name)
