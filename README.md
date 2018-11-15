# Music Sync Collection

This Collection is used to sync music from my banshee library with my server and from there with my smartphones (acrosync) and my online music library (koel)

## Syncing Banshee to m3u Playlists

First install the requirements:

```
pip install -r reqirements.txt
```

Then decide which playlists you want to sync and add them to the `playlists.json` and create a folder for your music files. The path to the folder needs also to be in the `playlists.json`.

now call `./banshee_to_m3u.py`.

This script will create m3u Playlists and Folders and hardlinks the original music files in these folders (using hashed names to avoid cross filesystem problems in naming).

## Syncing the music folder with your server

This can be done using rsync and an ssh connection.
Edit the `sync-music.sh` script to setup your paths.

## Sync the m3u files with your koel database

If you use koel in docker, you can build your custom docker image using the Dockerfile in the `koel` folder. You might need to change the database credentials in the `./koel/m3usync/m3usync.py` file.

It assumes that your media lives in `/media`. Feel free to change it.

**!** Only works with relative paths in the m3u files.

# License

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.

# Credits

Partially based on work of Florian Heinle from 2010
