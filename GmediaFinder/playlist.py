### playlist class

import gtk
from xml.dom import minidom
from xml.dom.minidom import Document, parse
import thread
import threading
from functions import htmlentitydecode, translate_html
import urllib2
import re

class Playlist(object):
    def __init__(self, gui):
        self.gui = gui
        self.xml = self.gui.playlists_xml
        self.selected_iter = None
        self.select_dialog = self.gui.gladeGui.get_widget("select_playlist_dialog")
        self.select_scroll = self.gui.gladeGui.get_widget('playlist_chooser_scroll')
        self.add_pl_btn = self.gui.gladeGui.get_widget('add_playlist_btn2')
        self.create_playlist_dialog = self.gui.gladeGui.get_widget("newcat_dialog")
        self.newcat_entry = self.gui.gladeGui.get_widget("newcat_entry")
        self.add_playlist_btn = self.gui.gladeGui.get_widget("add_playlist_btn")
        self.del_playlist_btn = self.gui.gladeGui.get_widget("del_playlist_btn")
        self.add_pl_btn.connect('clicked', self.add_playlist)
        self.add_playlist_btn.connect('clicked',self.add_playlist)
        self.del_playlist_btn.connect('clicked',self.remove_playlist)
        # Creation d'un modele nom/url source/flux/moteur
        self.treestore = gtk.TreeStore(str,str,str,str )
        self.treestore.connect('rows-reordered',self.on_rows_reordered)
        self.treeview = gtk.TreeView(self.treestore)
        self.tvcolumn = gtk.TreeViewColumn('')
        self.treeview.append_column(self.tvcolumn)
        self.cell = gtk.CellRendererText()
        self.tvcolumn.pack_start(self.cell, True)
        self.tvcolumn.add_attribute(self.cell, 'text', 0)

        #self.treeview.set_search_column(0)
        self.tvcolumn.set_sort_column_id(0)
        self.treeview.set_reorderable(True)
        #self.treeview.enable_model_drag_source(0, [("STRING", 0, 0),
                                                   #('text/plain', 0, 0)
                                                   #],
                                               #gtk.gdk.ACTION_DEFAULT)
        #self.treeview.enable_model_drag_dest([("STRING", 0, 0),
                                              #('text/plain', 0, 0),
                                              #('text/uri-list', 0, 0)
                                              #],
                                             #gtk.gdk.ACTION_DEFAULT)
        self.treeview.connect("row-activated", self.on_selected)
        #self.treeview.connect("drag_data_get", self.drag_data_get_data)
        #self.treeview.connect("drag_data_received",
                              #self.drag_data_received_data)     
        
        ##popup tree
        self.poptreeview = gtk.TreeView(self.treestore)
        tvcolumn = gtk.TreeViewColumn('')
        self.poptreeview.append_column(tvcolumn)
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, 'text', 0)
        self.select_scroll.add(self.poptreeview)
        self.poptreeview.show_all()
        self.poptreeview.connect("cursor-changed", self.on_selected)
        ## add to gui
        self.gui.playlist_scrollbox.add(self.treeview)
        self.load_xml()
        
    
    def on_rows_reordered(self,path,row_iter,order):
		print 'here'
		print path,row_iter,order
    
    def make_pb(self, tvcolumn, cell, model, riter):
        stock = model.get_value(riter, 1)
        pb = self.treeview.render_icon(stock, gtk.ICON_SIZE_MENU, None)
        cell.set_property('pixbuf', pb)
        return

    def add(self, name, link, media, engine):
        rep = self.select_dialog.run()
        catname = ''
        print rep
        if rep == 1 or rep == gtk.RESPONSE_DELETE_EVENT:
            self.select_dialog.hide()
            return
        else:
            catname = self.treestore.get_value(self.selected_iter, 0)
            self.select_dialog.hide()
        node_iter = self.get_iter_by_name(catname)
        root = self.parser.documentElement
        if node_iter:
            self.treestore.append(node_iter, [name,link,media,engine])
        else:
            catname = self.add_playlist()
            node_iter = self.get_iter_by_name(catname)
            self.treestore.append(node_iter, [name,link,media,engine])
        new_entry = self.create_entry(name, link, media, engine)
        node = self.get_elem_by_name(catname,'playlist')
        if node:
            node.appendChild(new_entry)
        self.parser.writexml(open(self.xml,"w"),'', '', '', "UTF-8")

    def get_iter_by_name(self, name):
        model = self.treeview.get_model()
        node_iter = None
        for item in model:
            if model.get_value(item.iter, 0) == name:
                node_iter = item.iter
        return node_iter
        
    def new_playlist(self,name):
		model = self.treeview.get_model()
		m_iter = self.treestore.append(None, [name,'','',''])
		return m_iter

    def on_selected(self, cell, t=None, r=None):
        self.selected_iter = cell.get_selection().get_selected()[1]
        self.gui.selected_iter = cell.get_selection().get_selected()[1]
        self.gui.path = self.treestore.get_path(self.selected_iter)
        url = self.treestore.get_value(self.selected_iter, 2)
        src_link = self.treestore.get_value(self.selected_iter, 1)
        if url == '':
            return
        engine = self.treestore.get_value(self.selected_iter, 3)
        try:
            self.gui.set_engine(engine)
        except:
            return
        self.gui.playlist_mode = True
        if self.test_link(url):
            self.gui.media_name = self.treestore.get_value(self.selected_iter, 0)
            self.gui.stop_play()
            self.gui.start_play(url)
        else:
            if engine == 'Youtube':
                vid=None
                try:
                    vid = re.search('watch\?v=(.*?)&(.*)',src_link).group(1)
                except:
                    try:
                        vid = re.search('watch\?v=(.*)',src_link).group(1)
                    except:
                        return
                thread.start_new_thread(self.gui.search_engine.play,(vid,))
                self.gui.media_name = self.treestore.get_value(self.selected_iter, 0)
            return
            
    def test_link(self,link):
        response = None
        try:
            request = urllib2.Request(link)
            request.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30')
            response = urllib2.urlopen(request)
        except:
            return False
        # check content type:
        content = response.info().getheader('Content-Type')
        print 'link content type: %s' % content
        if ('application/octet-stream' in content) or ('video' in content) or ('audio' in content):
            return True
        else:
            return False
        
    def drag_data_get_data(self, treeview, context, selection, target, etime):
        treeselection = treeview.get_selection()
        model, iter = treeselection.get_selected()
        data = model.get_value(iter, 0)
        selection.set('text/plain', 8, data)

    def drag_data_received_data(self, treeview, context, x, y, selection,
                                info, etime):
        print selection.target, selection.type, selection.format, selection.data
        drop_info = treeview.get_dest_row_at_pos(x, y)
        if drop_info:
            model = treeview.get_model()
            path, position = drop_info
            data = selection.data
            print path, data, model.get_value(model.get_iter(path), 0)
        return
    
    ## XML
    def load_xml(self):
        self.parser = parse(self.xml)
        for node in self.parser.getElementsByTagName('playlist'):
            name = htmlentitydecode(self.get_value_tag("name",node) or '' )
            m_iter = self.treestore.append(None, [name,'','',''])
            for entry in node.getElementsByTagName('entry'):
                link =  self.get_value_tag("url",entry)
                name = htmlentitydecode(self.get_value_tag("name",entry) or '' )
                flux = self.get_value_tag("media",entry)
                engine = self.get_value_tag("engine",entry)
                self.treestore.append(m_iter, [name,link,flux,engine])
                
    def get_elem_by_name(self, name, elem_type):
        for node in self.parser.getElementsByTagName(elem_type):
            node_name = self.get_value_tag("name",node)
            if name == node_name:
                return node

    def get_value_tag(self,name_tag,root_tag):
        tag = root_tag.getElementsByTagName(name_tag)
        if tag:
            tag = tag[0]
            first_child = tag.firstChild
            return None if not first_child else first_child.data
        else:
            return None
            
    def get_new_node(self,name_node,value_node):
        if name_node:
            node_tag = self.parser.createElement(name_node)
        else:
            return
        if value_node:
            node_text = self.parser.createTextNode(value_node)
            node_tag.appendChild(node_text)
        else:
            return
        return node_tag
            
    def add_playlist(self,widget=None):
        self.newcat_entry.set_text('')
        rep = self.create_playlist_dialog.run()
        if rep == gtk.RESPONSE_DELETE_EVENT or rep == 1:
            self.create_playlist_dialog.hide()
            return
        else:
            catname = self.newcat_entry.get_text()
            self.create_playlist_dialog.hide()
            doc_root = self.parser.childNodes[0]
            if not self.get_elem_by_name(catname,'playlist'):
                root = self.parser.createElement("playlist")
                root.appendChild(self.get_new_node("name",catname))
                doc_root.appendChild(self.parser.createTextNode("\n\t\t"))
                doc_root.appendChild(root)
                self.parser.writexml(open(self.xml,"w"),'', '', '', "UTF-8")
                self.treestore.append(None, [catname,"","",""])
            return catname
            
    def remove_playlist(self,widget=None):
        self.selected_iter = self.treeview.get_selection().get_selected()[1]
        name = self.treestore.get_value(self.selected_iter, 0)
        url = self.treestore.get_value(self.selected_iter, 1)
        self.treestore.remove(self.selected_iter)
        node = None
        if url != '':
            node = self.get_elem_by_name(name,'entry')
        else:
            node = self.get_elem_by_name(name,'playlist')
        node.parentNode.removeChild(node)
        self.parser.writexml(open(self.xml,"w"),'', '', '', "UTF-8")
        
    def create_entry(self, name, link, media, engine):
        name = translate_html(unicode(name))
        new_entry = None
        if not name or name == "":
            return
        new_entry = self.parser.createElement("entry")
        new_entry.appendChild(self.parser.createTextNode("\n\t\t"))
        new_entry.appendChild(
            self.get_new_node("name",name))
        new_entry.appendChild(self.parser.createTextNode("\n\t\t"))
        new_entry.appendChild(
            self.get_new_node("url",link))
        new_entry.appendChild(self.parser.createTextNode("\n\t\t"))
        new_entry.appendChild(
            self.get_new_node("media",media))
        new_entry.appendChild(self.parser.createTextNode("\n\t\t"))
        new_entry.appendChild(
            self.get_new_node("engine",engine))
        new_entry.appendChild(self.parser.createTextNode("\n\t\t"))
        return new_entry
		
