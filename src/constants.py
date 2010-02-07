#-*- coding: UTF-8 -*-
import os

version = "0.1"
app_name = "Gmediafinder"
exec_path =  os.path.dirname(os.path.abspath(__file__))
data_path =  os.path.join(exec_path,"data")
img_path = os.path.join(data_path,"img")
glade_path = os.path.join(data_path,"glade")

## gui
glade_file = os.path.join(glade_path,'mainGui.glade')