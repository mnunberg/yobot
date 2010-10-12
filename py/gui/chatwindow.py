#!/usr/bin/env python
import chatwindow_auto
from PyQt4.QtGui import (QComboBox, QMainWindow, QStandardItemModel, QStandardItem,
                         QIcon, QPixmap, QImage, QPainter, QDialog, QMessageBox,
                         QApplication, QFont, QTextEdit, QColorDialog, QPalette,
                         QListWidget, QListWidgetItem, QStyledItemDelegate,
                         QStyleOptionViewItem, QRegion, QWidget, QBrush, QStyle,
                         QPen, QPushButton, QStyleOption, QMenu, QAction, QCursor,
                         QTreeView, QLineEdit, QButtonGroup, QColor, QTextCursor,
                         QTextBlockFormat)

from PyQt4.QtCore import (QPoint, QSize, QModelIndex, Qt, QObject, SIGNAL, QVariant,
                          QAbstractItemModel, QRect, QRectF, QPointF, QStringList)

signal_connect = QObject.connect

CHAT, IM = (1,2)

import yobot_interfaces
import yobotproto
from debuglog import log_debug, log_err, log_warn, log_crit, log_info
from html_fmt import simplify_css, process_input, insert_smileys
import smileys_rc


class _ChatText(object):
    defaultFmt = QTextBlockFormat()
    archFmt = QTextBlockFormat()
    archFmt.setBackground(QBrush(QColor("#c0c0c0")))
    def __init__(self, qtb):
        self.qtb = qtb
        self.append = self._initAppend
    def _initAppend(self, txt, fmt=defaultFmt):
        self.qtb.textCursor().mergeBlockFormat(fmt)
        self.qtb.append(txt)
        self.append = self._normalAppend
    def _normalAppend(self, txt, fmt=defaultFmt):
        c = self.qtb.textCursor()
        c.movePosition(c.End)
        c.insertBlock(fmt)
        c.insertHtml(txt)
    
        
class _IgnoreList(object):
    def __init__(self, listwidget):
        self.lw = listwidget
        signal_connect(self.lw, SIGNAL("itemDoubleClicked(QListWidgetItem*)"), self._itemDoubleClicked)
        self.users = {}
    def __contains__(self, obj):
        return obj in self.users
    def _itemDoubleClicked(self, lwitem):
        #remove user from ignore list:
        if not lwitem:
            return
        username = str(lwitem.text())
        self.remove(username)
        
    def add(self, username):
        username = str(username)
        if username in self.users:
            return
        lwitem = QListWidgetItem(QIcon(":/icons/res/16x16/actions/dialog-cancel.png"), username)
        self.lw.addItem(lwitem)
        self.users[username] = lwitem
    def remove(self, username):
        username = str(username)
        if not username in self.users:
            return
        #remove the row assigned to this widget
        row = self.lw.row(self.users.pop(username))
        if row < 0:
            log_err("row is < 0")
            return
        self.lw.takeItem(row)
        log_debug("removed.. i think")

class ChatWindow(QMainWindow):
    """This class is quite dumb, but it does contain client hooks to get and send
    messages"""
    appearance_config = {}
    use_relsize = False
    @classmethod
    def get_config(self):
        "set appearance configuration object. no need to set it each time"
        if not self.appearance_config:
            c = yobot_interfaces.component_registry.get_component("client-config")
            self.appearance_config = c.globals.get("appearance", {"nothing":None})
        return self.appearance_config
    
    defaultBacklogCount = 50
    def __init__(self, client, parent=None, type=IM, acct_obj=None, target=None,
                 factory=None, initial_text="",):
        """Factory takes a target username and an account object. Supposed to respawn/activate a
        chat window"""
        self.users = {} #dict containing the name of the user mapped to the model object..
        
        if not target or not acct_obj:
            log_err( "must have target and account for chatwindow")
            return
        QMainWindow.__init__(self, parent)
        self.type = type
        self.target = target
        self.account = acct_obj
        
        self.widgets = chatwindow_auto.Ui_w_chatwindow()
        w = self.widgets
        
        w.setupUi(self)
        
        self.ignore_list = _IgnoreList(w.ignorelist)
        self.setWindowTitle(target)
        #and some key press events..
        w.input.keyPressEvent = self._inputKeyPressEvent
        w.input.mouseDoubleClickEvent = self._input_mouseDoubleClickEvent
        w.input.setHtml("")
        w.convtext.setHtml(initial_text)
        if type == CHAT:
            w.menuView.addAction(w.actionShow_User_List)
            w.menuView.addAction(w.actionShow_Ignore_List)
            w.menuActions.addAction(w.actionLeave)
            w.actionShow_User_List.setChecked(True)
            w.actionShow_Ignore_List.setChecked(True)
            w.userlist.clear()
            w.ignorelist.clear()
            w.menuView.addAction(w.actionShow_User_List)
            signal_connect(w.actionLeave, SIGNAL("activated()"), self.leaveRoom)
            
        elif type == IM:
            w.userlists.hide()
            signal_connect(w.actionShow_Backlog, SIGNAL("activated()"),
                           lambda: self.account.getBacklog(self.target, self.defaultBacklogCount))
            #todo: use a dialog for this, perhaps...
            
        self.current_action_target = ""
        w.userlist.clear()
        self.factory = factory
        self._init_input()
        self._init_menu()
        self.get_config()
        self.load_appearance_config()
        self.chat_text = _ChatText(self.widgets.convtext)
        
    def _init_input(self):
        #bold
        signal_connect(self.widgets.bold, SIGNAL("toggled(bool)"),
                       lambda bold: self.widgets.input.setFontWeight(75 if bold else 50))
        
        #color handling
        
        signal_connect(self.widgets.fg_color, SIGNAL("clicked()"), self._choosecolor)
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
    def _choosecolor(self, set_color=None):
        def _onClicked(color):
            self.widgets.input.setTextColor(color)
            self.widgets.fg_color.setStyleSheet("background-color: '%s'" % (color.name()))
        if not set_color:
            cdlg = QColorDialog(self)
            signal_connect(cdlg, SIGNAL("colorSelected(QColor)"), _onClicked)
            ret = cdlg.open()
        else:
            _onClicked(set_color)

    def load_appearance_config(self):
        w = self.widgets
        if self.appearance_config:
            #navigate around.. this could be tricky
            c = self.appearance_config
            if c.get("font_family", None):
                f = QFont()
                f.setFamily(c["font_family"])
                w.font.setCurrentFont(f)
            if c.get("font_size", None):
                log_warn("setting font size to ", c["font_size"])
                w.fontsize.setValue(c["font_size"])
                w.input.setFontPointSize(c["font_size"])
            if c.get("font_color", None): self._choosecolor(set_color=QColor(c["font_color"]))
            if c.get("font_bold", False): w.bold.setChecked(True)
            if c.get("font_italic", False): w.italic.setChecked(True)
            if c.get("font_underline", False): w.underline.setChecked(True)
            self.use_relsize = c.get("use_html_relsize", False)
            
            
    def _init_menu(self):
        "Initializes context menu for usernames"
        if not self.type == CHAT:
            return
        
        menu = QMenu()
        self._action_newmsg = menu.addAction(QIcon(":/icons/icons/message-new.png"), "Send IM")
        self._action_ignore_tmp = menu.addAction(QIcon(":/icons/res/16x16/actions/dialog-cancel.png"), "Ignore (from chat)")
        self._action_ignore_perm = menu.addAction(QIcon(":/icons/res/16x16/actions/dialog-cancel.png"), "Ignore (server)")
        
        if self.factory:
            def respawn(username):
                username = str(username)
                if self.account.improto == yobotproto.YOBOT_JABBER:
                    username = "/".join([self.target, username])
                self.factory(username, self.account)
                
            signal_connect(self._action_newmsg, SIGNAL("activated()"),
                    lambda: respawn(self.current_action_target))
            signal_connect(self.widgets.userlist, SIGNAL("itemDoubleClicked(QListWidgetItem*)"),
                lambda item: respawn(item.text()))
            
        signal_connect(self._action_ignore_tmp, SIGNAL("activated()"), lambda: self.ignore_list.add(self.current_action_target))
        self.userActionMenu = menu
        
        def _anchorClicked(link):
            link = str(link.toString())
            if link.startswith("YOBOT_INTERNAL"):
                user = link.split("/", 1)[1]
                self.current_action_target = user
                self.userActionMenu.exec_(QCursor().pos())
        signal_connect(self.widgets.convtext, SIGNAL("anchorClicked(QUrl)"), _anchorClicked)
        
        def _userlistContextMenu(point):
            item = self.widgets.userlist.itemAt(point)
            if not item:
                return
            self.current_action_target = item.text()
            self.userActionMenu.exec_(QCursor().pos())
            
        self.widgets.userlist.setContextMenuPolicy(Qt.CustomContextMenu)
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
        w = self.widgets
        key = event.key()
        modifiers = event.modifiers()
        if key== Qt.Key_Return:
            if not w.input.toPlainText():
                log_debug("empty input")
                return
            txt = unicode(w.input.toHtml().toUtf8(), "utf-8")
            if not txt:
                return
            
            log_warn(txt.encode("utf-8"))
            txt = simplify_css(txt.encode("utf-8"))
            log_warn(txt)
            self.sendMsg(txt)
            w.input.clear()
            return
        if key == Qt.Key_Backspace:
            cursor = w.input.textCursor()
            if cursor.selectionStart() <=1:
                #Don't erase formatting.. normally erasing the last character
                #will also reset the format. This stores the current formatting,
                #so that we can reset it after the character has been removed
                #according to Qt documentation, selectionStart "Returns the end of
                #the selection or position() if the cursor doesn't have a selection."
                font = w.input.currentFont()
                color = w.input.textColor()
                cursor.deletePreviousChar()
                w.input.setCurrentFont(font)
                w.input.setTextColor(color)
                return
            cursor.deletePreviousChar()            
            return
        if modifiers & Qt.CTRL:
            #MS-Word style size increase/decrease
            if key == Qt.Key_BracketLeft:
                w.fontsize.stepBy(-1)
                return
            elif key == Qt.Key_BracketRight:
                w.fontsize.stepBy(1)
                return
        
        QTextEdit.keyPressEvent(w.input,event)    
    
    def _input_mouseDoubleClickEvent(self, event):
        cursor = self.widgets.input.textCursor()
        if cursor.position() == 0:
            log_debug("doing nothing")
        else:
            QTextEdit.mouseDoubleClickEvent(self.widgets.input, event)
    
    def sendMsg(self, txt):
        chat = True if self.type == CHAT else False
        self.account.sendmsg(self.target, str(txt), chat=chat)
        
    def gotMsg(self, msg_obj):
        #get time..
        w = self.widgets
        if msg_obj.who in self.ignore_list:
            return
        
        whocolor = "darkblue" if msg_obj.prplmsgflags & yobotproto.PURPLE_MESSAGE_SEND else "darkred"
        whostyle = "color:%s;font-weight:bold;text-decoration:none;" % (whocolor,)
        
        
        msg_str = ""
        msg_str += """<a href='YOBOT_INTERNAL/%s' style='%s'>""" % (msg_obj.who, whostyle)
        msg_str += "(%s) " % (msg_obj.timeFmt,) if w.actionTimestamps.isChecked() else ""
        msg_str += "%s</a>: " % (msg_obj.who,)
        formatted = process_input(msg_obj.txt, self.use_relsize)
        formatted = insert_smileys(formatted, self.account.improto, ":smileys/smileys", 24, 24)
        log_debug(formatted)
        msg_str += formatted
        msg_str = unicode(msg_str, "utf-8")
        if (msg_obj.yprotoflags & yobotproto.YOBOT_BACKLOG or
            msg_obj.prplmsgflags & yobotproto.PURPLE_MESSAGE_DELAYED):
            self.chat_text.append(msg_str, fmt=self.chat_text.archFmt)
        else:
            self.chat_text.append(msg_str)
        sb = w.convtext.verticalScrollBar()
        sb.setValue(sb.maximum())
    
    def userJoined(self, user):
        if self.users.get(user): return
        u = QListWidgetItem()
        u.setText(user)
        self.widgets.userlist.addItem(u)
        self.users[user] = u
    def userLeft(self, user):
        log_err("hi")
        u = self.users.get(user)
        if not u: return
        #as always, we need to get the row of the item widget first...
        row = self.widgets.userlist.row(u)
        if row >= 0:
            self.widgets.userlist.takeItem(row)
        self.users.pop(u,"")
        
    def leaveRoom(self):
        self.account.leaveRoom(self.target)
    def roomLeft(self, msg=None):
        log_err("implement me!")
        pass
