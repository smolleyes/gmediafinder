#-*- coding: UTF-8 -*-
import os,sys

version = "0.1"
app_name = "Gmediafinder"
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
