# metadata for raw_db

import os

def get(db_folder):
    metadata_filename = "%s/metadata" % db_folder
    assert os.path.isfile(metadata_filename), "metadata mising: %s" % metadata_filename
    metadata_fh = open(metadata_filename, "r")
    metadata = metadata_fh.readlines()
    metadata_fh.close()
    metadata_dict = {}

    for mdi in metadata:
        key_value_pair = mdi.split(":")

        if len(key_value_pair) != 2:
            error("metadata in %s is of incorrect format" % db_folder)

        metadata_dict[key_value_pair[0]] = eval(key_value_pair[1])

    return metadata_dict