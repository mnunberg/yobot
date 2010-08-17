#!/usr/bin/env python
import sys
import os
if os.name == "posix":
    sys.path.append("../")
    import yobotproto
    from yobotclass import YobotAccount
    from client_support import YCAccount, YBuddylist, YBuddy

import main_auto
import sendjoin_auto
import chatwindow_auto
import time
import string
import random
from css_sax import simplify_css

from PyQt4 import QtCore, QtGui

#here be dragons:
from PyQt4.QtGui import (QComboBox, QMainWindow, QStandardItemModel, QStandardItem,
                         QIcon, QPixmap, QImage, QPainter, QDialog, QMessageBox,
                         QApplication, QFont, QTextEdit, QColorDialog, QPalette,
                         QListWidget, QListWidgetItem)

from PyQt4.QtCore import (QPoint, QSize, QModelIndex, Qt, QObject, SIGNAL, QVariant,
                          QAbstractItemModel)

signal_connect = QObject.connect

CHAT, IM = (1,2)
INDEX_ACCT, INDEX_BUDDY = (1,2)
PROTO_INT, PROTO_NAME = (1,2)
ROLE_ACCT_OBJ = Qt.UserRole + 2

status_icon_cache = {}
IMPROTOS_BY_NAME={}
IMPROTOS_BY_CONSTANT={}
STATUS_ICON_MAPS = {}
#make a mapping between yobot protocol constants and human names:

if os.name == "posix":
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
    if os.name != "posix":
        pass
    """Stores human readable improto names along with their yobt constants"""
    for proto_constant, proto_name in IMPROTOS_BY_CONSTANT.items():
        icon = getProtoStatusIcon(proto_name)
        cbox.addItem(icon, proto_name, proto_constant)

class AccountModel(QAbstractItemModel):
    def __init__(self, backend):
        """The backend should be iterable and indexable. The backend itself
        must contain list of blist objects which should also be iterable and indexable.
        Additionally, each item should have a status, status_message, and name attribute
        """
        QAbstractItemModel.__init__(self)
        self.backend = backend
        
        self.acctRoot = backend
        
        #tie up some functions..
        self.backend.beginAdd = self.beginAccountAdd
        self.backend.beginRemove = self.beginAccountRemove
        self.backend.beginChildAdd = self.beginBuddyAdd
        self.backend.beginChildRemove = self.beginBuddyRemove
        
        self.backend.endAdd = self.endInsertRows
        self.backend.endRemove = self.endRemoveRows
        self.backend.dataChanged = self.statusChange
        print "AccountModel: init done"
        
    def index(self, row, column = 0, parent = QModelIndex()):
        #if not self.hasIndex(row, column, parent):
        #    return QModelIndex()
        if column > 0:
            return QModelIndex()
            
        if not parent.isValid():
            #top level account..
            try:
                acct_obj = self.acctRoot[row]
                return self.createIndex(row, column, acct_obj)
            except IndexError:
                return QModelIndex()
                
        #if we got here.. we have a buddy item...
        parent_item = parent.internalPointer()
        try:
            buddy = parent_item.blist[row]
            return self.createIndex(row, column, buddy)
        except IndexError:
            return QModelIndex()
            
    def parent(self, index):
        obj = index.internalPointer()
        if not index.isValid(): #or obj.parent == -1
            return QModelIndex()
        try:
            if obj.parent == -1:
                return QModelIndex()
        except (ValueError, AttributeError), e:
            pass
        
        #return index of the buddy.. this is tough..
        return self.createIndex(obj.parent.index, 0, obj.parent)
    
    def rowCount(self, index = QModelIndex()):
        if index.column() > 0:
            return 0
        if not index.isValid():
            return len(self.backend)
        else:
            return index.internalPointer().childCount
            
    def columnCount(self, index = QModelIndex()):
        return 1
    
    def data(self, index, role = Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        type = INDEX_BUDDY if index.parent().isValid() else INDEX_ACCT
        
        item = index.internalPointer()
        if role == Qt.DisplayRole:
            return_text = item.name
            if item.status_message: return_text += " [ %s ]" % (item.status_message,)
            return QVariant(return_text)
            
        elif role == Qt.FontRole:
            font = QFont()
            if type == INDEX_ACCT:
                font.setWeight(QFont.Bold)
            return font
        
        elif role == Qt.DecorationRole:
            #get font stuff.. map the status to the right icon.. etc.
            improto = item.improto if type == INDEX_ACCT else item.account.improto
            #see if we have a status icon available...
            status_name = STATUS_ICON_MAPS.get(item.status, None)
            if not status_name:
                return QVariant(getProtoStatusIcon(IMPROTOS_BY_CONSTANT[improto]))
            else:
                return QVariant(getProtoStatusIcon(status_name, proto_int = improto))
    
    #ugly hacks
    def beginAccountAdd(self, index_no):
        self.beginInsertRows(QModelIndex(), index_no, index_no)
    def beginAccountRemove(self, index_no):
        self.beginRemoveRows(QModelIndex(), index_no, index_no)
        
    def beginBuddyAdd(self, parent_index, child_index):
        #get parent index first..
        parent_index = self.index(parent_index, 0)
        self.beginInsertRows(parent_index, child_index, child_index)
    def beginBuddyRemove(self, parent_index, child_index):
        parent_index = self.index(parent_index, 0)
        self.beginRemoveRows(parent_index, child_index, child_index)
    def statusChange(self, parent_index=None, child_index=None):
        if not child_index:
            #account status:
            index = self.index(parent_index, 0)
            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
        else:
            #buddy.. find parent node...
            parent_index = self.index(parent_index, 0)
            child_index = self.index(child_index, 0, parent_index)
            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"), child_index, child_index)
            



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
        print "account: ", acct_obj, " target: ", target
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

class ChatWindow(QMainWindow):
    """This class is quite dumb, but it does contain client hooks to get and send
    messages"""
    users = {} #dict containing the name of the user mapped to the model object..
    def __init__(self, client, parent=None, type=IM, acct_obj=None, target=None):
        if not target or not acct_obj:
            print "must have target and account for chatwindow"
            return
        
        QMainWindow.__init__(self, parent)

        self.type = type
        self.target = target
        self.account = acct_obj
        self.widgets = chatwindow_auto.Ui_w_chatwindow()
        
        self.widgets.setupUi(self)
        self.setWindowTitle(target)
        
        #add some buttons.. we shouldn't be doing this here, but we don't want to
        #rely on the auto generated .ui file or _auto.py
        self.widgets.bold.setIcon(getIcon("format-text-bold"))
        self.widgets.underline.setIcon(getIcon("format-text-underline"))
        self.widgets.italic.setIcon(getIcon("format-text-italic"))
        
        #and some key press events..
        self.widgets.input.keyPressEvent = self._inputKeyPressEvent
        self.widgets.input.setHtml("")
        def setbold(weight):
            bv = None
            if weight:
                bv = 75
            else:
                bv = 50
            self.widgets.input.setFontWeight(bv)
        signal_connect(self.widgets.bold, SIGNAL("toggled(bool)"),setbold)

        if type == CHAT:
            self.widgets.userlist.show()
            self.widgets.menuView.addAction(self.widgets.actionShow_User_List)
            signal_connect(self.widgets.userlist, SIGNAL("itemDoubleClicked(QListWidgetItem)"),
                           self.userClick)
        elif type == IM:
            self.widgets.userlist.hide()
        
        def choosecolor():
            def _onClicked(color):
                self.widgets.input.setColor(color)
                self.widgets.fg_color.setPalette(QPalette(color))
            cdlg = QColorDialog(self)
            signal_connect(cdlg, SIGNAL("colorSelected()"), _onClicked)
            cdlg.open()
        signal_connect(self.widgets.fg_color, SIGNAL("clicked()"), choosecolor)
        self.widgets.fg_color.setPalette(QPalette(Qt.white))
        
    def _inputKeyPressEvent(self, event):
        if not event.key() == Qt.Key_Return:
            QTextEdit.keyPressEvent(self.widgets.input,event)
            return
        txt = self.widgets.input.toHtml()
        if not txt:
            return
        txt = simplify_css(str(txt))
        print txt
        self.sendMsg(txt)
        self.widgets.input.clear()
    
    def sendMsg(self, txt):
        chat = False
        if self.type == CHAT:
            chat = True
        self.account.sendmsg(self.target, str(txt), chat=chat)
        
    def gotMsg(self, msg_obj):
        #get time..
        msg_str = ""
        msg_str += "(%s) " % (msg_obj.timeFmt,)
        msg_str += "<font color='mediumblue'><b><u>%s</u></b></font>: " % (msg_obj.who,)
        msg_str += msg_obj.txt
        self.widgets.convtext.append(msg_str)
        #TODO: make special formatting for the message... give the name a different color and perhaps a
        #hyperlink
        
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
    
    def userClick(self, item):
        user = str(item.text())
        self.respawn(self.acct_obj, user)
        
    def respawn(self, acct_obj, user, type=IM, popup=True):
        "to be attached to YobotGui's _openChat()"
        pass
    
class YobotGui(object):
    chats = {} #chats[account,target]->ChatWindow instance
    
    def __init__(self, client):
        "Client should have a ... shit.."
        self.client = client
        print "__init__ done"
    def init_backend(self, backend):
        self.datamodel = AccountModel(backend)
    ######################      PRIVATE HELPERS     ###########################

    def _showConnectionDialog(self):
        if self.mw_widgets.conninput.isVisible():
            return
        self.mw_widgets.w_username.setText("")
        self.mw_widgets.w_password.setText("")
        self.mw_widgets.conninput.show()
    
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
        print improto
        try:
            self.client.connect(user, passw, improto)
        except AttributeError, e:
            print e
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
            print "not processing account ops"
            return
        print obj
        acct = obj.account
        target = obj.name
        self._openChat(acct, target, IM)
        
    def _openChat(self, acct, target, type, popup = False):
        #find an old window...
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
    
    def _sendjoin(self, type):
        dlg = SendJoinDialog(self.datamodel,parent=self.mw,type=type)
        dlg.action = self._openChat if type == IM else self._joinreq
        dlg.show()
    
    def _joinreq(self, acct, room, type=CHAT):
        self._openChat(acct, room, CHAT)
        acct.joinchat(room)
    def _gui_init(self):
        #make the widgets..
        self.mw = QMainWindow()
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
        self.mw_widgets.statusbar.showMessage("Connected: "+ acct_obj.user)
        self.mw_widgets.conninput.hide()
        self.mw_widgets.blist.show()
        self.mw_widgets.blist.setExpanded(self.datamodel.index(acct_obj.index, 0),True)
        
    def gotMessage(self, acct_obj, msg_obj):
        print msg_obj
        type = CHAT if msg_obj.isChat else IM
        self._openChat(acct_obj, msg_obj.name, type)
        self.chats[acct_obj, msg_obj.name].gotMsg(msg_obj)
        
    def chatUserJoined(self, acct_obj, room, user):
        c = self.chats.get([acct_obj,room])
        if not c: return
        c.userJoined(user)

    def chatUserLeft(self, acct_obj, room, user):
        c = self.chats.get([acct_obj, room])
        if not c: return
        c.userLeft(user)
    
    def gotRequest(self, request_obj):
        if request_obj.isYesNo:
            mb = QMessageBox()
            mb.setStandardButtons(QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            mb.setWindowTitle(request_obj.title)
            mb.setText(request_obj.header)
            mb.setInformativeText(request_obj.message)
            mb.setIcon(QMessageBox.Question)
            def _cb(button):
                if mb.buttonRole(button) == mb.YesRole:
                    request_obj.respond(True)
                else:
                    request_obj.respond(False)
            signal_connect(mb, SIGNAL("buttonClicked(QAbstractButton*)"), _cb)
            mb.show()
            
            
            
        
if __name__ == "__main__":
    gui = YobotGui(None)
    gui._testgui()