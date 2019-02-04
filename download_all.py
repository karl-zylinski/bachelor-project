import urllib.request
import threading
import time
import os

source_repo = "http://cdn.gea.esac.esa.int/Gaia/gdr2/gaia_source_with_rv/csv/"
md5_file = "MD5SUM.txt"
dest_dir = "gaia_source_rv/"

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

def download_file(line):
    sl = line.split()
    md5sum = sl[0]
    filename = sl[1]

    if (os.path.isfile(filename)):
        print("Skipping " + filename + ", already exists")
        return

    print("Downloading " + filename)
    urllib.request.urlretrieve(source_repo + filename, dest_dir + filename)

urllib.request.urlretrieve(source_repo + md5_file, dest_dir + md5_file)
filenames_and_md5s = open(dest_dir + md5_file, "r")
line = filenames_and_md5s.readline()
while(line):
    while(threading.active_count() > 4):
        time.sleep(0.001)
    thread = threading.Thread(target = download_file, kwargs={"line": line})
    thread.start()
    line = filenames_and_md5s.readline()

filenames_and_md5s.close()