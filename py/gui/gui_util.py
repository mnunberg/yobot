#!/usr/bin/env python

#various utility functions for use with PyQt, used within the yobot codebase

from PyQt4 import QtCore, QtGui

#here be dragons:
from PyQt4.QtGui import (QComboBox, QMainWindow, QStandardItemModel, QStandardItem,
                         QIcon, QPixmap, QImage, QPainter, QDialog, QMessageBox,
                         QApplication, QFont, QTextEdit, QColorDialog, QPalette,
                         QListWidget, QListWidgetItem, QStyledItemDelegate,
                         QStyleOptionViewItem, QRegion, QWidget, QBrush, QStyle,
                         QPen, QPushButton, QStyleOption, QMenu, QAction, QCursor,
                         QTreeView, QLineEdit, QButtonGroup, QGraphicsDropShadowEffect,
                         qDrawShadePanel, QGraphicsOpacityEffect, QGraphicsEffect,
                         QTransform, QColor,QLabel, QErrorMessage
                         )

from PyQt4.QtCore import (QPoint, QSize, QModelIndex, Qt, QObject, SIGNAL, QVariant,
                          QAbstractItemModel, QRect, QRectF, QPointF, QTimer,
                          QPropertyAnimation)

signal_connect = QObject.connect

import yobotproto
from yobotclass import YobotAccount
from client_support import YCAccount, YBuddylist, YBuddy, YCRequest, SimpleNotice
from debuglog import log_debug, log_info, log_err, log_crit, log_warn
from cgi import escape as html_escape

import connection_properties
import notification
import agent_connect_dlg

import yobot_interfaces



_PROTO_INT, _PROTO_NAME = (1,2)

_status_icon_cache = {}
IMPROTOS_BY_NAME={}
IMPROTOS_BY_CONSTANT={}
STATUS_ICON_MAPS = {}
#make a mapping between yobot protocol constants and human names:

for proto_name, proto_constant in (
    ("Yahoo", yobotproto.YOBOT_YAHOO),
    ("AIM", yobotproto.YOBOT_AIM),
    ("MSN", yobotproto.YOBOT_MSN),
    ("Google-Talk", yobotproto.YOBOT_GTALK),
    ("Jabber", yobotproto.YOBOT_JABBER),
    ):
    IMPROTOS_BY_CONSTANT[proto_constant] = proto_name
    IMPROTOS_BY_NAME[proto_name] = proto_constant

STATUS_ICON_MAPS = {
    yobotproto.YOBOT_EVENT_BUDDY_ONLINE: "user-online",
    yobotproto.YOBOT_EVENT_BUDDY_OFFLINE: "user-offline",
    yobotproto.YOBOT_EVENT_BUDDY_AWAY: "user-away",
    yobotproto.YOBOT_EVENT_BUDDY_BUSY: "user-busy",
    yobotproto.YOBOT_EVENT_BUDDY_INVISIBLE: "user-invisible",
    yobotproto.YOBOT_EVENT_BUDDY_IDLE: "user-away",
    yobotproto.YOBOT_EVENT_BUDDY_BRB: "user-away",
}

STATUS_TYPE_MAPS = {
    "Away" : yobotproto.PURPLE_STATUS_AWAY,
    "Available" : yobotproto.PURPLE_STATUS_AVAILABLE,
    "Invisible" : yobotproto.PURPLE_STATUS_INVISIBLE,
}

def set_bg_opacity(widget, a):
    palette = widget.palette()
    w_color = palette.color(QPalette.Window)
    b_color = palette.color(QPalette.Button)
    base_color = palette.color(QPalette.Base)
    
    w_color.setAlpha(a)
    b_color.setAlpha(a)
    base_color.setAlpha(a)
    
    new_palette = QPalette(b_color, w_color)
    new_palette.setColor(QPalette.Window, w_color)
    new_palette.setColor(QPalette.Button, b_color)
    new_palette.setColor(QPalette.Base, base_color)
    #palette.setColor(QPalette.Window, color)
    widget.setPalette(new_palette)
    
def proto_name_int(proto, type):
    """-> (proto_name, proto_int)"""
    proto_name = None
    proto_int = None
    if type == _PROTO_INT:
        proto_int = proto
        proto_name = IMPROTOS_BY_CONSTANT[proto_int]
    else:
        proto_name = proto
        proto_int = IMPROTOS_BY_NAME[proto_name]
        
    return (proto_name, proto_int)

def getIcon(name):
    return QtGui.QIcon.fromTheme(name, QIcon(":/icons/icons/"+name.lower()))


def getProtoIconAndName(proto_int):
    "->(name, icon)"
    name = IMPROTOS_BY_CONSTANT.get(proto_int, "<UNKNOWN>")
    if name != "<UNKNOWN>":
        icon = getIcon(name)
    else:
        icon = QIcon
    return (name, icon)
    
    
def getProtoStatusIcon(name, proto_int=None):
    """Creates a nice little overlay of the status and the protocol icon.
    Returns QIcon"""
    status_icon = getIcon(name)
    if not proto_int:
        return status_icon
    else:
        ret = _status_icon_cache.get((name, proto_int), None)
        if ret:
            return ret
        proto_name, _ = proto_name_int(proto_int, _PROTO_INT)
        status_pixmap = status_icon.pixmap(QSize(16,16))
        proto_pixmap = getIcon(proto_name).pixmap(QSize(16,16))
        combined_pixmap = QImage(28,20, QImage.Format_ARGB32_Premultiplied)

        painter = QPainter(combined_pixmap)
        
        painter.setCompositionMode(painter.CompositionMode_Source)
        painter.fillRect(combined_pixmap.rect(), Qt.transparent)
        
        painter.setCompositionMode(painter.CompositionMode_Source)
        painter.drawPixmap(QPoint(0,0), status_pixmap)
        
        painter.setCompositionMode(painter.CompositionMode_SourceOver)
        painter.drawPixmap(QPoint(12,4), proto_pixmap)
        
        painter.end()
        #add cache
        _status_icon_cache[(name, proto_int)] = QIcon(QPixmap.fromImage(combined_pixmap))
        return _status_icon_cache[(name, proto_int)]
        
def mkProtocolComboBox(cbox):
    """Stores human readable improto names along with their yobt constants"""
    for proto_constant, proto_name in IMPROTOS_BY_CONSTANT.items():
        icon = getProtoStatusIcon(proto_name)
        cbox.addItem(icon, proto_name, proto_constant)

def widgetformatter(widget, font, color, klass="QWidget", extra=""):
    stylesheet = ((klass + "{" ) +
        ("font-weight:bold;" if font.bold() else "") +
        ("font-style:italic;" if font.italic() else "") +
        ("text-decoration:underline;" if font.underline() else "") +
        ("font-size:%dpt;" % (font.pointSize(),)) +
        ("font-family:%s;" % (font.family(),)) +
        ("color:%s;" % (color.name())) +
        (extra + "}")
        )
    log_debug(stylesheet)
    widget.setStyleSheet(stylesheet)

INDEX_ACCT, INDEX_BUDDY = (1,2)
ROLE_ACCT_OBJ = Qt.UserRole + 2
ROLE_SMALL_BUDDY_TEXT = Qt.UserRole + 3

class AccountModel(QAbstractItemModel):
    def __init__(self, backend):
        """The backend should be iterable and indexable. The backend itself
        must contain list of blist objects which should also be iterable and indexable.
        Additionally, each item should have a status, status_message, and name attribute
        """
        self.IDSTR="hi"
        super(AccountModel, self).__init__()
        #self.backend = backend
        
        self.backend = yobot_interfaces.component_registry.get_component("account-store")
        if not self.backend:
            raise Exception("couldn't find account store")
        #try to register account model:
        model = yobot_interfaces.component_registry.get_component("account-model")
        if model:
            return model
        else:
            yobot_interfaces.component_registry.register_component("account-model", self)
        
        self.acctRoot = backend
        self.blist = None
        
        #tie up some functions..
        self.backend.beginAdd = self.beginAccountAdd
        self.backend.beginRemove = self.beginAccountRemove
        self.backend.beginChildAdd = self.beginBuddyAdd
        self.backend.beginChildRemove = self.beginBuddyRemove
        
        self.backend.endAdd = self.endInsertRows
        self.backend.endRemove = self.endRemoveRows
        self.backend.dataChanged = self.statusChange
        self.backend.firstChildInserted = self._firstChange
        log_debug( "AccountModel: init done")
        def _logchanged(childindex, parentindex):
            log_err("called")
        #signal_connect(self, SIGNAL("dataChanged(QModelIndex, QModelIndex)"), _logchanged)
    
    def flags(self, index):
        return (Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable)
    
    def _firstChange(self, index):
        if self.blist:
            self.blist.setExpanded(self.index(index, 0), True)
            
    def index(self, row, column = 0, parent = QModelIndex()):
        if column != 0 or row <0:
            return QModelIndex()
        
        parent_item = parent.internalPointer()
        
        if not parent_item:
            #top level account..
            try:
                acct_obj = self.backend[int(row)]
                ret = self.createIndex(row, 0, acct_obj)
                return ret
            except (IndexError, KeyError), e:
                log_err(e)
                return QModelIndex()
                
        #if we got here.. we have a buddy item...
        assert(parent_item.parent is None)
        try:
            buddy = parent_item.blist[row]
            return self.createIndex(row, column, buddy)
        except (IndexError, KeyError), e:
            parent_chain = ""
            _p = parent
            while _p.isValid():
                parent_chain += "-> %d %d" % (_p.row(), _p.column())
                _p = _p.parent()
            log_err("Error", e, row, column, "parents", parent_chain)
            return QModelIndex()
            
    def parent(self, index):
        obj = index.internalPointer()
        if not obj:
            return QModelIndex() #no data, nothing valid
        if not index.isValid(): #or obj.parent == -1
            return QModelIndex()
            
        if not obj.parent:
            return QModelIndex()
        ret = self.createIndex(obj.parent.index, 0, obj.parent)
        return ret
            
    def rowCount(self, index = QModelIndex()):
        if not index.isValid():
            ret = len(self.backend)
        else:
            ret = index.internalPointer().childCount
        return ret
        
    def columnCount(self, index = QModelIndex()):
        if index.isValid():
            if index.internalPointer().childCount:
                return 1
            else:
                return 0
        return 1
    
            
    def data(self, index, role = Qt.DisplayRole):
        if not index.isValid():
            #log_err("returning QVariant()")
            return QVariant()
        
        #type = INDEX_BUDDY if index.parent().isValid() else INDEX_ACCT
        
        item = index.internalPointer()
        type = INDEX_BUDDY if item.parent else INDEX_ACCT
        
        if role == Qt.DisplayRole:
            return_text = item.name
            #log_err("returning",return_text)
            return QVariant(return_text)
            
        elif role == Qt.FontRole:
            font = QFont()
            if type == INDEX_ACCT:
                font.setWeight(QFont.Bold)
            return font
        
        elif role == ROLE_SMALL_BUDDY_TEXT:
            #ret = " ".join([str(i) for i in (
            #    item.status_message, index.row(),index.column(), index.parent().isValid())])
            return QVariant(item.status_message)
        
        elif role == Qt.DecorationRole:
            #get font stuff.. map the status to the right icon.. etc.
            try:
                improto = item.improto if type == INDEX_ACCT else item.account.improto
            except (AttributeError), e:
                log_err("INDEX_ACCT" if type==INDEX_ACCT else "INDEX_BUDDY")
                log_err(e)
                log_err("item", index.internalPointer(), "parent", index.parent().internalPointer())
                raise
            #see if we have a status icon available...
            status_name = STATUS_ICON_MAPS.get(item.status, None)
            if not status_name:
                return QVariant(getProtoStatusIcon(IMPROTOS_BY_CONSTANT[improto]))
            else:
                return QVariant(getProtoStatusIcon(status_name, proto_int = improto))
        return QVariant()

    #ugly hacks    
    def endInsertRows(self):
        #log_err("done")
        QAbstractItemModel.endInsertRows(self)
        self.model_dump()
    
    def endRemoveRows(self):
        #log_err("done")
        QAbstractItemModel.endRemoveRows(self)
        self.model_dump()
        
    def beginAccountAdd(self, index_no):
        #log_err("inserting account wiht index %d" % (index_no,))
        self.beginInsertRows(QModelIndex(), index_no, index_no)
        
    def beginAccountRemove(self, index_no):
        #log_err("removing account at index", index_no)
        self.beginRemoveRows(QModelIndex(), index_no, index_no)
        
    def beginBuddyAdd(self, parent_index, child_index):
        #get parent index first..
        iindex = parent_index
        parent_index = self.index(parent_index, 0)
        #log_err("inserting buddy [%d] with parent index %d VALID: %s PARENT VALID: %s" %
        #        (child_index, iindex, parent_index.isValid(), parent_index.parent().isValid()))
        self.beginInsertRows(parent_index, child_index, child_index)
    def beginBuddyRemove(self, parent_index, child_index):
        parent_index = self.index(parent_index, 0)
        self.beginRemoveRows(parent_index, child_index, child_index)
    def statusChange(self, parent_index, child_index):
        #log_err(parent_index, child_index)
        if not child_index:
            #account status:
            index = self.index(parent_index, 0)
            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
        else:
            #buddy.. find parent node...
            parent_index = self.index(parent_index, 0)
            child_index = self.index(child_index, 0, parent_index)
            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"), child_index, child_index)
        self.model_dump()
    
    def model_dump(self):
        return
        for a in self.backend:
            log_warn(a)
            for b in a.blist:
                log_warn("\t", b)
        log_err("now recursing")
        rows = self.rowCount()
        log_err("rows: ", rows)
        if rows > 0:
            for r in xrange(0, rows):
                acct_index = self.index(r)
                log_warn("Account", acct_index.internalPointer().name)
                c_rows = self.rowCount(acct_index)
                if c_rows > 0:
                    for cr in xrange(0, c_rows):
                        c_index = self.index(cr, 0, acct_index)
                        log_warn("\tBuddy", c_index.internalPointer().name)



class ConnectionWidget(QWidget):
    def __init__(self, parent = None, connect_cb = None):
        QWidget.__init__(self, parent)
        self.widgets = connection_properties.Ui_connection_widget()
        w = self.widgets
        w.setupUi(self)
        
        self.container_height_exclusive = self.sizeHint().height() - self.widgets.proxy_params.sizeHint().height()
        self.combined_height = self.sizeHint().height()
        
        self.pp_show_animation = QPropertyAnimation(self, "size", self)
        self.pp_show_animation.setDuration(100)
        self.pp_show_animation.setStartValue(QSize(self.width(), self.container_height_exclusive))
        self.pp_show_animation.setEndValue(QSize(self.width(), self.combined_height))
        
        self.pp_hide_animation = QPropertyAnimation(self, "size", self)
        self.pp_hide_animation.setDuration(100)
        self.pp_hide_animation.setStartValue(QSize(self.width(), self.combined_height))
        self.pp_hide_animation.setEndValue(QSize(self.width(), self.container_height_exclusive))
        
        mkProtocolComboBox(w.w_improto)
        w.proxy_params.proxy_type_group = QButtonGroup(w.proxy_params)
        for i in ("http", "socks4", "socks5"):
            w.proxy_params.proxy_type_group.addButton(getattr(w, "proxy_type_" + i))
        self.connect_cb = connect_cb
        if connect_cb:
            signal_connect(w.w_connect, SIGNAL("clicked()"), self.submit)
            signal_connect(w.w_username, SIGNAL("returnPressed()"), self.submit)
            signal_connect(w.w_password, SIGNAL("returnPressed()"), self.submit)
                
        @QtCore.pyqtSlot("bool", name="setVisible")
        def proxy_setVisible(b):
            if b:
                self.pp_show_animation.start()
                QTimer.singleShot(self.pp_show_animation.duration(),
                                  lambda: type(w.proxy_params).setVisible(w.proxy_params, True))
            else:
                self.pp_hide_animation.start()
                type(w.proxy_params).setVisible(w.proxy_params, False)
                
        def _hideEvent(e):
            if self.parent() and self.parent().layout():
                self.parent().layout().activate()
            type(w.proxy_params).hideEvent(w.proxy_params, e)
            
        w.proxy_params.setVisible = proxy_setVisible
        w.proxy_params.hideEvent = _hideEvent
        w.proxy_params.setVisible(False)
        signal_connect(w.show_proxy_prefs, SIGNAL("toggled(bool)"), w.proxy_params.setVisible)
        self.setAutoFillBackground(True)
        w.proxy_params.setAutoFillBackground(False)
                        
    @property
    def visible_height(self):
        if not self.widgets.proxy_params.isVisible():
            return self.container_height_exclusive
        else:
            return self.combined_height
        
    def getValues(self):
        w = self.widgets
        username = self.widgets.w_username.text()
        password = self.widgets.w_password.text()
        if not (username and password):
            msg = QMessageBox()
            msg.setIcon(msg.Critical)
            msg.setText("Username or password is empty!")
            msg.setWindowTitle("Missing Input!")
            msg.exec_()
            return None
        improto = self.widgets.w_improto.model().index(self.widgets.w_improto.currentIndex(),
                                     0,QModelIndex()).data(Qt.UserRole).toPyObject()
        
        _d_proxy_params = {"proxy_host" : None, "proxy_port": None, "proxy_type" : None,
                           "proxy_username" : None, "proxy_password" : None}
        _d_proxy_params["proxy_host"] = str(w.proxy_host.text())
        if _d_proxy_params["proxy_host"]:
            _d_proxy_params["proxy_port"] = str(w.proxy_port.text())
            _d_proxy_params["proxy_type"] = str(w.proxy_params.proxy_type_group.checkedButton().text()).lower()
            _d_proxy_params["proxy_username"] = str(w.proxy_username.text())
            _d_proxy_params["proxy_password"] = str(w.proxy_password.text())
        return (username, password, improto, _d_proxy_params)
        
    def submit(self):
        ret = self.getValues()
        if ret:
            username, password, improto, proxy_params = ret
            self.connect_cb(username, password, improto, **proxy_params)
            
    def reset(self):
        self.widgets.w_username.setText("")
        self.widgets.w_password.setText("")
        

class ShadowAndAlphaEffect(QGraphicsDropShadowEffect):
    def __init__(self, blur=15.0, transparency=0.7,
                 shadowColor = QColor(0,0,0,255), parent=None):
        QGraphicsDropShadowEffect.__init__(self, parent)
        self.setBlurRadius(blur)
        #self.setColor(shadowColor)
        self.transparency = transparency
        
    def draw(self, painter):
        src_pixmap, offset = self.sourcePixmap()
        painter.save()
        painter.setOpacity(self.transparency)
        painter.drawPixmap(offset, src_pixmap)
        painter.restore()
        
        #now find the clipping region:
        src_r = QRegion(self.sourceBoundingRect().toRect())
        effect_r = QRegion(self.boundingRect().toRect())
        
        clip_region = effect_r.subtracted(src_r)
        
        painter.save()
        painter.setClipRegion(clip_region)
        QGraphicsDropShadowEffect.draw(self, painter)
        painter.restore()

        
class OverlayConnectionWidget(ConnectionWidget):
    def __init__(self, pos_fn, cb, parent=None):
        super(type(self), self).__init__(parent, cb)
        self.setAutoFillBackground(True)
        self.animation = QPropertyAnimation(self, "size", self)
        self.effect = ShadowAndAlphaEffect(blur = 15.0, transparency = 0.90, parent = self)
        self.setGraphicsEffect(self.effect)
        self.pos_fn = pos_fn
        saved_size = None
        self._parent = parent
        
    def paintEvent(self, event):
        if self._parent:
            self.setFixedWidth(self._parent.width()-20)
        super(type(self), self).paintEvent(event)            
        painter = QPainter(self)
        qDrawShadePanel(painter, self.rect(), QPalette())
    def showEvent(self, event):
        super(type(self), self).showEvent(event)
        if not event.spontaneous():
            self.animation.setStartValue(QSize(self.width(), 0))
            self.animation.setEndValue(QSize(self.width(), self.visible_height))
            self.move(self.pos_fn())
            self.animation.start()
        
    def setVisible(self, b):
        if not b:
            self._animation = QPropertyAnimation(self, "size", self)
            self._animation.setEndValue(QSize(self.width(), 0))
            signal_connect(self._animation, SIGNAL("finished()"), lambda: super(type(self), self).setVisible(False))
            self._animation.start()
        else:
            super(type(self), self).setVisible(b)        


class NotificationBox(object):
    def __init__(self, qdockwidget, qstackedwidget, noTitleBar=True):
        self.reqs = {}
        self.qdw = qdockwidget
        self.qsw = qstackedwidget
        while self.qsw.count() > 0:
            self.qsw.removeWidget(self.qsw.currentWidget())
        self.qdw.hide()
        if noTitleBar:
            self._tmp = QWidget()
            self.qdw.setTitleBarWidget(self._tmp)
        btn_font = QFont()
        btn_font.setBold(True)
        btn_font.setPointSize(8)
        self.btn_font = btn_font
        
    def navigate(self, next = True):
        log_debug("")
        currentIndex = self.qsw.currentIndex()
        if next: #navigate to next..
            if currentIndex-1 < self.qsw.count() and currentIndex >= 0:
                self.qsw.setCurrentIndex(currentIndex+1)
        else:
            if currentIndex-1 > 0:
                self.qsw.setCurrentIndex(currentIndex-1)
    
    def addItem(self, ycreqobj):
        qw = QWidget()
        if ycreqobj.refid:
            self.reqs[(ycreqobj.acct, ycreqobj.refid)] = qw
        #setup the widget
        notice_widget = notification.Ui_Form()
        notice_widget.setupUi(qw)
        #notice_widget.iconlabel.hide()
        notice_widget.discard.hide()
        notice_widget.accept.hide()
        
        #get an icon:
        acct = ycreqobj.acct
        icon = icon = (QPixmap(":/icons/icons/help-about.png")
                       if not ycreqobj.isError else
                       QPixmap(":/icons/res/16x16/status/dialog-error.png"))
        notice_widget.iconlabel.setPixmap(icon)
        #get options..
        def _cbwrap(cb):
            #closes the notification after an action has been sent
            cb()
            self.qsw.removeWidget(qw)
            if not self.qsw.count():
                self.qsw.hide()
                self.qdw.hide()
            qw.destroy()

        for o in ycreqobj.options:
            optname, optcb, typehint = o
            b = QPushButton()
            b.setText(optname)
            b.setFont(self.btn_font)
            icon = None
            try:
                typehint = int(typehint)
            except ValueError, TypeError:
                typehint = -1
            if typehint == yobotproto.YOBOT_ACTIONTYPE_OK:
                icon = QIcon(":/icons/icons/help-about.png")
            elif typehint == yobotproto.YOBOT_ACTIONTYPE_CANCEL:
                icon = QIcon(":/icons/res/16x16/actions/dialog-close.png")
            else:
                icon = QIcon()
            b.setIcon(icon)
            
            signal_connect(b, SIGNAL("clicked()"), lambda optcb=optcb: _cbwrap(optcb))
            notice_widget.bbox.addWidget(b)
            
        accticon = getProtoStatusIcon(acct.name, acct.improto)
        if accticon:
            notice_widget.accticon.setPixmap(accticon.pixmap(24, 24))
        notice_widget.account.setText(acct.name)
        txt=("<center><b>"+ycreqobj.title+"</b><br>"+
             "<i>"+ycreqobj.primary+
             "</i></center>"+ycreqobj.secondary)
        notice_widget.message.append(txt)
        log_debug(txt)
        notice_widget.message.setBackgroundRole(QPalette.Window)
        sb = notice_widget.message.verticalScrollBar()
        sb.setMaximumWidth(12)
        
        signal_connect(notice_widget.next, SIGNAL("clicked()"), lambda: self.navigate(next=True))
        signal_connect(notice_widget.prev, SIGNAL("clicked()"), lambda: self.navigate(next=False))
        
        self.qsw.show()
        self.qdw.show()
        self.qsw.addWidget(qw)
        self.qsw.setCurrentWidget(qw)
    def delItem(self, item):
        log_err("not implemented!")

class AgentConnectDialog(QDialog):
    def __init__(self, *args, **kwargs):
        QDialog.__init__(self, *args, **kwargs)
        w = agent_connect_dlg.Ui_Dialog()
        w.setupUi(self)
        self.widgets = w
        signal_connect(self, SIGNAL("accepted()"), self._accepted)
        self.show()
        
    def _accepted(self):
        w = self.widgets
        client_operations = yobot_interfaces.component_registry.get_component("client-operations")
        if not client_operations:
            raise Exception("Couldn't get client operations")
        acct_port_string = str(w.agent_addrinfo.currentText())
        if not acct_port_string:
            QErrorMessage(self).showMessage("Address is empty")
            return False
        tmp = acct_port_string.rsplit(":", 1)
        if len(tmp) >= 2:
            address = tmp[0]
            port = int(tmp[1])
            client_operations.connectToAgent(address=address, port=port,
                                             disconnect_from_server=w.disconnect_from_server.isChecked())
        else:
            address = tmp[0]
            client_operations.connectToAgent(address=address,
                                             disconnect_from_server=w.disconnect_from_server.isChecked())
        
