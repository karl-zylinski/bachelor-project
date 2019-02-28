def to_int(str):
    try:
        return int(str)
    except ValueError:
        return None