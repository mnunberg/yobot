#!/usr/bin/env python

import gc
import sys


try:
    sys.path.append("../")
    from debuglog import log_debug, log_err, log_warn, log_crit, log_info
    if __name__ == "__main__":
        import debuglog
        debuglog.init("Tabbed Windows", title_color="red")
except ImportError, e:
    def log_generic(*args):
        print " ".join([str(a) for a in args])
    log_debug = log_err = log_warn = log_crit = log_info = log_generic
    log_err(e)

import os
if os.environ.get("USE_PYSIDE"):
    log_warn("Using PySide")
    from PySide.QtCore import *
    from PySide.QtGui import *
else:
    from PyQt4.Qt import (QHBoxLayout, QTabBar, QWidget, QMainWindow, QFrame,
                          QCursor, QVBoxLayout, QMenu, QPixmap, QApplication,
                          QPoint, QPushButton, QSizePolicy, QTabWidget, QMenuBar,
                          QLabel, QDrag, QTabBar, QAction)
    from PyQt4.QtCore import (QMimeData, QObject, SIGNAL, QPoint, Qt)

               

#make a few classes here



signal_connect = QObject.connect

def setmargins(layout, left=-1, top=-1, right=-1, bottom=-1):
    log_debug(left, top, right, bottom)
    oldleft, oldtop, oldright, oldbottom = layout.getContentsMargins()
    layout.setContentsMargins(*[new if new >= 0 else old for old, new in
                                ((oldleft, left), (oldtop, top), (oldright, right), (oldbottom, bottom))])    


class _TabBar(QTabBar):
    STYLE="""
    QTabBar {
        border-bottom:none;
    }
     QTabBar::tab {
     /*
         background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                     stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                     stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
    */
         border: 1px solid palette(shadow);
         border-top-left-radius: 4px;
         border-top-right-radius: 4px;
         min-width: 12ex;
         padding: 2px;
         border-bottom-width:1px;
         background-color:palette(dark);
         margin-right:-2px;
     }

     QTabBar::tab:selected, QTabBar::tab:hover {
         background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                     stop: 0 #fafafa, stop: 0.4 #f4f4f4,
                                     stop: 0.5 #e7e7e7, stop: 1.0 #fafafa);
     }

     QTabBar::tab:selected {
         border-color: #9B9B9B;
         border-bottom-color: #C2C7CB; /* same as pane color */
         background-color:palette(base);
         font-weight:bold;
     }

     QTabBar::tab:!selected {
         margin-top: 2px; /* make non-selected tabs look smaller */
         background-color:palette(window);
     }
     QTabBar::tab:last {
        margin-right:0px;
        border-top-right-radius:15px;
     }
     QTabBar::tab:first {
        border-top-left-radius:15px;
     }
     """
    def __init__(self, realtabwidget):
        super(_TabBar, self).__init__(realtabwidget)
        self.realtabwidget = realtabwidget
        self.drag_pos = QPoint()
        self.setAcceptDrops(False)
        self.setStyleSheet(self.STYLE)
        self.setExpanding(True)
    @property
    def current_widget(self):
        return self.realtabwidget.widget(self.currentIndex())
    
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
        drag.setPixmap(QPixmap.grabWidget(self.current_widget))
        drag.exec_()
        log_debug(drag.target())
        if not isinstance(drag.target(), TabContainer):
            self.detachWidget()
    def mouseDoubleClickEvent(self, event):
        self.detachWidget()
        
    def detachWidget(self):
        log_debug("detachWidget")
        widget = self.current_widget
        if not isinstance(widget, ChatPane):
            log_err("expected ChatPane instance")
            raise ValueError("Expected ChatPane instance, got %r", widget)
            
        if widget.tabcontainer:
            oldsize = widget.tabcontainer.size()
        else:
            oldsize = widget.size()
        
        ret = widget.removeFromTabContainer()
        tc = TabContainer()
        widget.addToTabContainer(tc)
        TabContainer.refs.add(tc)
        tc.show()
        tc.resize(oldsize)
        
        tc.move(QCursor().pos())
        

class _RealTabWidget(QTabWidget):
    def __init__(self, parent):
        super(_RealTabWidget, self).__init__(parent)
        self.setTabBar(_TabBar(self))
        self.tab_ids = set()
        self.setTabsClosable(True)
        self.tabBar().setExpanding(True)
    def addTab(self, widget, *args):
        log_debug("%x: adding %x" % (id(self), id(widget)))
        self.tab_ids.add(id(widget))
        QTabWidget.addTab(self, widget, *args)
        self.setCurrentWidget(widget) 
    def removeTab(self, index, *args):
        widget = self.widget(index)
        log_debug("%x: removing %x" % (id(self), id(widget)))
        self.tab_ids.remove(id(widget))
        super(type(self),self).removeTab(index, *args)
        
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
    def __init__(self, parent = None, destroy_parent_on_close=True):
        super(TabContainer, self).__init__(parent)
        self.setAcceptDrops(True)
        self.destroy_parent_on_close = destroy_parent_on_close
        self.tabwidget = _RealTabWidget(self)
        self.parent_ = parent
        signal_connect(self.tabwidget, SIGNAL("tabCloseRequested(int)"), self._tabCloseRequested)
        signal_connect(self.tabwidget, SIGNAL("currentChanged(int)"), self._currentChanged)
        
        def _tabRemoved(index):
            if self.tabwidget.count() == 0:
                log_warn("last tab removed..")
                self.close()
        self.tabwidget.tabRemoved = _tabRemoved
        
        self.setCentralWidget(self.tabwidget)
        #layout = QVBoxLayout(self.centralWidget())
        #layout.setContentsMargins(0,0,0,0)
        #layout.setSpacing(0)
        #self.centralWidget().setLayout(layout)
        #layout.addWidget(self.tabwidget)
        
    default_stylesheet = ""
    drag_stylesheet = default_stylesheet + """
    QMainWindow {
        margin:1px;
        /*border:3px solid palette(text);*/
        padding:10px;
        background-color:palette(dark);
    }"""
    
    def dragEnterEvent(self, event):
        m = event.mimeData()
        if "action" in m.formats() and m.data("action") == "window_drag":
            log_debug("Accepting")
            event.acceptProposedAction()
            #self.setStyleSheet(self.default_stylesheet + self.drag_stylesheet)
    #def dragLeaveEvent(self, event):
    #    self.setStyleSheet(self.default_stylesheet)
    
    def dropEvent(self, event):
        #self.setStyleSheet(self.default_stylesheet)
        log_debug("")
        m = event.mimeData()
        s = event.source()
        if "action" in m.formats() and m.data("action") == "window_drag":
            event.acceptProposedAction()
            log_debug("Got drop request for window")
            if not getattr(s, "current_widget", None):
                log_debug("Not a valid object for dropping:", s)
                return
            widget = s.current_widget
            if id(widget) in self.tabwidget.tab_ids:
                log_info("drop requested, but widget %r already exists" % (widget))
                return
            widget.addToTabContainer(self)
    
    def _tabCloseRequested(self, index):
        widget = self.tabwidget.widget(index)
        self.tabwidget.removeTab(index)
        widget.close()
        widget.deleteLater()
        
    def _currentChanged(self, index):
        oldmenubar = self.menuWidget()
        if oldmenubar and getattr(oldmenubar, "real_owner", None):
            try:
                oldmenubar.real_owner.setMenuWidget(oldmenubar)
                del oldmenubar.real_owner
            except RuntimeError, e:
                log_err(e)
        widget = self.tabwidget.currentWidget()
        if not widget: return
        self.setWindowTitle(widget.title)
        if isinstance(widget, QMainWindow):
            #preserve the old widget, and return it back to its rightful owner
            menubar = widget.menuWidget()
            menubar.real_owner = widget
            self.setMenuWidget(menubar)
    def forceRemove(self, widget):
        index = self.tabwidget.indexOf(widget)
        if index == -1: return
        self._tabCloseRequested(index)
    def closeEvent(self, event):
        event.accept()
        if self in TabContainer.refs:
            TabContainer.refs.remove(self)
        
class ChatPane(QMainWindow):
    def __init__(self, parent = None, tabcontainer = None, title = ""):
        """Note that the caller is responsible to ensure that this widget has
        draggable content, e.g. insert a DragBar class somewhere"""
        super(ChatPane, self).__init__(parent)
        self.setAcceptDrops(True)
        self.title = title
        self.tabcontainer = None
        self.setupWidgets()
        if not tabcontainer:
            tabcontainer = TabContainer.getContainer()
            if not tabcontainer:
                tabcontainer = TabContainer(parent, destroy_parent_on_close=False)
                tabcontainer.show()
                tabcontainer.activateWindow()
                TabContainer.refs.add(tabcontainer)
        if isinstance(tabcontainer, TabContainer):
            self.addToTabContainer(tabcontainer)
        signal_connect(self, SIGNAL("destroyed()"), lambda: log_info("destroyed"))
    def setupWidgets(self):
        """Override this."""
        self.setCentralWidget(QWidget(self))
        _layout = QVBoxLayout(self.centralWidget())
        self.centralWidget().setLayout(_layout)
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

    def keyPressEvent(self, event):
        if not (Qt.Key_1 <= event.key() <= Qt.Key_9 and
                event.modifiers() & Qt.AltModifier and self.tabcontainer):
            return
        requested = abs(Qt.Key_0-event.key())-1
        self.tabcontainer.tabwidget.setCurrentIndex(requested)
    
class _TestWidget(ChatPane):
    counter = 0
    wrefs = set()
    def setupWidgets(self):
        self.setWindowTitle(self.title)
        menubar = QMenuBar(self)
        menu = QMenu("Title " + self.title)
        self._action_tmp = QAction("Reproduce", self)
        signal_connect(self._action_tmp, SIGNAL("activated()"), self.reproduce)
        menu.addAction(self._action_tmp)
        menubar.addMenu(menu)
        menubar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMenuBar(menubar)
        cw = QWidget(self)
        layout = QVBoxLayout(cw)
        cw.setLayout(layout)
        button = QPushButton("Reproduce", self)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(button)
        self.button = button
        signal_connect(button, SIGNAL("clicked()"), self.reproduce)        
        for o in ("menubar", "menu", "cw"): setattr(self, o, eval(o))
        
        self.setCentralWidget(cw)
    
    def reproduce(self):
        if self.tabcontainer:
            _TestWidget.counter += 1
            cp = _TestWidget(self.tabcontainer, tabcontainer=self.tabcontainer, title=str(self.counter) + " " * 10)
            _TestWidget.wrefs.add(cp)
            signal_connect(cp, SIGNAL("destroyed()"), lambda: _TestWidget.wrefs.remove(cp))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    t = TabContainer()
    p1 = _TestWidget(tabcontainer = t, title="First Pane")
    p2 = _TestWidget(tabcontainer = t, title="Second Pane")
    t.show()
    t.resize(500,500)
    app.exec_()