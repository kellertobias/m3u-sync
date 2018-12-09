import mysql.connector
import glob
from os import path

userId = 1

sql = mysql.connector.connect(host='127.0.0.1', database='koel-database', user='koel-user', password='koel-password')
cursor = sql.cursor()

try:
   cursor.execute('ALTER TABLE playlists ADD COLUMN m3ufile VARCHAR(255) CHARACTER SET utf8 COLLATE utf8_bin');
except Exception:
   pass

cursor.execute('DELETE FROM playlists WHERE m3ufile IS NOT NULL')

for m3upath in glob.glob("/media/*.m3u"):
   m3uname = m3upath.split('.')
   if m3uname[len(m3uname) - 1 ] != 'm3u':
      continue
   del m3uname[len(m3uname) - 1 ]
   if m3uname[len(m3uname) - 1 ] == 'smart':
      del m3uname[len(m3uname) - 1 ]

   m3uname = ".".join(m3uname)
   m3uname = m3uname.split("/")
   m3uname = m3uname[len(m3uname) - 1]

   # Now we read the file
   print("Importing: %s \tfrom %s" % (m3uname, m3upath))
   cursor.execute('''
      INSERT INTO playlists(user_id, name, m3ufile) VALUES
      (%s, "%s", "%s")
   ''' % (userId, m3uname, m3upath))

   playlistId = cursor.lastrowid
   print (playlistId)

   songPaths = []
   with open(m3upath) as m3ufile:
      lines = m3ufile.readlines()
      for songPath in lines:
         songPath = songPath.strip()
         if songPath == '0':
            continue

         songPath = path.join("/media", songPath.strip())
         songPaths.append('"' + songPath + '"')

   cursor.execute("""
      INSERT INTO playlist_song(playlist_id, song_id) SELECT %s, id FROM songs WHERE path IN(%s)
   """ % (playlistId, ','.join(songPaths)))
         
   
   sql.commit()
   # cursor.close()
   # sql.close()

print("Done :)")
