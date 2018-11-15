#!/bin/bash
#

rsync \
--ignore-existing \
--info=progress2 \
--stats \
--human-readable \
--archive \
--compress \
-e ssh ~/.musicsync user@server:~/music

rsync \
--info=progress2 \
--stats \
--human-readable \
--archive \
--compress \
--include="*.m3u" \
-e ssh ~/.musicsync user@server:~/music
