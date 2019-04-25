# Author: Karl Zylinski, Uppsala University

# Tools for working with MIST isochrones

from functools import reduce
import pickle

def _is_comment(line):
    for c in line:
        if not c.isspace():
            return c == "#"

    return False

def _is_whitespace(line):
    for c in line:
        if not c.isspace():
            return False

    return True

def parse_isochrones(path):
    columns = ["EEP","log10_isochrone_age_yr","initial_mass","star_mass","log_Teff","log_g","log_L","[Fe/H]_init","[Fe/H]","Bessell_U","Bessell_B","Bessell_V","Bessell_R","Bessell_I","2MASS_J","2MASS_H","2MASS_Ks","Kepler_Kp","Kepler_D51","Hipparcos_Hp","Tycho_B","Tycho_V","Gaia_G_DR2Rev","Gaia_BP_DR2Rev","Gaia_RP_DR2Rev","Gaia_G_MAW","Gaia_BP_MAWb","Gaia_BP_MAWf","Gaia_RP_MAW","TESS","phase"]
    i_age = columns.index("log10_isochrone_age_yr")
    fh = open(path, 'r')
    line = fh.readline()

    cur_isochrone = []
    all_isochrones = []
    cur_age = -1

    while line:
        if len(line) == 0 or _is_whitespace(line) or _is_comment(line):
            line = fh.readline()
            continue

        data = list(map(lambda x: float(x), line.split()))
        age = data[i_age]
        if age != cur_age:
            ic = {}
            ic["columns"] = columns
            ic["age"] = cur_age
            ic["data"] = cur_isochrone
            cur_isochrone = []
            all_isochrones.append(ic)

        cur_age = age
        cur_isochrone.append(data)
        line = fh.readline()

    return all_isochrones

def save_isochrones(isos, path):
    f = open(path, "wb")
    pickle.dump(isos, f)
    f.close()

def load_isochrones(path):
    f = open(path, "rb")
    iso = pickle.load(f)
    f.close()
    return iso