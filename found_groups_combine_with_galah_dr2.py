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
galah_cols = ["star_id","sobject_id","gaia_dr2_id","ndfclass","field_id","raj2000","dej2000","jmag","hmag","kmag","vmag_jk","e_jmag","e_hmag","e_kmag","snr_c1","snr_c2","snr_c3","snr_c4","rv_synt","e_rv_synt","rv_obst","e_rv_obst","rv_nogr_obst","e_rv_nogr_obst","chi2_cannon","sp_label_distance","flag_cannon","teff","e_teff","logg","e_logg","fe_h","e_fe_h","vmic","e_vmic","vsini","e_vsini","alpha_fe","e_alpha_fe","li_fe","e_li_fe","flag_li_fe","c_fe","e_c_fe","flag_c_fe","o_fe","e_o_fe","flag_o_fe","na_fe","e_na_fe","flag_na_fe","mg_fe","e_mg_fe","flag_mg_fe","al_fe","e_al_fe","flag_al_fe","si_fe","e_si_fe","flag_si_fe","k_fe","e_k_fe","flag_k_fe","ca_fe","e_ca_fe","flag_ca_fe","sc_fe","e_sc_fe","flag_sc_fe","ti_fe","e_ti_fe","flag_ti_fe","v_fe","e_v_fe","flag_v_fe","cr_fe","e_cr_fe","flag_cr_fe","mn_fe","e_mn_fe","flag_mn_fe","co_fe","e_co_fe","flag_co_fe","ni_fe","e_ni_fe","flag_ni_fe","cu_fe","e_cu_fe","flag_cu_fe","zn_fe","e_zn_fe","flag_zn_fe","y_fe","e_y_fe","flag_y_fe","ba_fe","e_ba_fe","flag_ba_fe","la_fe","e_la_fe","flag_la_fe","eu_fe","e_eu_fe","flag_eu_fe"]
galah_cols_data_types = ["text","integer","integer","text","integer","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real","real"]
i_source_id_galah = galah_cols.index("gaia_dr2_id")
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
    for j in range(0, len(source_values)):
        dt = galah_cols_data_types[j]
        sv = source_values[j].strip()

        if sv == '':
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
    new_groups_stars = []

    for s in g["stars"]:
        sid = s[i_source_id]
        galah_matches = galah_data.get(sid)

        if galah_matches == None:
            continue

        for galah_match in galah_matches:
            data = list(s)
            data.extend(galah_match[1:])
            new_groups_stars.append(data)

    if len(new_groups_stars) == 0:
        continue

    new_group = {}
    new_group["stars"] = new_groups_stars
    new_group["size"] = len(new_groups_stars)
    combined["groups"].append(new_group)

combined["columns"].extend(galah_cols[1:])
combined["columns_datatypes"].extend(galah_cols_data_types[1:])
utils_dict.write(combined, output_filename)