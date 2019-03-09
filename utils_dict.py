# Author: Karl Zylinski, Uppsala University

import pickle

def get_or_error(d, key, err):
    val = d.get(key)
    assert val != None, err
    return val

def read(filename):
    fh = open(filename,"rb")
    groups_dict = pickle.load(fh)
    fh.close()
    return groups_dict

def write(groups_dict, filename):
    fh = open(filename, "wb")
    pickle.dump(groups_dict, fh)
    fh.close()