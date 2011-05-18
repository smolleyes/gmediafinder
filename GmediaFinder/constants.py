#-*- coding: UTF-8 -*-
import os,sys,gtk
import gettext
from Translation import Translation

version = "0.9"
APP_NAME = "gmediafinder"
exec_path =  os.path.dirname(os.path.abspath(__file__))

## gui
if ('/usr/local' in exec_path):
    data_path = os.path.join('/usr/local/share/gmediafinder')
elif ('/usr' in exec_path):
	data_path = os.path.join('/usr/share/gmediafinder')
else:
    data_path =  os.path.join(exec_path,"../data")

if sys.platform == "win32" and not ('constants.py' in os.listdir(os.path.abspath('.'))):
    data_path= "data"

img_path = os.path.join(data_path,"img")
glade_path = os.path.join(data_path,"glade")
glade_file = os.path.join(glade_path,"mainGui.glade")
print glade_file


## LOCALISATION
source_lang = "en"
rep_trad = "/usr/share/locale"
traduction = Translation(APP_NAME, source_lang, rep_trad)
gettext.install(APP_NAME)
gtk.glade.bindtextdomain(APP_NAME, rep_trad)
gettext.textdomain(APP_NAME)
_ = traduction.gettext
