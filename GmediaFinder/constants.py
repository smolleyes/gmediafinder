#-*- coding: UTF-8 -*-
import os,sys,gtk
import gettext
from Translation import Translation

version = "0.1"
APP_NAME = "Gmediafinder"
exec_path =  os.path.dirname(os.path.abspath(__file__))
if sys.platform == "win32" and not ('constants.py' in os.listdir(os.path.abspath('.'))):
    data_path= "data"
else:
    data_path =  os.path.join(exec_path,"../data")
img_path = os.path.join(data_path,"img")
glade_path = os.path.join(data_path,"glade")

## gui
if ('/usr' in exec_path):
    glade_file = os.path.join('/usr/share/gmediafinder/mainGui.glade')
else:
    glade_file = os.path.join(glade_path,'mainGui.glade')


## LOCALISATION
source_lang = "en"
rep_trad = "/usr/share/locale"
traduction = Translation(APP_NAME, source_lang, rep_trad)
gettext.install(APP_NAME)
gtk.glade.bindtextdomain(APP_NAME, rep_trad)
gettext.textdomain(APP_NAME)
_ = traduction.gettext
