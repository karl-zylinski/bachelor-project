import sys
import os
import numpy
import matplotlib.pyplot as plt
import mist
import comoving_groups

def verify_arguments():
    if len(sys.argv) != 3:
        return False

    if not os.path.isfile(sys.argv[1]):
        return False

    return True

assert verify_arguments(), "Usage: plot_comoving_groups_against_isochrones.py group_file age"

cg = comoving_groups.read(sys.argv[1])
age = float(sys.argv[2])
log10_age = numpy.log10(age)
isos = {}

for i in numpy.arange(0, 4.5, 0.5):
    iso_path = "isochrones/feh-%.1f.iso.cmd" % i
    isos[-i] = mist.parse_isochrones(iso_path)

cg_cols = cg["columns"]
i_teff_cg = cg_cols.index("teff_val")
i_lum_cg = cg_cols.index("lum_val")

gaia_lteff = []
gaia_lums = []

for g in cg["groups"]:
    if g["size"] != 2:
        continue

    for s in g["stars"]:
        if s[i_teff_cg] == None or s[i_lum_cg] == None:
            continue

        gaia_lteff.append(numpy.log10(s[i_teff_cg]))
        gaia_lums.append(numpy.log10(s[i_lum_cg]))


plt.plot(gaia_lteff, gaia_lums, '.', markersize=2)

for metallicty, isos_by_age in isos.items():
    iso_lteff = []
    iso_lum = []

    isochrone_to_use = None

    for iso in isos_by_age:
        if iso["age"] >= log10_age:
            isochrone_to_use = iso
            break

    i_lteff_iso = isochrone_to_use["columns"].index("log_Teff")
    i_lum_iso = isochrone_to_use["columns"].index("log_L")

    for d in isochrone_to_use["data"]:
        iso_lteff.append(d[i_lteff_iso])
        iso_lum.append(d[i_lum_iso])

    plt.plot(iso_lteff, iso_lum)

plt.xlabel('log T_eff')
plt.ylabel('log L/L_sun')
plt.legend(["Data", "Fe/H 0", "Fe/H -0.5", "Fe/H -1", "Fe/H -1.5", "Fe/H -2", "Fe/H -2.5", "Fe/H -3", "Fe/H -3.5", "Fe/H -4"])
plt.gca().invert_xaxis()
plt.show()