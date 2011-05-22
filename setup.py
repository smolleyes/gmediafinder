#!/usr/bin/env python

import sys, os
from stat import *
from distutils.core import setup
from distutils.command.install import install as _install

try:
    from DistUtilsExtra.command import *
except ImportError:
    print 'Cannot install gmediafinder :('
    print 'Would you please install package "python-distutils-extra" first?'
    sys.exit()
import glob

INSTALLED_FILES = '.installed_files'

#stolen from ccsm
class install (_install):

	def run (self):

		_install.run(self)
		outputs = self.get_outputs()
		data = '\n'.join(outputs)
		try:
			f = open(INSTALLED_FILES, 'w')
		except:
			self.warn ('Could not write installed files list %s' %INSTALLED_FILES)
			return 

		f.write(data)
		f.close()

class uninstall(_install):

	def run(self):
		try:
			files = file(INSTALLED_FILES, 'r').readlines()
		except:
			self.warn('Could not read installed files list %s' %INSTALLED_FILES)
			return

		for f in files:
			print 'Uninstalling %s' %f.strip()
			try:
				os.unlink(f.strip())
			except:
				self.warn('Could not remove file %s' %f)
		os.remove(INSTALLED_FILES)

version = open('VERSION', 'r').read().strip()	

packages = ['GmediaFinder','GmediaFinder.lib','GmediaFinder.lib.engines']

data_files = [
	('share/icons/hicolor/22x22/apps',['images/22x22/gmediafinder.png']),
	('share/icons/hicolor/24x24/apps',['images/24x24/gmediafinder.png']),
	('share/icons/hicolor/48x48/apps',['images/48x48/gmediafinder.png']),
	('share/applications',['gmediafinder.desktop']),
	('share/gmediafinder/glade',['data/glade/mainGui.glade']),
	('share/gmediafinder/img',['data/img/gmediafinder.png','data/img/sound.png','data/img/throbber.png','data/img/throbber.gif']),
]


setup(
	name='gmediafinder',
	version=version,
	description='Find audio or video files on various websites',
	author='Laguillaumie sylvain',
	author_email='s.lagui@free.fr',
	url='http://penguincape.org',
	packages=packages,
	scripts=['gmediafinder'],
	data_files=data_files,
	cmdclass={'build' :  build_extra.build_extra,
	    'build_i18n' :  build_i18n.build_i18n,
	    'build_help' :  build_help.build_help,
	    'build_icons' :  build_icons.build_icons,
	    'uninstall': uninstall,
	    'install': install,
	    },
)

#Stolen from ccsm's setup.py
if sys.argv[1] == 'install':
	
	prefix = None

	if len (sys.argv) > 2:
		i = 0
		for o in sys.argv:
			if o.startswith ("--prefix"):
				if o == "--prefix":
					if len (sys.argv) >= i:
						prefix = sys.argv[i + 1]
					sys.argv.remove (prefix)
				elif o.startswith ("--prefix=") and len (o[9:]):
					prefix = o[9:]
				sys.argv.remove (o)
				break
			i += 1

	if not prefix:
		prefix = '/usr'
	os.system('chmod +x %s' % os.path.join(prefix,'bin/gmediafinder'))
	gtk_update_icon_cache = '''gtk-update-icon-cache -f -t \
%s/share/icons/hicolor''' % prefix
	root_specified = [s for s in sys.argv if s.startswith('--root')]
	if not root_specified or root_specified[0] == '--root=/':
		print 'Updating Gtk icon cache.'
		os.system(gtk_update_icon_cache)
	else:
		print '''*** Icon cache not updated. After install, run this:
***     %s''' % gtk_update_icon_cache
        os.system('xdg-desktop-menu install --novendor gmediafinder.desktop')

