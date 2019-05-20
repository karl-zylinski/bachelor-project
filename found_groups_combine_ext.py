# Author: Karl Zylinski, Uppsala University

# Cuts out the part of a comoving-groups-file that overlaps with lamost spatially.
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

    return True

assert verify_arguments(), "Usage: found_groups_combine_with_lamost_dr3.py input_cms input_lamost_csv"
input_cms = sys.argv[1]
input_lamost_csv = sys.argv[2]

cg = utils_dict.read(input_cms)
cols = cg["columns"]

i_source_id = cols.index("source_id")
lamost_cols = ["angDist","_RAJ2000","_DEJ2000","LAMOST","RAJ2000","DEJ2000","Teff","e_Teff","log(g)","e_log(g)","[Fe/H]","e_[Fe/H]","Vmag","gmag","Ksmag","W2mag","r_E(B-V)","E(B-V)","r_pmRA","pmRA","pmDE","RVel","Vphi","Dist","e_Dist","sng","CaHK","Hbeta","Mg2","Mgb","NaD","CEMP","DR4","UCAC4","Link2","Gaia","SDSS","Sloan","2M","ra_epoch2000","dec_epoch2000","errHalfMaj","errHalfMin","errPosAng","source_id","ra","ra_error","dec","dec_error","parallax","parallax_error","pmra","pmra_error","pmdec","pmdec_error","duplicated_source","phot_g_mean_flux","phot_g_mean_flux_error","phot_g_mean_mag","phot_bp_mean_flux","phot_bp_mean_flux_error","phot_bp_mean_mag","phot_rp_mean_flux","phot_rp_mean_flux_error","phot_rp_mean_mag","bp_rp","radial_velocity","radial_velocity_error","rv_nb_transits","teff_val","a_g_val","e_bp_min_rp_val","radius_val","lum_val"]
i_source_id_lamost = lamost_cols.index("source_id")
lamost_sids = set()
csv_fh = open(input_lamost_csv, "r")
csv_lines = csv_fh.readlines()
csv_fh.close()

for i in range(1, len(csv_lines)): # skip header line
    csv_line = csv_lines[i]

    if csv_line[0] == "#":
        continue

    source_values = csv_line.split(",")

    if len(source_values) != len(lamost_cols):
        continue

    sid = int(source_values[i_source_id_lamost])
    lamost_sids.add(sid)

combined = cg.copy()
combined["groups"] = []

for g in cg["groups"]:
    new_group_stars = []
    contains_match = False

    for s in g["stars"]:
        sid = s[i_source_id]

        if sid in lamost_sids:
            print(sid)

