#!/usr/bin/env python2
# -*- coding:utf-8 -*-

""" export playlists from Banshee to m3u files

What this script does is read banshee playlists and copy song files
to a flat directory. Additionally, an m3u file is created to preserve
user selected ordering of playlists

This version was modified and brought to you by Tobias Keller

Original Copyright (c) 2010 Florian Heinle <launchpad@planet-tiax.de>
"""

# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.


from sqlalchemy import create_engine
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relation
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

from urllib import unquote
from shutil import copy
from inspect import getmembers

import binascii

import shutil
import json
import ctypes

import codecs

import sys
import os
import unicodedata

import pprint

banshee_db = os.path.expanduser('~/.config/banshee-1/banshee.db')
engine = create_engine('sqlite:///%s' % banshee_db)
Session = sessionmaker(bind=engine)

Base = declarative_base()

import sys
import chardet

IS_PY2 = sys.version_info < (3, 0)
if not IS_PY2:
   # Helper for Python 2 and 3 compatibility
   unicode = str

def make_compat_str(in_str):
   """
   Tries to guess encoding of [str/bytes] and decode it into
   an unicode object.
   """
   assert isinstance(in_str, (bytes, str, unicode))
   if not in_str:
      return unicode()

   # Chardet in Py2 works on str + bytes objects
   if IS_PY2 and isinstance(in_str, unicode):
      return in_str

   # Chardet in Py3 works on bytes objects
   if not IS_PY2 and not isinstance(in_str, bytes):
      return in_str

   # Detect the encoding now
   enc = chardet.detect(in_str)

   # Decode the object into a unicode object
   out_str = in_str.decode(enc['encoding'])

   # Cleanup: Sometimes UTF-16 strings include the BOM
   if enc['encoding'] == "UTF-16BE":
      # Remove byte order marks (BOM)
      if out_str.startswith('\ufeff'):
         out_str = out_str[1:]

   # Return the decoded string
   return out_str


class Track(Base):
	"""Track in Banshee's database

	contains Uris instead of filenames and is referenced from
	PlaylistEntry"""
	__tablename__ = 'CoreTracks'

	TrackID = Column(Integer, primary_key=True)
	ArtistID = Column(Integer)
	Uri = Column(String)
	Title = Column(String)

	def __init__(self, **kwargs):
		for key, value in kwargs:
			setattr(self, key, value)

	def __repr__(self):
		return "<Track('%s')>" % self.Title.encode('utf-8')

class Playlist(Base):
	"""Playlist in Banshee's database

	contains not much more than Playlist Names and provides an ID for 
	reference by PlaylistEntry"""
	__tablename__ = 'CorePlaylists'

	PlaylistID = Column(Integer, primary_key=True)
	Name = Column(String)
	Special = Column(Integer)

	def __init__(self, **kwargs):
		for key, value in kwargs:
			setattr(self, key, value)

	def __repr__(self):
		return "<Playlist('%s', id '%s')>" % (self.Name.encode('utf-8'),
											  self.PlaylistID)

class SmartPlaylist(Base):
	"""SmartPlaylist in Banshee's database

	contains not much more than Playlist Names and provides an ID for 
	reference by SmartPlaylistEntry"""
	__tablename__ = 'CoreSmartPlaylists'

	SmartPlaylistID = Column(Integer, primary_key=True)
	Name = Column(String)

	def __init__(self, **kwargs):
		for key, value in kwargs:
			setattr(self, key, value)

	def __repr__(self):
		return "<Playlist('%s', id '%s')>" % (self.Name.encode('utf-8'),
											  self.SmartPlaylistID)

class PlaylistEntry(Base):
	"""PlaylistEntry in Banshee's database

	contains TrackID/PlaylistID pairs and their ordering in playlists"""
	__tablename__ = 'CorePlaylistEntries'

	EntryID = Column(Integer, primary_key=True)
	PlaylistID = Column(Integer, ForeignKey('CorePlaylists.PlaylistID'))
	TrackID = Column(Integer, ForeignKey('CoreTracks.TrackID'))
	ViewOrder = Column(Integer)

	playlist = relation(Playlist,
						order_by=ViewOrder,
						backref='playlist_tracks'
					   )
	track = relation(Track,
					 order_by=ViewOrder,
					 backref='track'
					)

	def __init__(self, **kwargs):
		for key, value in kwargs:
			setattr(self, key, value)

class SmartPlaylistEntry(Base):
	"""SmartPlaylistEntry in Banshee's database

	contains TrackID/PlaylistID pairs and their ordering in playlists"""
	__tablename__ = 'CoreSmartPlaylistEntries'

	EntryID = Column(Integer, primary_key=True)
	SmartPlaylistID = Column(Integer, ForeignKey('CoreSmartPlaylists.SmartPlaylistID'))
	TrackID = Column(Integer, ForeignKey('CoreTracks.TrackID'))

	playlist = relation(SmartPlaylist,
						backref='smart_playlist_tracks'
					   )
	track = relation(Track,
					 backref='smart_track'
					)

	def __init__(self, **kwargs):
		for key, value in kwargs:
			setattr(self, key, value)

def get_regular_playlists():
	"""return all user-created playlists, excepting play queues etc"""
	session = Session()
	session.flush = lambda: True #read only database
	playlists = session.query(Playlist).filter_by(Special=0)
	return playlists.all()

def get_special_playlists():
	"""return all user-created playlists, excepting play queues etc"""
	session = Session()
	session.flush = lambda: True #read only database
	playlists = session.query(SmartPlaylist)
	return playlists.all()

def get_song_uris_in_playlist(playlist_id):
	"""read playlist contents"""
	session = Session()
	query = session.query(PlaylistEntry).filter_by(PlaylistID=playlist_id)\
										.order_by(PlaylistEntry.ViewOrder) 
   
	# ...
	uris = [];
	for obj in query.all():
		if obj.track != None:
			uris.append(obj.track.Uri);
	# print "Printing done"
	# uris = [playlist_entry.track.Uri for playlist_entry in query.all()]
	return uris

def get_song_uris_in_smart_playlist(playlist_id):
	"""read playlist contents"""
	session = Session()
	query = session.query(SmartPlaylistEntry).filter_by(SmartPlaylistID=playlist_id)
   
	# ...
	uris = [];
	for obj in query.all():
		if obj.track != None:
			uris.append(obj.track.Uri);
	# print "Printing done"
	# uris = [playlist_entry.track.Uri for playlist_entry in query.all()]
	return uris
	
def strip_album_tags(song, new_album='Playlists'):
	"""replace album tags with a special new one

	this ensures that duplicate songs don't clutter mp3 players'
	album views"""
	song_file = EasyID3(song)
	song_file['album'] = new_album
	song_file.save()

def strip_accents(s):
	return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def umlaut(a):
	string = strip_accents(u""+a).encode('ascii','ignore');
	string = string.replace(',',' ')
	string = string.replace(';',' ')
	string = string.replace('\\',' ')
	string = string.replace(':',' ')
	return string

def create_link_song(source, base_folder):
	"""Make song Filename fitting to the database structure

	this ensures that duplicate songs don't clutter mp3 players'
	album views"""
	dest = "";

	try:
		song = source.decode(sys.getfilesystemencoding())
	except:
		song = make_compat_str(source)

	song = song.encode('ascii', 'ignore')

	song_file = {};
	try:
		song_file = EasyID3(song)
	except:
		song_file['artist'] = "Unknown";
		song_file['album']  = "Unknown";

	try:
		src = song
		target = base_folder


		try:
			artist = ''.join(song_file['artist']);
			if (artist == ""):
				artist = ''.join(song_file['author'])
			if (artist == ""):
				artist = ''.join(song_file['performer'])
			if (artist == ""):
				artist = ''.join(song_file['composer'])      
		except KeyError, exception_reason:
			artist = u"Unknown Artist"

		artist = (binascii.crc32(artist.encode('utf-8')) & 0xffffffff);
		artist = "%x" % (artist);

		target = os.path.join(target, artist);
		if not os.path.isdir(target):
			os.makedirs(target)


		try:
			album = ''.join(song_file['album']);    
		except KeyError, exception_reason:
			album = u"Unknown Album"

		album = (binascii.crc32(album.encode('utf-8')) & 0xffffffff);
		album = "%x" % (album);
		basename = os.path.basename(src);
		basename = basename.split(".");
		ext = (basename[-1:])[0].encode("utf-8");
		basename = u".".join(basename[:-1])
		basename = (binascii.crc32(basename.encode('utf-8')) & 0xffffffff)
		basename = "%x" % (basename);

		srcBasename = "%s-%s.%s" % (album, basename, ext);

		dest = dest + artist + "/" + srcBasename;

		print type(dest)
		print type(src)

		print u"{}\t{}".format(dest, src);

		os.link(src, os.path.join(target, srcBasename));

	except OSError, exception_reason:
		if exception_reason[1] == 'File exists':
			return dest;
		else:
			return 0 

	return dest;

def normalize_filename(uri):
	"""convert URIs used by banshee to normal filenames"""
	# TODO: support gvfs uris
	assert uri.startswith('file:///'), 'Only local files supported'
	filename = unquote(uri.encode(sys.getfilesystemencoding())[7:])
	return filename
def utf8(str):
	  return unicode(str, 'latin1').encode('utf-8')

def getTimeDisp(time):
	timeDispSecs  = int(time) % 60;
	timeDispMins  = int(time/60);
	timeDispHours = int(timeDispMins/60)
	timeDispMins  = timeDispMins % 60;

	timeDispSecsStr = str(timeDispSecs);
	if timeDispSecs < 10:
		timeDispSecsStr = "0" + str(timeDispSecs);

	timeDispMinsStr = str(timeDispMins);
	if timeDispMins < 10:
		timeDispMinsStr = "0" + str(timeDispMins);

	timeDispHoursStr = str(timeDispHours);
	if timeDispHours < 10:
		timeDispHoursStr = "0" + str(timeDispHours);

	timeDisp = "" + str(timeDispMinsStr) + ":" + str(timeDispSecsStr);

	if timeDispHours > 0:
		timeDisp = timeDispHoursStr + ":" + timeDisp;

	return timeDisp;

def print_playlist(playlist_id): 
	playlist = get_song_uris_in_playlist(playlist_id)

	count = 0;
	time = 0.0;
	print ' #No.', '%s' % "Title".ljust(50,"-"), '%s' % "Artist".ljust(38,"-"), '%s' % "Genre".ljust(20,"-"), '%10s'%"Duration", '%12s'%"Start";
	for track in playlist: 
		count = count +1;
		song = normalize_filename(track).decode(sys.getfilesystemencoding())
		song_file = {};
		try:
			genre = "Generic";
			artist = "Unknown Artist";
			title = "Unknown Title";

			try:
				song_file = EasyID3(song);
				if 'title' in song_file:
					title  = song_file['title'][0][0:45];
				
				if 'artist' in song_file:
					artist  = song_file['artist'][0][0:33];
				
				if 'genre' in song_file:
					genre  = song_file['genre'][0][0:15];
			except:
				title = os.path.splitext(os.path.basename(song))[0][0:45];

			try:
				audio = MP3(song);
			except:
				audio;

			titleLengthStr = getTimeDisp(audio.info.length)
			timeDisp = getTimeDisp(time);

			print '%4d ' % count, '%s' % title.ljust(50), '%s' % artist.ljust(38), '%s' % genre.ljust(20), '%10s' % titleLengthStr, '%12s'%timeDisp;
			time = time + audio.info.length;
		except Exception as inst: 
			print type(inst)     # the exception instance
			print inst.args      # arguments stored in .args
			print inst           # __str__ allows args to printed directly
			x, y = inst          # __getitem__ allows args to be unpacked directly
			print 'x =', x
			print 'y =', y
	timeDisp = getTimeDisp(time);
	print '   # ', '%s' % "Total Time:".rjust(121, "-"),  '%12s'%timeDisp;

	return count;

def save_playlist(playlist_id, target, playlist_file_name, verbose=False):
	"""save songs from a playlist to a directory and write m3u file"""
	if not os.path.isdir(target):
		os.makedirs(target)
	playlist = get_song_uris_in_playlist(playlist_id)
	playlist_fname = os.path.join(target, '%s.m3u' % playlist_file_name)
	playlist_file = codecs.open(playlist_fname, 'w', "utf8")
	count = 0;
	for track in playlist: 
		source = normalize_filename(track)
		try:
			song_file = create_link_song(source, target)
			m3u_file_line = song_file
			count = count +1;
		except IOError, exception_reason:
			if exception_reason[1] == 'No such file or directory':
				msg = 'Error: File not found "%s"' % source
				print >> sys.stderr, msg
				continue
			else:
				raise
		if not(type(m3u_file_line) is int):
			playlist_file.write("" + m3u_file_line + '\n')
			if verbose:
				print "Added %s" % m3u_file_line
	playlist_file.close()
	return count;

def save_smart_playlist(playlist_id, target, playlist_file_name, verbose=False):
	"""save songs from a playlist to a directory and write m3u file"""
	if not os.path.isdir(target):
		os.makedirs(target)
	playlist = get_song_uris_in_smart_playlist(playlist_id)
	playlist_fname = os.path.join(target, '%s.smart.m3u' % playlist_file_name)
	playlist_file = codecs.open(playlist_fname, 'w', "utf8")

	count = 0;

	for track in playlist: 
		source = normalize_filename(track)
		try:
			song_file = create_link_song(source, target)
			m3u_file_line = song_file
			count = count +1;
		except IOError, exception_reason:
			if exception_reason[1] == 'No such file or directory':
				msg = 'Error: File not found "%s"' % source
				print >> sys.stderr, msg
				continue
			else:
				raise
		playlist_file.write("%s\n" % m3u_file_line)
		if verbose:
			print "Added %s" % m3u_file_line
	playlist_file.close()
	return count;

def main(argv=[]):
	argv = argv or sys.argv[1:]
	import optparse
	parser = optparse.OptionParser()
	parser.add_option('-v', '--verbose', dest='verbose', default=False,
					  help='Print all files while copying',
					  action='store_true')
	parser.add_option('-l', '--list', dest='listit',
					  help='List the Elements', default=0,
					  action='store_true')
	parser.add_option('-p', '--playlength', dest='showlist',
					  help='Get length of one Playlist', default=0,
					  action='store_true')
	(options, args) = parser.parse_args(argv)

	print "Usage: b2m3u.py \n -l: list all Playlists\n -v: verbose output\n -p: print playlist \n modified by Tobias Keller (tokemedia.de)"

	with open('playlists.json') as data_file:    
		data = json.load(data_file)

	sync_lists 	= data["playlists"]
	aim_dir 	= data["folder"]
	aim_dir 	= os.path.expanduser(aim_dir)

	if not options.listit:
		for the_file in os.listdir(os.path.expanduser(aim_dir)):
			file_path = os.path.join(os.path.expanduser(aim_dir), the_file)
			try:
				if os.path.isfile(file_path):
					os.unlink(file_path)
				else:
					shutil.rmtree(file_path);
			except Exception, e:
				print e

	print 'Banshee playlists:'
	print 'ID: | Name:'
	print "### Usual Playlists"
	for playlist in get_regular_playlists():
		#If Playlist should be synced
		if not options.listit and not options.showlist:
			if playlist.Name in sync_lists:
				#Print name of List and Sync to folder
				session = Session()
				session.flush = lambda: True #read only database
				p = session.query(Playlist).filter_by(PlaylistID=playlist.PlaylistID).first().Name
				count = save_playlist(int(playlist.PlaylistID), os.path.expanduser(aim_dir), p,
							  verbose=options.verbose)
				print '%4d' % playlist.PlaylistID, '%40s'%playlist.Name, '(%4d Songs)' % count;
		else:
			print '%4d' % playlist.PlaylistID, '%40s'%playlist.Name, '(   ? Songs)';

	print "### Smart Playlists"
	if not options.showlist:
		for playlist in get_special_playlists():
			#If Playlist should be synced
			if not options.listit and not options.showlist:
				if playlist.Name in sync_lists:
					#Print name of List and Sync to folder
					session = Session()
					session.flush = lambda: True #read only database
					p = session.query(SmartPlaylist).filter_by(SmartPlaylistID=playlist.SmartPlaylistID).first().Name
					count = save_smart_playlist(int(playlist.SmartPlaylistID), os.path.expanduser(aim_dir), p,
								  verbose=options.verbose)
					print '%4d' % playlist.SmartPlaylistID, 'Smart' '%35s'%playlist.Name, '(%4d Songs)' % count;
			else:
				print '%4d' % playlist.SmartPlaylistID, 'Smart' '%35s'%playlist.Name, '(   ? Songs)';
	print "Done"

	if options.showlist:
		print "Which List do you want to display?";
		listid = int(sys.stdin.readline());
		print "Showing List number %d"%listid;
		for playlist in get_regular_playlists():
			if playlist.PlaylistID == listid:
				print '%4d' % playlist.PlaylistID, '%s'%playlist.Name;
				
				session = Session()
				session.flush = lambda: True #read only database

				print_playlist(int(playlist.PlaylistID));


	return 0;

if __name__ == '__main__':
	sys.exit(main())
