# Author: Karl Zylinski, Uppsala University

def to_int(str):
    try:
        return int(str)
    except ValueError:
        return None

def to_float(str):
    try:
        return float(str)
    except ValueError:
        return None