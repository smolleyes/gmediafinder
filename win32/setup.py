from distutils.core import setup

from glob import glob
import os
from os import path


import pygtk
pygtk.require('2.0')
import gtk, sys
import shutil

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

mfcdir = 'C:\Python26\Lib\site-packages\pythonwin'
mfcfiles = [path.join(mfcdir, i) for i in ["mfc90.dll","mfc90u.dll" ,"mfcm90.dll","mfcm90u.dll","Microsoft.VC90.MFC.manifest"]]
gstPath = "C:\gst"

print ('Deploying GStreamer')
# Copy gstreamer binaries to the dist folder
for name in os.listdir(os.path.join(gstPath, 'bin')):
    shutil.copy (os.path.join(gstPath, 'bin', name),
                 os.path.join (os.getcwd(), 'dist/bin'))
for file in filter(lambda f: f.endswith('.dll'),
                       os.listdir(path.join(gstPath, 'bin'))):
        if not os.path.isfile(path.join('dist', file)):
            shutil.copy(path.join(gstPath, 'bin', file), 'dist')

if not os.path.exists(os.path.join(gstPath, 'lib', 'gstreamer-0.10')):
    shutil.copytree(os.path.join(gstPath, 'lib', 'gstreamer-0.10'),
                    os.path.join(os.path.join (os.getcwd(), 'dist/lib'), 'gstreamer-0.10'))
shutil.copyfile("C:\\libxml2-2.dll", 'dist/libxml2-2.dll')

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
                      'includes': 'cairo, pango, pangocairo, atk, gobject, gio, gst, gtk'
                  }
              },

    data_files=[("Microsoft.VC90.MFC", mfcfiles),
                   ('images/22x22',['images/22x22/gmediafinder.png']),
	('images/24x24',['images/24x24/gmediafinder.png']),
	('images/48x48/apps',['images/48x48/gmediafinder.png']),
	('data/glade',['data/glade/mainGui.glade']),
        ('data/img',['data/img/gmediafinder.png','data/img/sound.png']),
               ]
)