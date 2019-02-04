import threading
import time
import hashlib
import os

md5_file = "MD5SUM.txt"
dest_dir = "gaia_source_rv/"

print("Chcecking in " + dest_dir)

def md5check(file, md5hash):
    fh = open(file,"rb")
    data = fh.read()
    fh.close()
    m = hashlib.md5(data)
    md5hash_file = m.hexdigest()
    return md5hash_file == md5hash

def check_file(line):
    sl = line.split()
    md5sum = sl[0]
    filename = sl[1]

    if not os.path.isfile(dest_dir + filename):
        print("MISSING: " + filename)
        return

    if not md5check(dest_dir + filename, md5sum):
        print("WRONG MD5 " + filename)

filenames_and_md5s = open(dest_dir + md5_file, "r")
line = filenames_and_md5s.readline()
i = 0
start_at = 0

while (i < start_at):
    i = i + 1
    filenames_and_md5s.readline()

while(line):
    while(threading.active_count() > 12):
        time.sleep(0.005)
    thread = threading.Thread(target = check_file, kwargs={"line": line})
    thread.start()
    line = filenames_and_md5s.readline()

    if i%100 == 0:
        print(str(i) + " files checked")
        
    i = i + 1

filenames_and_md5s.close()