#!/usr/bin/env python
import sys
sys.path.append("../")
import yobotproto
from yobotclass import YobotAccount
from client_support import YCAccount, YBuddylist, YBuddy, YCRequest, SimpleNotice
from debuglog import log_debug, log_info, log_err, log_crit, log_warn
from cgi import escape as html_escape
import main_auto
import sendjoin_auto
import chatwindow_auto
import notification
import logbrowser
import logdlg
import time
import buddy_entry
import lxml.html
import status_dialog
from html_fmt import simplify_css, process_input, insert_smileys
import smileys_rc
from modeltest import ModelTest

import traceback

from PyQt4 import QtCore, QtGui

#here be dragons:
from PyQt4.QtGui import (QComboBox, QMainWindow, QStandardItemModel, QStandardItem,
                         QIcon, QPixmap, QImage, QPainter, QDialog, QMessageBox,
                         QApplication, QFont, QTextEdit, QColorDialog, QPalette,
                         QListWidget, QListWidgetItem, QStyledItemDelegate,
                         QStyleOptionViewItem, QRegion, QWidget, QBrush, QStyle,
                         QPen, QPushButton, QStyleOption, QMenu, QAction, QCursor,
                         QTreeView, QLineEdit)

from PyQt4.QtCore import (QPoint, QSize, QModelIndex, Qt, QObject, SIGNAL, QVariant,
                          QAbstractItemModel, QRect, QRectF, QPointF)

signal_connect = QObject.connect

CHAT, IM = (1,2)
INDEX_ACCT, INDEX_BUDDY = (1,2)
PROTO_INT, PROTO_NAME = (1,2)
NOTICE, ERROR, DIALOG = (1,2,3)
ROLE_ACCT_OBJ = Qt.UserRole + 2
ROLE_SMALL_BUDDY_TEXT = Qt.UserRole + 3

status_icon_cache = {}
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

def proto_name_int(proto, type):
    """-> (proto_name, proto_int)"""
    proto_name = None
    proto_int = None
    if type == PROTO_INT:
        proto_int = proto
        proto_name = IMPROTOS_BY_CONSTANT[proto_int]
    else:
        proto_name = proto
        proto_int = IMPROTOS_BY_NAME[proto_name]
        
    return (proto_name, proto_int)

def getIcon(name):
    return QtGui.QIcon.fromTheme(name, QIcon(":/icons/icons/"+name.lower()))


def getProtoStatusIcon(name, proto_int=None):
    """Creates a nice little overlay of the status and the protocol icon.
    Returns QIcon"""
    status_icon = getIcon(name)
    if not proto_int:
        return status_icon
    else:
        ret = status_icon_cache.get((name, proto_int), None)
        if ret:
            return ret
        proto_name, _ = proto_name_int(proto_int, PROTO_INT)
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
        status_icon_cache[(name, proto_int)] = QIcon(QPixmap.fromImage(combined_pixmap))
        return status_icon_cache[(name, proto_int)]
        
def mkProtocolComboBox(cbox):
    """Stores human readable improto names along with their yobt constants"""
    for proto_constant, proto_name in IMPROTOS_BY_CONSTANT.items():
        icon = getProtoStatusIcon(proto_name)
        cbox.addItem(icon, proto_name, proto_constant)

class BuddyItemDelegate(QStyledItemDelegate):
    largeEntryIcon = (32, 32)
    
    def __init__(self, parent):
        QStyledItemDelegate.__init__(self)
        self.qw = QWidget()
        self.be = buddy_entry.Ui_be()
        self.be.setupUi(self.qw)
    
    def sizeHint(self, option, index):
        if not index.isValid():
            return QSize(-1, -1)
        self._populateWidget(index)
        return self.qw.size()
    
    
    #do away with a widget.. try something else...
    
    def _populateWidget(self, index):
        """This should go.. not using this anymore"""
        qw = self.qw
        be = self.be
        be.status.clear()
        be.name.clear()
        be.protostatus.clear()
        be.buddyicon.clear()

        item = index.internalPointer()
                
        #if item.icon:
        #    buddyicon = QPixmap()
        #    buddyicon.loadFromData(item.icon)
        #    buddyicon = buddyicon.scaled(QSize(*self.largeEntryIcon),Qt.KeepAspectRatio)
            
        protostatus_icon = index.data(Qt.DecorationRole)
        if protostatus_icon and protostatus_icon.canConvert(QVariant.Icon):
            icon = QIcon(protostatus_icon)
            be.protostatus.setPixmap(icon.pixmap(*self.largeEntryIcon))
        
        font_style = index.data(Qt.FontRole)
        if font_style and font_style.canConvert(QVariant.Font):
            font = QFont(font_style)
            be.name.setFont(font)
        be.name.setText(index.data().toString())
        
        status_message = index.data(ROLE_SMALL_BUDDY_TEXT)
        if status_message.canConvert(QVariant.String):
            status_message = status_message.toString()
            font_style = QFont()
            font_style.setPointSize(8)
            be.status.setFont(font_style)
            be.status.setText(status_message)
            
    
    def _paintDirect(self, painter, option, index):
        painter.save()
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.brush(QPalette.Highlight))
            
        self._populateWidget(index)
        #protostatus..

        protostatus = index.data(Qt.DecorationRole)
        if protostatus and protostatus.canConvert(QVariant.Icon):
            protostatus = QIcon(protostatus).pixmap(*self.largeEntryIcon)
            #get target rect..
            target_rect = QRect(option.rect.topLeft(), QSize(*self.largeEntryIcon))
            source_rect = QRect(0,0,*self.largeEntryIcon)
            
            painter.drawPixmap(target_rect,protostatus,source_rect)
        #first get the font..
        font_style = index.data(Qt.FontRole)
        if font_style and font_style.canConvert(QVariant.Font):
            font_style = QFont(font_style)
        else:
            font_style = QFont()
        painter.save()
        painter.setFont(font_style)
        text_begin = QPoint(option.rect.left() + self.largeEntryIcon[0] + 2, option.rect.top()+14)
        painter.drawText(text_begin, index.data().toString())
        painter.restore()
        
        status_message = index.data(ROLE_SMALL_BUDDY_TEXT)
        if status_message.canConvert(QVariant.String):
            status_message = status_message.toString()
            font_style = QFont()
            font_style.setPointSize(8)
            painter.save()
            painter.setFont(font_style)
            
            #now the color...
            color = option.palette.color(QPalette.Disabled, QPalette.WindowText)
            painter.setPen(QPen(color))
            text_begin = QPoint(option.rect.left() + self.largeEntryIcon[0] + 5, option.rect.bottom()-2)
            painter.drawText(text_begin, status_message)
            painter.restore()
            
        
        #finally.. the buddy icon...
        item = index.internalPointer()
        if item.icon:
            #log_err("have icon")
            buddyicon = QPixmap()
            buddyicon.loadFromData(item.icon)
            if not buddyicon.isNull():
                buddyicon = buddyicon.scaled(QSize(*self.largeEntryIcon),Qt.KeepAspectRatio)
                if not buddyicon.isNull():
                    target_rect = QRect(
                        option.rect.right()-self.largeEntryIcon[0], option.rect.top(), *self.largeEntryIcon)
                    source_rect = QRect(0,0,*self.largeEntryIcon)
                    painter.drawPixmap(target_rect, buddyicon, source_rect)
                else:
                    #log_err("scale failed")
                    pass
            else:
                #log_err("pixmap is NULL, %10s", item.icon)
                pass
        
        QApplication.style().drawPrimitive(QStyle.PE_PanelItemViewRow, option, painter)

        painter.restore()
        
    def _paintWidget(self, painter, option, index):
        self._populateWidget(index)
        #put the right palette
        self.qw.setPalette(option.palette)
        self.qw.setAutoFillBackground(False)
        if option.state & QStyle.State_Selected:
            log_debug( "selected")
            self.qw.setBackgroundRole(QPalette.Highlight)
        else:
            self.qw.setBackgroundRole(QPalette.Base)
        p = QPixmap(self.qw.size())
        self.qw.render(p)
        painter.drawPixmap(option.rect, p)

    def paint(self, painter, option, index):
        if not index.isValid():
            return
        
        self._paintDirect(painter, option, index)
        
class AccountModel(QAbstractItemModel):
    def __init__(self, backend):
        """The backend should be iterable and indexable. The backend itself
        must contain list of blist objects which should also be iterable and indexable.
        Additionally, each item should have a status, status_message, and name attribute
        """
        self.IDSTR="hi"
        super(AccountModel, self).__init__()
        self.backend = backend
        
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
        #if not self.hasIndex(row, column, parent):
        #    return QModelIndex()
        if column != 0 or row <0:
            return QModelIndex()
        
        parent_item = parent.internalPointer()
        #log_err(parent_item)
        
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
        #except (ValueError, AttributeError), e:
        #    log_warn(e)
        #    raise
        #    pass
        #    #return QModelIndex()
        
        #return index of the buddy.. this is tough..
        #log_err("got second level item", obj)
        ret = self.createIndex(obj.parent.index, 0, obj.parent)
        #log_err("returning index with data", obj.parent)
        return ret
            
    def rowCount(self, index = QModelIndex()):
        #if index.column() > 0:
        #    log_debug("returning 0 for column > 0")
        #    return 0
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
                        
class AccountInputDialog(QDialog):
    def __init__(self, model, parent=None, type=None):
        QDialog.__init__(self, parent)
        widgets = sendjoin_auto.Ui_Dialog()
        widgets.setupUi(self)
        widgets.account.setModel(model)
        self.widgets = widgets
        self.model = model
        signal_connect(self, SIGNAL("accepted()"), self.dialogDone)
        self.type = type
    
    def dialogDone(self):
        acct_obj = self.model.index(self.widgets.account.currentIndex()).internalPointer()
        target  = self.widgets.target.text()
        log_debug( "account: ", acct_obj, " target: ", target)
        self.action(acct_obj, target, self.type)
        #do something...
        
    def action(self, acct_obj, target, type):
        #FIXME: add proto key
        """To be overridden.. this will be passed the resulting account object
        and target"""
        pass

    
class SendJoinDialog(AccountInputDialog):
    """Utility dialog to open a conversation with a user or chatroom"""
    def __init__(self, model, parent=None, type=IM):
        super(SendJoinDialog,self).__init__(model, parent, type)
        txt = "Send Message" if type == IM else "Join Room"
        self.setWindowTitle(txt)
        self.widgets.target_label.setText("To" if type == IM else "Room")

class UserAddDialog(AccountInputDialog):
    def __init__(self, model, parent = None, type = None):
        super(UserAddDialog, self).__init__(model, parent, type)
        txt = "Add User"
        self.setWindowTitle(txt)
        self.widgets.target_label.setText("ID: ")
    def action(self, acct_obj, target, _null):
        acct_obj.addUser(str(target))


class DisconnectDialog(AccountInputDialog):
    def __init__(self, model, parent=None, server=False):
        super(DisconnectDialog, self).__init__(model, parent)
        self.widgets.target.hide()
        self.widgets.target_label.hide()
        title = "Disconnect account from "
        title += "client" if not server else "server"
        self.setWindowTitle(title)
        self.fromServer = server
    def action(self, acct_obj, _null, _null2):
        acct_obj.disconnect(self.fromServer)

class ChatWindow(QMainWindow):
    """This class is quite dumb, but it does contain client hooks to get and send
    messages"""
    defaultBacklogCount = 50
    def __init__(self, client, parent=None, type=IM, acct_obj=None, target=None,
                 factory=None, initial_text="",):
        self.users = {} #dict containing the name of the user mapped to the model object..
        self.ignore_list = set()
        
        if not target or not acct_obj:
            log_err( "must have target and account for chatwindow")
            return
        QMainWindow.__init__(self, parent)
        self.type = type
        self.target = target
        self.account = acct_obj
        
        self.widgets = chatwindow_auto.Ui_w_chatwindow()
        
        self.widgets.setupUi(self)
        self.setWindowTitle(target)
        #and some key press events..
        self.widgets.input.keyPressEvent = self._inputKeyPressEvent
        self.widgets.input.setHtml("")
        self.widgets.convtext.setHtml(initial_text)
        if type == CHAT:
            self.widgets.userlist.show()
            self.widgets.menuView.addAction(self.widgets.actionShow_User_List)
            signal_connect(self.widgets.actionLeave, SIGNAL("activated()"), self.leaveRoom)
            
        elif type == IM:
            self.widgets.userlist.hide()
            signal_connect(self.widgets.actionShow_Backlog, SIGNAL("activated()"),
                           lambda: self.account.getBacklog(self.target, self.defaultBacklogCount))
            #todo: use a dialog for this, perhaps...
            
        self.current_action_target = ""
        self.widgets.userlist.clear()
        self.factory = factory
        self._init_input()
        self._init_menu()
    def _init_input(self):
        #bold
        def setbold(weight):
            self.widgets.input.setFontWeight(75 if weight else 50)
        signal_connect(self.widgets.bold, SIGNAL("toggled(bool)"),setbold)
        
        #color handling
        def choosecolor():
            def _onClicked(color):
                self.widgets.input.setTextColor(color)
                self.widgets.fg_color.setStyleSheet("background-color: '%s'" % (color.name()))
            cdlg = QColorDialog(self)
            signal_connect(cdlg, SIGNAL("colorSelected(QColor)"), _onClicked)
            ret = cdlg.open()
        signal_connect(self.widgets.fg_color, SIGNAL("clicked()"), choosecolor)
        fgcolor = self.widgets.input.textColor().name()
        self.widgets.fg_color.setStyleSheet("background-color: '%s'" % (fgcolor,))
        
        #fontsize handling
        current_size = int(self.widgets.input.currentFont().pointSize())
        def _setSize(i):
            try:
                self.widgets.input.setFontPointSize(float(i))
            except Exception, e:
                log_err(e)
        signal_connect(self.widgets.fontsize, SIGNAL("valueChanged(int)"), _setSize)
        
        #for updating the formatting buttons
        signal_connect(self.widgets.input, SIGNAL("currentCharFormatChanged(QTextCharFormat)"),
                       self._currentCharFormatChanged)
                        
    def _init_menu(self):
        if not self.type == CHAT:
            return
        menu = QMenu()
        self._action_newmsg = menu.addAction(
            QIcon(":/icons/icons/message-new.png"), "Send IM")
        self._action_ignore_tmp = menu.addAction(
            QIcon(":/icons/res/16x16/actions/dialog-cancel.png"), "Ignore (from chat)")
        self._action_ignore_perm = menu.addAction(
            QIcon(":/icons/res/16x16/actions/dialog-cancel.png"), "Ignore (server)")
        
        if self.factory:
            signal_connect(self._action_newmsg, SIGNAL("activated()"),
                           lambda: self.factory(target = self.current_action_target,
                                                account = self.account, type = self.type))
            signal_connect(self.widgets.userlist, SIGNAL("itemDoubleClicked(QListWidgetItem*)"),
                           lambda item: self.factory(
                            target = item.text(), account = self.account, type = self.type))
    
        signal_connect(self._action_ignore_tmp, SIGNAL("activated()"),
                       lambda: self.ignore_list.add(self.current_action_target))
        self.userActionMenu = menu
        def _anchorClicked(link):
            link = str(link.toString())
            if link.startswith("YOBOT_INTERNAL"):
                user = link.split("/", 1)[1]
                if user:
                    self.current_action_target = user
                    self.userActionMenu.exec_(QCursor().pos())
        signal_connect(self.widgets.convtext, SIGNAL("anchorClicked(QUrl)"),
                       _anchorClicked)
        
        def _userlistContextMenu(point):
            self.current_action_target = self.widgets.userlist.indexAt(point).data()
            self.userActionMenu.exec_(QCursor().pos())
        signal_connect(self.widgets.userlist, SIGNAL("customContextMenuRequested(QPoint)"),
               _userlistContextMenu)
            
    
    def _currentCharFormatChanged(self,format):
        self.widgets.font.setCurrentFont(format.font())
        self.widgets.fontsize.setValue(int(format.fontPointSize()))
        self.widgets.bold.setChecked(format.fontWeight() >= 75)
        self.widgets.italic.setChecked(format.fontItalic())
        self.widgets.underline.setChecked(format.fontUnderline())
        self.widgets.fg_color.setStyleSheet("background-color: '%s'" % (format.foreground().color().name(),))
                
    def _inputKeyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        if key== Qt.Key_Return:
            txt = self.widgets.input.toHtml()
            if not txt:
                return
            log_warn(txt)
            txt = simplify_css(str(txt))
            log_warn(txt)
            self.sendMsg(txt)
            self.widgets.input.clear()
            return
        if key == Qt.Key_Backspace:
            log_debug("backspace")
            self.widgets.input.textCursor().deletePreviousChar()
                #log_debug("at beginning")
            return
        if modifiers & Qt.CTRL:
            print "control"
            if key == Qt.Key_BracketLeft:
                self.widgets.fontsize.stepBy(-1)
                return
            elif key == Qt.Key_BracketRight:
                self.widgets.fontsize.stepBy(1)
                return
        
        QTextEdit.keyPressEvent(self.widgets.input,event)    
    
    def sendMsg(self, txt):
        chat = True if self.type == CHAT else False
        self.account.sendmsg(self.target, str(txt), chat=chat)
        
    def gotMsg(self, msg_obj):
        #get time..
        if msg_obj.who in self.ignore_list:
            return
        msg_str = "<a href='YOBOT_INTERNAL/%s'>" % (msg_obj.who)
        msg_str += "(%s) " % (msg_obj.timeFmt,) if self.widgets.actionTimestamps.isChecked() else ""
        msg_str += "<font color='mediumblue'><b>%s</b></font></a>: " % (msg_obj.who,)
        formatted = process_input(msg_obj.txt)
        formatted = insert_smileys(formatted, self.account.improto, ":smileys/smileys", 24, 24)
        log_debug(formatted)
        msg_str += formatted
        self.widgets.convtext.append(msg_str)
    
    def userJoined(self, user):
        if self.users.get(user): return
        u = QListWidgetItem()
        u.setText(user)
        self.widgets.userlist.addItem(u)
        self.users[user] = u
    def userLeft(self, user):
        u = self.users.get(user)
        if not u: return
        self.widgets.userlist.removeItemWidget(u)
        self.users.pop(u,"")
        
    def leaveRoom(self):
        self.account.leaveRoom(self.target)    

class StatusDialog(object):
    def __init__(self, status_mappings, accept_fn):
        self.qd = QDialog()
        self.widgets = status_dialog.Ui_status_dialog()
        self.widgets.setupUi(self.qd)
        self.widgets.message.paintEvent = self._paintEvent
        self.accept_fn = accept_fn
        for k, v in status_mappings.items():
            icon, status_int = v
            self.widgets.status_list.addItem(icon, k, status_int)
        signal_connect(self.qd, SIGNAL("accepted()"), self._accept_wrap)
    
    def show(self):
        self.qd.show()
        
    def _accept_wrap(self):
        message = self.widgets.message.text()
        _sl = self.widgets.status_list
        status_type = _sl.itemData(_sl.currentIndex()).toPyObject()
        if not status_type:
            log_warn("don't have status type")
            return
        self.accept_fn(status_type, str(message))
        
    def _paintEvent(self, event):
        QLineEdit.paintEvent(self.widgets.message, event)
        if not self.widgets.message.text():
            qp = QPainter(self.widgets.message)
            r = event.rect()
            margins = self.widgets.message.getTextMargins()
            r.adjust(*margins)
            qp.setPen(self.widgets.message.palette().color(QPalette.Dark))
            qp.drawText(r, Qt.AlignCenter | Qt.AlignVCenter, "Status Message..")
            

class NotificationBox(object):
    def __init__(self, qdockwidget, qstackedwidget):
        self.reqs = {}
        self.qdw = qdockwidget
        self.qsw = qstackedwidget
        while self.qsw.count() > 0:
            self.qsw.removeWidget(self.qsw.currentWidget())
        self.qdw.hide()
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
        #FIXME: make nice fields for title, primary, and secondary
        txt=("<center><b>"+ycreqobj.title+"</b><br>"+
             "<i>"+ycreqobj.primary+
             "</i></center>"+ycreqobj.secondary)
        notice_widget.message.append(txt)
        log_debug(txt)
        #txt = "::".join([ycreqobj.primary, ycreqobj.secondary])
        #notice_widget.message.append(txt)
        notice_widget.message.setBackgroundRole(QPalette.Window)
        sb = notice_widget.message.verticalScrollBar()
        sb.setMaximumWidth(12)
        
        signal_connect(notice_widget.next, SIGNAL("clicked()"), lambda: self.navigate(next=True))
        signal_connect(notice_widget.prev, SIGNAL("clicked()"), lambda: self.navigate(next=False))
        
        self.qsw.show()
        self.qdw.show()
        self.qsw.addWidget(qw)
        self.qsw.setCurrentWidget(qw)


class _LogGroup(object):
    def __init__(self, lw_item, acct_obj, name):
        self.lw_item = lw_item
        self.txt = ""
        self.acct_obj = acct_obj
        self.name = name
        
class LogBrowser(QMainWindow):
    def __init__(self, parent=None, newmsgfactory=None, title="Log"):
        QMainWindow.__init__(self, parent)
        qw = QWidget()
        self.widgets = logbrowser.Ui_logbrowser()
        self.widgets.setupUi(qw)
        self.setCentralWidget(qw)
        self.qw = qw
        self.entries_by_acct_name = {} #as so: entries[aacount, target] -> _LogGroup object
        self.entries_by_lwitem = {} #[lwitem] -> account, target
        signal_connect(self.widgets.userlist,
                       SIGNAL("currentItemChanged(QListWidgetItem*, QListWidgetItem*)"),
                       self._showMessages)
        signal_connect(self.widgets.userlist, SIGNAL("itemDoubleClicked(QListWidgetItem*)"),
                       self._mknewmsg)
        self.newmsgfactory = newmsgfactory
        self.setWindowTitle(title)
        self.widgets.convtext.clear()
        self.widgets.userlist.clear()
        self.show()
    def addEntry(self, acct_obj, name, msg_obj):
        group = self.entries_by_acct_name.get((acct_obj, name))
        log_err(name)
        if not group:
            _lw_item = QListWidgetItem(getProtoStatusIcon(name, acct_obj.improto),
                                  name, parent = self.widgets.userlist)
            group = _LogGroup(_lw_item, acct_obj, name)
            self.entries_by_acct_name[(acct_obj, name)] = group
            self.entries_by_lwitem[group.lw_item] = group
        #apply formatting
        msg_str = "(%s) " % (msg_obj.timeFmt,)
        msg_str += "<font color='mediumblue'><b>%s</b></font>: " % (name,)
        formatted = process_input(msg_obj.txt)
        formatted = insert_smileys(formatted, acct_obj.improto, ":smileys/smileys", 24, 24)
        formatted = msg_str + formatted + "<br>" #for some reason line breaks are missing
        #add to our viewer
        group.txt += formatted
        if self.widgets.userlist.currentItem() == group.lw_item:
            self.widgets.convtext.append(formatted)
    def _showMessages(self, lwitem, _):
        if not lwitem:
            return
        self.widgets.convtext.clear()
        self.widgets.convtext.append(self.entries_by_lwitem[lwitem].txt) #group.txt
    def _mknewmsg(self, lwitem):
        if not lwitem:
            return
        if not self.newmsgfactory:
            return
        info = self.entries_by_lwitem[lwitem]
        self.newmsgfactory(info.acct_obj, info.name, initial_text = info.txt)
            
class YobotGui(object):
    chats = {} #chats[account,target]->ChatWindow instance
    def __init__(self, client):
        "Client should have a ... shit.."
        self.client = client
        log_debug( "__init__ done")
        self.target_account = None
    def init_backend(self, backend):
        self.datamodel = AccountModel(backend)
    ######################      PRIVATE HELPERS     ###########################

    def _showConnectionDialog(self):
        if self.mw_widgets.conninput.isVisible():
            return
        self.mw_widgets.w_username.setText("")
        self.mw_widgets.w_password.setText("")
        self.mw_widgets.conninput.show()
        
    def _disconnectAccount(self, acct, server=False):
        acct.disconnect(server)
    
    def _requestConnection(self):
        user, passw = (self.mw_widgets.w_username.text(),
                                    self.mw_widgets.w_password.text())
        if not user or not passw:
            msg = QMessageBox()
            msg.setIcon(msg.Critical)
            msg.setText("Username or password is empty!")
            msg.setWindowTitle("Missing Input!")
            msg.exec_()
            return
        
        improto_list = self.mw_widgets.w_improto
        improto = improto_list.model().index(improto_list.currentIndex(), 0,QModelIndex()).data(Qt.UserRole).toPyObject()
        log_debug( improto)
        try:
            self.client.connect(user, passw, improto)
        except AttributeError, e:
            log_warn( e)
        self.mw_widgets.statusbar.showMessage("connecting " + user)
                
    def _showAbout(self):
        msg = QMessageBox()
        msg.setIconPixmap(QPixmap(":/yobot_icons/icons/custom/yobot_48_h"))
        msg.setText("Yobot (C) 2010 by M. Nunberg. Licensed under the GPLv2, see LICENSE for more information")
        msg.setWindowTitle("Yobot")
        msg.exec_()
        
    def _buddyClick(self, index):
        obj = index.internalPointer()
        if not hasattr(obj, "account"): #account
            #log_debug( "not processing account ops on row %d column %d" % (index.row(), index.column()))
            return
        log_debug( obj)
        acct = obj.account
        target = obj.name
        self._openChat(acct, target, IM)
        
    def _blistContextMenu(self, point):
        index = self.mw_widgets.blist.indexAt(point)
        item = index.internalPointer()
        if index.parent().isValid():
            buddy = item
            signal_connect(self.mw_widgets.actionSendMessage, SIGNAL("activated()"),
                           lambda: self._openChat(buddy.account, buddy.name, IM))
            def _delconfirm(user):
                msgbox = QMessageBox()
                msgbox.setText(("Are you sure you wish to remove %s from"
                                " your buddy list?" % user))
                msgbox.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
                ret = msgbox.exec_()
                if ret == QMessageBox.Yes:
                    buddy.account.delUser(user)
            signal_connect(self.mw_widgets.actionDelete, SIGNAL("activated()"),
                           lambda: _delconfirm(buddy.name))
            self.buddyContextMenu_w.exec_(self.mw_widgets.blist.mapToGlobal(point))
        else:
            self.target_account = item
            self.accountContextMenu_w.exec_(self.mw_widgets.blist.mapToGlobal(point))
            
            
    def _openChat(self, acct, target, type, popup = False):
        #find an old window...
        target = str(target)
        window = self.chats.get((acct, target))
        if window:
            return
        
        self.chats[(acct, target)] = ChatWindow(self.client, type=type, parent=self.mw,
                                                acct_obj=acct, target=target)
        self.chats[(acct, target)].activateWindow()
        def _closeEvent(_QCloseEvent_null):
            "Remove window from the window list when closed"
            self.chats.pop((acct, target))
        self.chats[(acct, target)].closeEvent = _closeEvent
        self.chats[(acct, target)].show()
        self.chats[(acct, target)].activateWindow()
        log_info( "created chat with type %d, target %s" % (type, target))
        log_debug( self.chats)
        
    def _logBrowserAppend(self, acct_obj, name, msg, title="Log"):
        if not self.logbrowser:
            self.logbrowser = LogBrowser(title=title)
            def _onClose(event):
                super(LogBrowser, self.logbrowser).closeEvent(event)
                self.logbrowser = None
            self.logbrowser.closeEvent = _onClose
        self.logbrowser.addEntry(acct_obj, name, msg)
            
    def _sendjoin(self, type):
        dlg = SendJoinDialog(self.datamodel,parent=self.mw,type=type)
        dlg.action = self._openChat if type == IM else self._joinreq
        dlg.show()
    
    def _joinreq(self, acct, room, type=CHAT):
        self._openChat(acct, room, CHAT)
        acct.joinchat(room)
        
    def _mwCloseEvent(self, event):
        QMainWindow.closeEvent(self.mw, event)
        self.client.uiClosed()
        
    def _disconnect(self, fromServer):
        dlg = DisconnectDialog(self.datamodel, server=fromServer)
        dlg.show()
        
    def _gui_init(self):
        #make the widgets..
        self.mw = QMainWindow()
        self.mw.closeEvent = self._mwCloseEvent
        self.mw.setWindowIcon(QIcon(":/yobot_icons/icons/custom/yobot_24_h"))
        self.mw_widgets = main_auto.Ui_MainWindow()        
        w = self.mw_widgets
        
        w.setupUi(self.mw)
        w.blist.hide()
        w.conninput.show()

        #add the model for the protocol and buddy lists
        mkProtocolComboBox(w.w_improto)
        w.blist.show()
        w.blist.setModel(self.datamodel)
        
        self.datamodel.blist = w.blist
        self.delegate = BuddyItemDelegate(w.blist)
        w.blist.setItemDelegate(self.delegate)
        self.buddyContextMenu_w = QMenu()
        for a in ("actionAppearHiddenToContact",
                  "actionSendMessage",
                  "actionDelete"):
            self.buddyContextMenu_w.addAction(getattr(w, a))
        w.blist.setContextMenuPolicy(Qt.CustomContextMenu)
        signal_connect(w.blist, SIGNAL("customContextMenuRequested(QPoint)"), self._blistContextMenu)
        
        
        self.accountContextMenu_w = QMenu()
        def _statusChange(status, message = ""):
            if self.target_account:
                self.target_account.statusChange(status, message)
        #mirror the same set of actions for custom messages:
        _d_status = {}
        for k, v in STATUS_TYPE_MAPS.items():
            action = getattr(w, "actionStatus" + k)
            self.accountContextMenu_w.addAction(action)
            signal_connect(action, SIGNAL("activated()"), lambda v=v: _statusChange(v))
            _d_status[k] = (action.icon(), v)
        self.status_change_dialog = StatusDialog(_d_status,
            lambda status, message: self.target_account.statusChange(status, message))
        self.accountContextMenu_w.addSeparator()
        self.accountContextMenu_w.addAction(w.actionStatusCustom)
        signal_connect(w.actionStatusCustom, SIGNAL("activated()"), self.status_change_dialog.show)
        
        self.notifications = NotificationBox(w.noticebox, w.notices)
        #connect signals...
        signal_connect(w.blist, SIGNAL("doubleClicked(QModelIndex)"),
               self._buddyClick)
        
        signal_connect(w.w_connect, SIGNAL("clicked()"), self._requestConnection)
        signal_connect(w.w_username, SIGNAL("returnPressed()"), self._requestConnection)
        signal_connect(w.w_password, SIGNAL("returnPressed()"), self._requestConnection)
        signal_connect(w.actionNewconn, SIGNAL("activated()"), self._showConnectionDialog)
        signal_connect(w.actionAbout, SIGNAL("activated()"), self._showAbout)
        signal_connect(w.actionSend_IM, SIGNAL("activated()"), lambda: self._sendjoin(IM))
        signal_connect(w.actionJoin_Room, SIGNAL("activated()"), lambda: self._sendjoin(CHAT))
        signal_connect(w.actionAddUser, SIGNAL("activated()"),
                       lambda: UserAddDialog(self.datamodel, parent=self.mw).show())
        signal_connect(w.actionDisconnect_Account_Client, SIGNAL("activated()"),
                       lambda: DisconnectDialog(
                        self.datamodel, parent=self.mw, server=False).show())
        signal_connect(w.actionDisconnect_Account_Server, SIGNAL("activated()"),
                       lambda: DisconnectDialog(
                        self.datamodel, parent=self.mw, server=True).show())
        
        #self.testview = QTreeView()
        #self.testview.setModel(self.datamodel)
        #self.testview.show()
        self.logbrowser = None

    #########################   PUBLIC      ###################################
    def gui_init(self):
        """After a QApplication has been set and the main loop has been initialized,
        call this"""
        self._gui_init()
        
    def accountConnected(self, acct_obj):
        """Network end calls this to notify that the account has been connected
        It will receive an account object which must have the following implemented:
        attr: user -> the account name
        attr: improto -> the protocol ID (yobot constant)
        method: sendmsg(destination, txt)
        method: joinchat(room)
        
        The account object will be added to the account list, along with a node
        for the menus/buddy lists...
        """
        if not getattr(self, "modeltest", False):
            self.modeltest = ModelTest(self.datamodel, self.mw)

        self.mw_widgets.statusbar.showMessage("Connected: "+ acct_obj.user)
        self.mw_widgets.conninput.hide()
        self.mw_widgets.blist.show()
        #fetch offline messages
        acct_obj.getOfflines()
        
    def gotMessage(self, acct_obj, msg_obj):
        log_debug(msg_obj)
        #FIXME: hack..
        name = msg_obj.name
        if acct_obj.improto == yobotproto.YOBOT_JABBER:
            name = name.split("/", 1)[0]

        if (msg_obj.yprotoflags & yobotproto.YOBOT_OFFLINE_MSG or
            (msg_obj.yprotoflags & yobotproto.YOBOT_BACKLOG and
             (acct_obj, name) not in self.chats)):
            #open a new logbrowser..
            self._logBrowserAppend(acct_obj, name, msg_obj,
                                   title="Offline Messages" if msg_obj.yprotoflags & yobotproto.YOBOT_OFFLINE_MSG else "Log")
            return
        
        type = CHAT if msg_obj.isChat else IM
        self._openChat(acct_obj, name, type)
        self.chats[acct_obj, name].gotMsg(msg_obj)
        
    def chatUserJoined(self, acct_obj, room, user):
        c = self.chats.get((acct_obj,room))
        if not c: return
        c.userJoined(user)

    def chatUserLeft(self, acct_obj, room, user):
        c = self.chats.get([acct_obj, room])
        if not c: return
        c.userLeft(user)
    
    def gotRequest(self, request_obj):
        log_err(str(request_obj))
        self.notifications.addItem(request_obj)
    
    def delRequest(self, acct, refid):
        self.notifications.delItem(acct, refid)
    def connectionFailed(self, acct, txt):
        m = SimpleNotice(acct, txt)
        m.title = "Connection Failed!"
        m.isError = True
        self.notifications.addItem(m)
        
    genericNotice = gotRequest
        
        
if __name__ == "__main__":
    gui = YobotGui(None)
    gui._testgui()