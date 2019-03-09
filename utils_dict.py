# Author: Karl Zylinski, Uppsala University

def get_or_error(d, key, err):
    val = d.get(key)
    assert val != None, err
    return val