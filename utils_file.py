def remove_extension(path):
    ext_sep = path.rfind(".")

    if ext_sep == -1:
        return path

    return path[0:ext_sep]