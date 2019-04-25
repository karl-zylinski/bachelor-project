# Author: Karl Zylinski, Uppsala University

# Cuts out the part of a comoving-groups-file that overlaps with GALAH spatially.
# I.e. keeps only |b| > 10 and dec < 10

import os
import sys
import utils_dict

def verify_arguments():
    if len(sys.argv) < 3:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    if not os.path.isfile(sys.argv[2]):
        return False

    if os.path.isfile(sys.argv[3]):
        return False

    return True

assert verify_arguments(), "Usage: found_groups_combine_with_galah_dr3.py input_cms input_galah_csv output_cms"
input_cms = sys.argv[1]
input_galah_csv = sys.argv[2]
output_filename = sys.argv[3]

cg = utils_dict.read(input_cms)
cols = cg["columns"]

i_source_id = cols.index("source_id")
galah_cols = ["GaiaID","tmassID","GalahID","teff","eteff","logg","elogg","feh","efeh"]
galah_cols_data_types = ['integer', 'text', 'integer', 'real', 'real', 'real', 'real', 'real', 'real']
i_source_id_galah = galah_cols.index("GaiaID")
galah_data = {}
csv_fh = open(input_galah_csv, "r")
csv_lines = csv_fh.readlines()
csv_fh.close()

for i in range(1, len(csv_lines)): # skip header line
    csv_line = csv_lines[i]

    if csv_line[0] == "#":
        continue

    source_values = csv_line.split(",")

    if len(source_values) != len(galah_cols):
        continue

    source_values_with_dt = []
    for i in range(0, len(source_values)):
        dt = galah_cols_data_types[i]
        sv = source_values[i].strip()

        if sv == 'NULL':
            source_values_with_dt.append(None)
        elif dt == 'integer':
            source_values_with_dt.append(int(sv))
        elif dt == 'text':
            source_values_with_dt.append(sv)
        elif dt == 'real':
            source_values_with_dt.append(float(sv))
        else:
            exit("unknown datatype")

    sid = source_values_with_dt[i_source_id_galah]
    gd_for_sid = galah_data.get(sid)

    if gd_for_sid == None:
        gd_for_sid = []
        galah_data[sid] = gd_for_sid

    gd_for_sid.append(source_values_with_dt)

combined = cg.copy()
combined["groups"] = []

for g in cg["groups"]:
    new_group_stars = []
    contains_match = False

    for s in g["stars"]:
        sid = s[i_source_id]
        galah_matches = galah_data.get(sid)

        if galah_matches != None:
            contains_match = True
            break

    if contains_match:
        for s in g["stars"]:
            sid = s[i_source_id]
            galah_matches = galah_data.get(sid)

            if galah_matches == None:
                data = list(s)
                none_data = [None] * (len(galah_cols) - 1) # we do not keep gaia id from galah cols
                data.extend(none_data)
                new_group_stars.append(data)
                continue

            for galah_match in galah_matches:
                data = list(s)
                data.extend(galah_match[1:])
                new_group_stars.append(data)

    if len(new_group_stars) == 0:
        continue

    new_group = {}
    new_group["id"] = g["id"]
    new_group["stars"] = new_group_stars
    new_group["size"] = len(new_group_stars)
    combined["groups"].append(new_group)

combined["columns"].extend(galah_cols[1:])
combined["columns_datatypes"].extend(galah_cols_data_types[1:])
utils_dict.write(combined, output_filename)

