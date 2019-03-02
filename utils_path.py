def remove_extension(path):
    ext_sep = path.rfind(".")

    if ext_sep == -1:
        return path

    return path[0:ext_sep]

def append(path, item):
    if len(path) == 0:
        return item

    if path[-1] == "/":
        return "%s%s" % (path, item)

    return "%s/%s" % (path, item)