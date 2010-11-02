#!/usr/bin/env python

import sys

try:
    sys.path.append("../")
    from debuglog import log_debug, log_err, log_warn, log_crit, log_info
    from gui_util import adjust_stylesheet_palette
    if __name__ == "__main__":
        import debuglog
        debuglog.init("Tabbed Windows", title_color="red")
except ImportError, e:
    def log_generic(*args):
        print " ".join([str(a) for a in args])
    log_debug = log_err = log_warn = log_crit = log_info = log_generic
    adjust_stylesheet_palette = lambda x: x
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
                          QLabel, QDrag, QTabBar, QAction, QPainter, QStyleOptionTab,
                          QImage, QDesktopWidget, QRect)
    from PyQt4.QtCore import (QMimeData, QObject, SIGNAL, QPoint, Qt, QTimer, QSize,
                              pyqtSignal)

               

#make a few classes here



signal_connect = QObject.connect

def setmargins(layout, left=-1, top=-1, right=-1, bottom=-1):
    log_debug(left, top, right, bottom)
    oldleft, oldtop, oldright, oldbottom = layout.getContentsMargins()
    layout.setContentsMargins(*[new if new >= 0 else old for old, new in
                                ((oldleft, left), (oldtop, top), (oldright, right), (oldbottom, bottom))])    
    

TABBAR_STYLE_BASE="""
    QTabBar {
        border-bottom:none;
    }
     QTabBar::tab {
        min-width:100px;
        margin-top:2px;
        border: 1px groove palette(dark);
        border-top-left-radius: 4px; border-top-right-radius: 4px;
        padding-right:10px; padding-left:10px;
        border-bottom-width:1px;
        margin-right:-2px;
        border-bottom:1px solid $PALETTE_ADJUST(dark, -200,-200,-200,-255);
        background-color:$PALETTE_ADJUST(dark, -140, -140, -140, 255);
        color:palette(base);
     }
     QTabBar::tab:selected {
        background-color:qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 $PALETTE_ADJUST(dark, -50, -50, -50, -100),
            stop:0.8 $PALETTE_ADJUST(text, 35, 35 ,35, 0));
        background-repeat:repeat-x;
        border-top-color:qlineargradient(x1:0,y1:0,x2:1,y2:0,
            stop:0 argb(0,0,0,0),
            stop:0.2 $PALETTE_ADJUST(text, 35, 35, 35, 0),
            stop:0.8 $PALETTE_ADJUST(text, 35, 35, 35, 0),
            stop:1 argb(0,0,0,0));
        border-top-width:4px; border-radius:0px;
        border-style:double;
     }
     QTabBar::tab:last:!selected {
        margin-right:0px;
        border-top-right-radius:15px;
     }
     QTabBar::tab:first:!selected {
        margin-left:0px;
        border-top-left-radius:15px;
     }
     QTabBar::tab:only-one {
        border-top-left-radius:15px;
        border-top-right-radius:15px;
        margin-right:0px; margin-left:0px;
    }     
     """

def setTabBarStyle(tb):
    if True:
        tb.base_stylesheet = adjust_stylesheet_palette(TABBAR_STYLE_BASE)
        tb.setStyleSheet(tb.base_stylesheet)


class DragPixmap(QLabel):
    CURSOR_OFFSET=25
    def __init__(self, pixmap, opacity=0.40, parent=None):
        QLabel.__init__(self, parent)
        self.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        self.setPixmap(pixmap)
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.Dialog)
        self.setWindowOpacity(opacity)
        
        self.orig_size = pixmap.size()
        self.screen_geometry = QDesktopWidget().availableGeometry()
        self.old_geometry = QRect()
        
        #state variable
        self.isShrinked = False
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.updatepos)
        self.timer.start()
    
    def updatepos(self):
        self.setUpdatesEnabled(False)
        pos = QCursor().pos()
        geometry = self.geometry()
        geometry.moveTo(pos.x() + self.CURSOR_OFFSET, pos.y() + self.CURSOR_OFFSET)
        intersected = geometry.intersected(self.screen_geometry)
        while True:
            if not intersected == geometry: #too big
                geometry = intersected
                self.isShrinked = True
                break
            if self.isShrinked: #enlarge
                geometry.setSize(self.orig_size)
                intersected = geometry.intersected(self.screen_geometry)
                if not intersected == geometry:
                    self.isShrinked = True
                    geometry = intersected
                else:
                    self.isShrinked = False
                break
            break
        if geometry.intersects(self.screen_geometry):
            self.setGeometry(geometry)
        self.setUpdatesEnabled(True)

class TabBar(QTabBar):
    widgetDnD = pyqtSignal((QWidget, QWidget))
    
    def __init__(self, realtabwidget):
        super(TabBar, self).__init__(realtabwidget)
        self.realtabwidget = realtabwidget
        self.drag_pos = QPoint()
        self.setAcceptDrops(False)
        setTabBarStyle(self)
            
    @property
    def current_widget(self):
        return self.realtabwidget.widget(self.currentIndex())
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.pos()
        super(type(self), self).mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if not event.buttons() & Qt.LeftButton: return
        if (event.pos() - self.drag_pos).manhattanLength() < 100: return
        
        event.accept()
        drag = QDrag(self)
        mimedata = QMimeData()
        mimedata.setData("action", "window_drag")
        drag.setMimeData(mimedata)
        widget = self.current_widget
        pixmap = QPixmap.grabWidget(widget).scaledToWidth(300, Qt.SmoothTransformation)
        dragpixmap = DragPixmap(pixmap, 0.50, self)
        dragpixmap.move(QCursor().pos())
        dragpixmap.show()
        drag.exec_()
        dragpixmap.deleteLater()
        self.widgetDnD.emit(self.current_widget, drag.target())
        return
                

class RealTabWidget(QTabWidget):
    tabs_stylesheet_fmt = """QTabBar::tab:only-one { width: %dpx; border:none;
    border-radius:none;}"""
    def __init__(self, parent):
        super(RealTabWidget, self).__init__(parent)
        self.setTabBar(TabBar(self))
        self.tab_ids = set()
        self.setTabsClosable(True)
        self.tabBar().setExpanding(True)
    def addTab(self, widget, *args):
        log_debug("%x: adding %x" % (id(self), id(widget)))
        self.tab_ids.add(id(widget))
        if not self.count():
            self.resize(widget.size())
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
        self.tabwidget = RealTabWidget(self)
        
        #important!
        self.tabwidget.tabBar().widgetDnD.connect(self.handleDnD, Qt.QueuedConnection)
        
        signal_connect(self.tabwidget, SIGNAL("tabCloseRequested(int)"), self._tabCloseRequested)
        signal_connect(self.tabwidget, SIGNAL("currentChanged(int)"), self._currentChanged)
        
        def _tabRemoved(index):
            if self.tabwidget.count() == 0:
                log_warn("last tab removed..")
                self.close()
        self.tabwidget.tabRemoved = _tabRemoved
        
        self.setCentralWidget(self.tabwidget)
        
    default_stylesheet = ""
    drag_stylesheet = default_stylesheet + """
    QMainWindow {
        margin:1px;
        /*border:3px solid palette(text);*/
        padding:10px;
        background-color:palette(dark);
    }"""
    
    def handleDnD(self, source, target):
        if not isinstance(target, TabContainer) and not self.tabwidget.count() == 1:
            #something that's not going to accept our drop and this is not the only tab:
            if not isinstance(source, ChatPane):
                raise ValueError("Source Widget is something other than a ChatPane object: %r", source)
            assert id(source) in self.tabwidget.tab_ids
            tc = TabContainer(self.parentWidget(),destroy_parent_on_close=False)
            TabContainer.refs.add(tc)
            source.addToContainer(tc)
            tc.resize(self.size())
            tc.move(QCursor().pos())
            tc.show()
        if not self.tabwidget.count():
            self.deleteLater()
    
    def dragEnterEvent(self, event):
        m = event.mimeData()
        if "action" in m.formats() and m.data("action") == "window_drag":
            event.acceptProposedAction()
    
    def dropEvent(self, event):
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
            widget.addToContainer(self)
    
    def _tabCloseRequested(self, index):
        widget = self.tabwidget.widget(index)
        self.tabwidget.removeTab(index)
        widget.close()
        widget.deleteLater()
        if not self.tabwidget.count():
            self.deleteLater()
        
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
                tabcontainer.resize(self.sizeHint())
                TabContainer.refs.add(tabcontainer)
        if isinstance(tabcontainer, TabContainer):
            self.addToContainer(tabcontainer)
        signal_connect(self, SIGNAL("destroyed()"), lambda: log_info("destroyed"))
    def setupWidgets(self):
        """Override this."""
        self.setCentralWidget(QWidget(self))
        _layout = QVBoxLayout(self.centralWidget())
        self.centralWidget().setLayout(_layout)
        _layout.setContentsMargins(0,0,0,0)
        self.centralWidget().layout().addWidget(QLabel("This is normal text", self))
        
    def removeFromContainer(self):
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
    def addToContainer(self, tabcontainer):
        self.setWindowFlags(Qt.Widget)
        if self.tabcontainer:
            self.removeFromContainer()
        self.tabcontainer = tabcontainer
        self.tabcontainer.tabwidget.addTab(self, self.title)

    def keyPressEvent(self, event):
        if not (Qt.Key_1 <= event.key() <= Qt.Key_9 and
                event.modifiers() & Qt.AltModifier and self.tabcontainer):
            return
        requested = abs(Qt.Key_0-event.key())-1
        self.tabcontainer.tabwidget.setCurrentIndex(requested)
    def activateWindow(self):
        QMainWindow.activateWindow(self)
        self.raise_()
        if self.tabcontainer:
            self.tabcontainer.activateWindow()
            self.tabcontainer.raise_()
    
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
    p1 = _TestWidget(tabcontainer = t, title="first" * 3)
    p2 = _TestWidget(tabcontainer = t, title="second" * 3)
    t.show()
    t.resize(500,500)
    app.exec_()