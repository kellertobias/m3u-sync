import mysql.connector
import glob

sql = mysql.connector.connect(host='127.0.0.1', database='koel-database', user='koel-user', password='koel-password').cursor()

try:
   sql.execute('ALTER TABLE playlist ADD COLUMN m3ufile CHAR(255) CHARACTER SET utf8 COLLATE utf8_bin');
except Exception as e:
   print(e)

sql.execute('DELETE FROM playlist WHERE m3ufile IS NOT NULL')

for m3ufile in glob.glob("/media/*.m3u"):
   print("Importing: %s" % m3ufile)

print("Synced!")