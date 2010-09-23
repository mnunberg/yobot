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
#import notification
import logbrowser
import logdlg
import time
import buddy_entry
import lxml.html
import status_dialog
from html_fmt import simplify_css, process_input, insert_smileys
import smileys_rc
import gui_util
import yobot_interfaces
#from modeltest import ModelTest

import traceback

from PyQt4 import QtCore, QtGui

#here be dragons:
from PyQt4.QtGui import (QComboBox, QMainWindow, QStandardItemModel, QStandardItem,
                         QIcon, QPixmap, QImage, QPainter, QDialog, QMessageBox,
                         QApplication, QFont, QTextEdit, QColorDialog, QPalette,
                         QListWidget, QListWidgetItem, QStyledItemDelegate,
                         QStyleOptionViewItem, QRegion, QWidget, QBrush, QStyle,
                         QPen, QPushButton, QStyleOption, QMenu, QAction, QCursor,
                         QTreeView, QLineEdit, QButtonGroup)

from PyQt4.QtCore import (QPoint, QSize, QModelIndex, Qt, QObject, SIGNAL, QVariant,
                          QAbstractItemModel, QRect, QRectF, QPointF)

signal_connect = QObject.connect

app = QtGui.QApplication(sys.argv)
from contrib import qt4reactor
qt4reactor.install()


from gui_util import (getIcon, getProtoStatusIcon, mkProtocolComboBox, NotificationBox,
                      STATUS_ICON_MAPS, STATUS_TYPE_MAPS, signal_connect,
                      IMPROTOS_BY_CONSTANT, ConnectionWidget, AccountModel, ROLE_SMALL_BUDDY_TEXT,
                      ROLE_ACCT_OBJ)
CHAT, IM = (1,2)
NOTICE, ERROR, DIALOG = (1,2,3)


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
        signal_connect(self.widgets.bold, SIGNAL("toggled(bool)"),
                       lambda bold: self.widgets.input.setFontWeight(75 if bold else 50))
        
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
            #log_debug("backspace")
            self.widgets.input.textCursor().deletePreviousChar()
            return
        if modifiers & Qt.CTRL:
            #print "control"
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
    yobot_interfaces.implements(yobot_interfaces.IYobotUIPlugin)
    plugin_name = "gui_main"
    def __init__(self):
        #first get some components.. we need the account store at least
        account_manager = yobot_interfaces.component_registry.get_component("account-store")
        if not account_manager:
            raise Exception("couldn't get account store")
        client = yobot_interfaces.component_registry.get_component("client-operations")
        if not client:
            raise Exception("Couldn't find client operations component")
            
        self.client = client
        log_debug( "__init__ done")
        self.datamodel = AccountModel(account_manager)
        self.chats = {} #chats[account,target]->ChatWindow instance
        self.gui_init()
        self.mw.show()
        yobot_interfaces.component_registry.register_component("gui-main", self)
    ######################      PRIVATE HELPERS     ###########################

    def _showConnectionDialog(self):
        if self.conninput.isVisible():
            return
        self.conninput.reset()
        self.conninput.show()
        
    def _disconnectAccount(self, acct, server=False):
        acct.disconnect(server)
    
    def _requestConnection(self, user, passw, improto, **_d_proxy_params):
        try:
            self.client.connect(user, passw, improto, **_d_proxy_params)
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
        self.conninput = ConnectionWidget(connect_cb = self._requestConnection)
        w.mainLayout.addWidget(self.conninput, 0, 0)
        #gui_util.set_bg_opacity(self.conninput, 150)
        self.conninput.show()
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
        
        self.mw_widgets.statusbar.showMessage("Connected: "+ acct_obj.user)
        self.conninput.hide()
        self.mw_widgets.blist.show()
        #fetch offline messages
        acct_obj.fetchBuddies()
        acct_obj.getOfflines()
        
    def gotMessage(self, acct_obj, msg_obj):
        #log_debug(msg_obj)
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
    def roomJoined(self, acct, room):
        acct.fetchRoomUsers(room)
    
    accountConnectionFailed = connectionFailed        
    genericNotice = gotRequest
        
if __name__ == "__main__":
    gui = YobotGui(None)
    gui._testgui()