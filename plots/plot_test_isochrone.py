import sys
sys.path.append('..')
import matplotlib.pyplot as plt
import mist

mists = mist.parse_isochrones("../MIST_iso_5c76ac8ba0821.iso.cmd")

for miso in mists:
    lteff = []
    g = []
    i_lteff = miso["columns"].index("log_Teff")
    i_g = miso["columns"].index("Gaia_G_MAW")

    for d in miso["data"]:
        lteff.append(d[i_lteff])
        g.append(d[i_g])

    plt.plot(lteff, g)
    plt.xlabel('T_eff')
    plt.ylabel('G')

plt.show()
