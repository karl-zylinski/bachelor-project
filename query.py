import sys
import datetime
import sqlite3

db_name = "gaia_dr2_2019-02-08-21-46-12.db"
q = sys.argv[1]

conn = sqlite3.connect(db_name)
res = conn.execute(q).fetchall()
conn.close()

output_name = datetime.datetime.now().strftime("query-result-" + db_name + "-%Y-%m-%d-%H-%M-%S.txt")
print("Saving result to %s" % output_name)

file = open(output_name, "w")
file.write(q + "\n\n")
file.write(str(res))
file.close()