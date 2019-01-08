import importlib
import os

from python_qt_binding import QtCore
from python_qt_binding import QtWidgets

from ..core import console
from ..core import fspath

# ToDo: move package
#     core = client, mirror
#     qtui = guimgr



class AwQtGuiManager(object):

    def __init__(self, client):
        self.__client  = client
        self.__widgets = {}

        for filepath in os.listdir(fspath.package("src/autoware_launcher/qtui/plugins")):
            fkey, fext = os.path.splitext(os.path.basename(filepath))
            if (fkey != "__init__") and (fext == ".py"):
                console.info("load plugin module: " + fkey)
                module = importlib.import_module("autoware_launcher.qtui.plugins." + fkey)
                for wkey, wcls in module.plugin_widgets().items():
                     self.__widgets[fkey + "." + wkey] = wcls

    #def widget(self, view):
    #    return self.__widgets[view["view"]]

    def client(self):
        return self.__client

    def create_widget(self, node, view, parent = None, widget = None):
        widget = widget or self.__widgets[view["view"]]
        return widget(self, node, view)

    def create_frame(self, mirror, guikey = None, guicls = None):
        #print "Create Frame: {:<7} Key: {} Class: {}".format(mirror.nodename(), guikey, guicls)
        if not guicls:
            guikey = guikey or mirror.plugin().frame()
            guicls = self.__widgets[guikey + "_frame"]
        return guicls(self, mirror)

    def create_panel(self, mirror, guikey = None, guicls = None):
        #print "Create Panel: {:<7} Key: {} Class: {}".format(mirror.nodename(), guikey, guicls)
        if not guicls:
            guikey = guikey or mirror.plugin().panel()
            guicls = self.__widgets[guikey + "_panel"]
        return guicls(self, mirror)

    def create_arg_frame(self, parent, view):
        guicls = self.__widgets["args." + view["type"]]
        return guicls(self, parent, view)

    def create_frame_entire_vlayout(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        return layout

    def create_frame_header_hlayout(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(5, 2, 2, 2)
        return layout



class AwLaunchTreeMirror(object):
    
    def __init__(self, client):
        self.nodes = {}
        self.cache = {}
        self.client = client

    def clear(self, lpath = None):
        if lpath:
            self.cache.pop(lpath, None)
        else:
            self.cache.clear()

    def find(self, path):
        if path not in self.cache:
            self.cache[path] = self.client.find_node(path)
        return self.cache[path]

    def create(self, path):
        #console.warning("create_node {}".format(path))
        if path not in self.nodes:
            self.nodes[path] = AwLaunchNodeMirror(self, path)
        return self.nodes[path]

    def remove(self, path, node):
        #console.warning("remove_node {}".format(path))
        self.nodes.pop(path)




class AwLaunchNodeMirror(object):

    def __init__(self, tree, path):
        self.__tree = tree
        self.__path = path
        self.__refs = []

    def __find(self):
        return self.__tree.find(self.__path)

    def tostring(self):
        return self.__find().tostring()

    def status(self):
        node = self.__find()
        if node.status == node.STOP: return "stop"
        if node.status == node.EXEC: return "exec"
        if node.status == node.TERM: return "term"
        return "exec/term"

    def isleaf(self):
        return self.__find().plugin.isleaf()

    def path(self):
        return self.__find().nodepath()

    def name(self):
        return self.__find().nodename()
    
    def plugin(self):
        return self.__find().plugin

    def config(self):
        #return self.__find().config
        return self.__find().config.copy()

    def update(self, ldata):
        return self.__tree.client.update_node(self.__path, ldata)

    def launch(self, mode):
        self.__tree.client.launch_node(self.__path, mode)

    def listnode(self, this):
        return map(lambda node: node.nodepath(), self.__find().listnode(this))

    def haschild(self, name):
        return self.__find().haschild(name)

    def getchild(self, name):
        return self.__tree.create(self.__path + "/" + name)

    def addchild(self, lname, ppath):
        return self.__tree.client.create_node(self.__path + "/" + lname, ppath)

    def children(self):
        mirrored_children = []
        for child in self.__find().children():
            mirrored_children.append(self.__tree.create(child.nodepath()))
        return mirrored_children

    def childnames(self):
        return map(lambda node: node.nodename(), self.__find().children())

    def updated(self):
        for widget in self.__refs:
            if hasattr(widget, "config_updated"): widget.config_updated()

    def status_updated(self, state):
        for widget in self.__refs:
            if hasattr(widget, "status_updated"): widget.status_updated(state)

    def get_config(self, key, value):
        return self.__find().config.get(key, value)

    def generate_launch(self):
        return self.__find().generate_launch()

    def send_term_completed(self):
        print "send_term_completed:" + self.__path