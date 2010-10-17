#!/usr/bin/env python

from PyQt4.Qt import (QHBoxLayout, QTabBar, QWidget, QMainWindow, QFrame,
                      QCursor, QVBoxLayout, QMenu, QPixmap, QApplication,
                      QPoint, QPushButton, QSizePolicy, QTabWidget, QMenuBar,
                      QLabel, QDrag)
from PyQt4.QtCore import (QMimeData, QObject, SIGNAL, QPoint, Qt)
    
    
import sys
               
try:
    sys.path.append("../")
    from debuglog import log_debug, log_err, log_warn, log_crit, log_info
except ImportError, e:
    log_debug(e)
    def log_generic(*args):
        print " ".join([str(a) for a in args])
    log_debug = log_err = log_warn = log_crit = log_info = log_generic

#make a few classes here

signal_connect = QObject.connect

def setmargins(layout, left=-1, top=-1, right=-1, bottom=-1):
    log_debug(left, top, right, bottom)
    oldleft, oldtop, oldright, oldbottom = layout.getContentsMargins()
    layout.setContentsMargins(*[new if new >= 0 else old for old, new in ((oldleft, left), (oldtop, top), (oldright, right), (oldbottom, bottom))])    

class DragBar(QWidget):
    def __init__(self, parent, text=""):
        super(type(self), self).__init__(parent)
        self.chatpane = parent
        self.label = QLabel(text, self)
        self._layout = QHBoxLayout(self)
        self.setLayout(self._layout)
        self._layout.addWidget(self.label)
        #keep an ID for the window...
        self.chatpane_id = id(parent)
        self.drag_pos = QPoint()
        self.owner = id(parent) if parent else None
        self._layout.setContentsMargins(0,0,0,0)
        self.setStyleSheet("""background:argb(0,0,0,150); border:2px solid black; color:palette(base)""")
        self.setFixedHeight(20)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.pos()
        super(type(self), self).mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if not event.buttons() & Qt.LeftButton: return
        if (event.pos() - self.drag_pos).manhattanLength() < QApplication.startDragDistance(): return
        drag = QDrag(self)
        mimedata = QMimeData()
        mimedata.setData("action", "window_drag")
        drag.setMimeData(mimedata)
        drag.setPixmap(QPixmap.grabWidget(self.chatpane))
        drag.exec_()
        log_debug(drag.target())
        if not isinstance(drag.target(), TabContainer):
            self.detachWidget()
    def mouseDoubleClickEvent(self, event):
        self.detachWidget()
    
    def keyPressEvent(self, event):
        print event
    
    def detachWidget(self):
        log_debug("detachWidget")
        oldsize = self.chatpane.size()
        ret = self.chatpane.removeFromTabContainer()
        log_debug("ret was", ret)
        tw = TabContainer()
        self.chatpane.addToTabContainer(tw)
        TabContainer.refs.add(tw)
        tw.resize(oldsize)
        tw.show()
        tw.move(QCursor().pos())


class _RealTabWidget(QTabWidget):
    def __init__(self, parent):
        QTabWidget.__init__(self, parent)
        self.tab_ids = set()
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.tabBar().setExpanding(True)
        self.tabBar().setDrawBase(False)
        self.tabBar().setMovable(True)
        self.tabBar().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    def addTab(self, widget, *args):
        log_debug("adding", id(widget))
        self.tab_ids.add(id(widget))
        QTabWidget.addTab(self, widget, *args)
        self.setCurrentWidget(widget)
        
    def removeTab(self, index, *args):
        widget = self.widget(index)
        log_debug("removing", id(widget))
        self.tab_ids.remove(id(widget))
        QTabWidget.removeTab(self, index, *args)
    def tabRemoved(self, index):
        QTabWidget.tabRemoved(self, index)
        if self.count() == 1:
            self.tabBar().hide()
        elif self.count() == 0:
            if self in TabContainer.refs:
                TabContainer.refs.remove(self)
            self.deleteLater()
    def tabInserted(self, index):
        QTabWidget.tabInserted(self, index)
        if self.count() > 1:
            self.tabBar().show()
        else:
            self.tabBar().hide()
        
class TabContainer(QMainWindow):
    refs = set()
    @classmethod
    def getContainer(klass):
        #first try to find the one that has focus, otherwise return any
        last = None
        for i in klass.refs:
            if i.isActiveWindow(): return i
            last = i
        return last

    stylesheet_ = """
    ::tab {
         background-color:palette(text); color:palette(base);
        border-top:1px solid;
        border-right:1px solid;
        border-radius:3px;
    }
    ::tab:selected {
        background-color:palette(base); color:palette(text);
    }
    ::tab:hover {
        background-color:palette(window); color:palette(text);
    }
    """
    stylesheet_ = ""
    def __init__(self, parent = None, destroy_parent_on_close=True):
        QTabWidget.__init__(self, parent)
        self.setAcceptDrops(True)
        self.setDocumentMode(True)
        self.setStyleSheet(self.stylesheet_)
        self.destroy_parent_on_close = destroy_parent_on_close
        self.tabwidget = _RealTabWidget(self)
        self.parent_ = parent
        signal_connect(self.tabwidget, SIGNAL("tabCloseRequested(int)"), self._tabCloseRequested)
        signal_connect(self.tabwidget, SIGNAL("currentChanged(int)"), self._currentChanged)
        signal_connect(self.tabwidget, SIGNAL("destroyed()"), self.deleteLater)
        signal_connect(self, SIGNAL("destroyed()"), lambda: self.refs.remove(self))
        
        self.setCentralWidget(QWidget(self))
        layout = QVBoxLayout(self.centralWidget())
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        self.centralWidget().setLayout(layout)
        layout.addWidget(self.tabwidget)
        
    def dragEnterEvent(self, event):
        m = event.mimeData()
        if "action" in m.formats() and m.data("action") == "window_drag":
            log_debug("Accepting")
            event.acceptProposedAction()
    def dropEvent(self, event):
        log_debug("dropEvent")
        m = event.mimeData()
        s = event.source()
        if "action" in m.formats() and m.data("action") == "window_drag":
            log_debug("Got drop request for window")
            if not getattr(s, "chatpane", None):
                log_debug("Not a valid object for dropping:", s)
                return
            if id(s.chatpane) in self.tabwidget.tab_ids:
                log_debug("drop requested, but widget %r already exists" % (s.chatpane))
                return
            s.chatpane.addToTabContainer(self)
            event.acceptProposedAction()
    
    def _tabCloseRequested(self, index): self.tabwidget.removeTab(index)
    
    def _currentChanged(self, index):
        oldmenubar = self.menuWidget()
        if oldmenubar and getattr(oldmenubar, "real_owner", None):
            log_debug("Old...")
            try:
                oldmenubar.real_owner.setMenuWidget(oldmenubar)
            except RuntimeError, e:
                log_err(e)
            log_debug("Done..")
        widget = self.tabwidget.currentWidget()
        if not widget: return
        self.setWindowTitle(widget.title)
        if isinstance(widget, QMainWindow):
            log_debug("switching menu...")
            #preserve the old widget, and return it back to its rightful owner
            menubar = widget.menuWidget()
            menubar.real_owner = widget
            self.setMenuWidget(menubar)
    def forceRemove(self, widget):
        index = self.tabwidget.indexOf(widget)
        if index == -1: return
        self._tabCloseRequested(index)
    
class ChatPane(QMainWindow):
    def __init__(self, parent = None, tabcontainer = None, title = ""):
        """Note that the caller is responsible to ensure that this widget has
        draggable content, e.g. insert a DragBar class somewhere"""
        QMainWindow.__init__(self, parent)
        self.setAcceptDrops(True)
        self.title = title
        self.tabcontainer = None
        self.setupWidgets()
        
        #if not_add_to_existing...
        
        if not tabcontainer:
            tabcontainer = TabContainer.getContainer()
            if not tabcontainer:
                tabcontainer = TabContainer(parent, destroy_parent_on_close=False)
                tabcontainer.show()
                tabcontainer.activateWindow()
                TabContainer.refs.add(tabcontainer)
        if isinstance(tabcontainer, TabContainer):
            self.addToTabContainer(tabcontainer)
        
    def setupWidgets(self):
        """Override this."""
        self.setCentralWidget(QWidget(self))
        _layout = QVBoxLayout(self.centralWidget())
        self.centralWidget().setLayout(_layout)
        _layout.addWidget(DragBar(self, text="Drag me..."))
        _layout.setContentsMargins(0,0,0,0)
        self.centralWidget().layout().addWidget(QLabel("This is normal text", self))
        
    def removeFromTabContainer(self):
        if self.tabcontainer:
            #find ourself in the widget..
            index = self.tabcontainer.tabwidget.indexOf(self)
            if index == -1:
                log_err("invalid index for widget", str(id(self)))
                self.tabcontainer = None
                return False
            self.tabcontainer.tabwidget.removeTab(index)
            self.tabcontainer = None
            return True
        log_err("tabcontainer has not been set!")
        return False
    def addToTabContainer(self, tabcontainer):
        self.setWindowFlags(Qt.Widget)
        if self.tabcontainer:
            self.removeFromTabContainer()
        self.tabcontainer = tabcontainer
        self.tabcontainer.tabwidget.addTab(self, self.title)
        
    def closeEvent(self, event):
        log_err("")
        #clean up the tabs...
        if self.tabcontainer:
            self.tabcontainer.forceRemove(self)
        event.accept()
        self.deleteLater()
        
    def keyPressEvent(self, event):
        if not (Qt.Key_1 <= event.key() <= Qt.Key_9 and
                event.modifiers() & Qt.AltModifier and self.tabcontainer):
            return
        requested = abs(Qt.Key_0-event.key())-1
        self.tabcontainer.tabwidget.setCurrentIndex(requested)
        
        
class _TestWidget(ChatPane):
    counter = 0
    def setupWidgets(self):
        self.setWindowTitle(self.title)
        menubar = QMenuBar(self)
        menu = QMenu("Title " + self.title)
        menu.addAction("Reproduce", self.reproduce)
        menubar.addMenu(menu)
        menubar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMenuBar(menubar)
        
        cw = QWidget(self)
        layout = QVBoxLayout(cw)
        cw.setLayout(layout)
        dragbar = DragBar(self, "drag: " + self.title)
        layout.setMenuBar(dragbar)
        button = QPushButton("Reproduce", self)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(button)
        self.button = button
        signal_connect(button, SIGNAL("clicked()"), self.reproduce)
        
        for o in ("menubar", "menu", "dragbar", "cw"): setattr(self, o, eval(o))
        
        self.setCentralWidget(cw)
    
    def reproduce(self):
        if self.tabcontainer:
            self.counter += 1
            cp = _TestWidget(self.tabcontainer, tabcontainer=self.tabcontainer, title=str(self.counter) + " " * 10)
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    t = TabContainer()
    p1 = _TestWidget(tabcontainer = t, title="First Pane")
    p2 = _TestWidget(tabcontainer = t, title="Second Pane")
    t.show()
    t.resize(500,500)
    app.exec_()