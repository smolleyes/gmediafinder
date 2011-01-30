from distutils.core import setup

from glob import glob
import os

import pygtk
pygtk.require('2.0')
import gtk, sys

import pygst
pygst.require('0.10')
import gst

try:
    import py2exe.mf as modulefinder
except ImportError:
    import modulefinder
import win32com
for p in win32com.__path__[1:]:
    modulefinder.AddPackagePath("win32com", p)
for extra in ["win32com.shell"]: #,"win32com.mapi"
    __import__(extra)
    m = sys.modules[extra]
    for p in m.__path__[1:]:
        modulefinder.AddPackagePath(extra, p)

try:
    import py2exe
except ImportError:
    pass

setup(
    name = 'gmediafinder',
    packages = ['GmediaFinder'],
    description = 'Stream and download youtube or mp3 search engines files',
    version = '1.0',

    windows = [
                  {
                      'script': 'GmediaFinder/gmediafinder.py',
                      'icon_resources': [(1, "data/img/gmediafinder.ico")],
                  }
              ],

    options = {
                  'py2exe': {
                      'bundle_files': 3,
                      'packages':'encodings',
                      'includes': 'cairo, pango, pangocairo, atk, gobject, gio, pygst, gst'
                  }
              },

    data_files=[
                   ('images/22x22',['images/22x22/gmediafinder.png']),
	('images/24x24',['images/24x24/gmediafinder.png']),
	('images/48x48/apps',['images/48x48/gmediafinder.png']),
	('data/glade',['data/glade/mainGui.glade']),
        ('data/img',['data/img/gmediafinder.png','data/img/sound.png']),
               ]
)
