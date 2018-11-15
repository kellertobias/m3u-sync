#!/usr/bin/env python
# -*- coding:utf-8 -*-

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

rootdir = "/home/user/Musik"

for root, directories, filenames in os.walk('/tmp/'):
	for directory in directories:
		print(os.path.join(root, directory))
	for filename in filenames:
		print(os.path.join(root,filename))