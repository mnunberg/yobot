#!/usr/bin/env python
if __name__ == "__main__":
    import sys
    sys.path.append("../")
import chatwindow_auto
from PyQt4.QtGui import (QComboBox, QMainWindow,
                         QIcon, QMenu,
                         QApplication, QFont, QTextEdit, QColorDialog, QPalette,
                         QListWidget, QListWidgetItem, QWidget, QBrush,
                         QAction, QCursor,
                         QLineEdit, QColor, QTextCursor,
                         QTextBlockFormat, QLinearGradient,
                         )

from PyQt4.QtCore import (QPoint, QSize, Qt, QObject, SIGNAL,)

from tabwindows import ChatPane, TabContainer

signal_connect = QObject.connect

CHAT, IM = (1,2)

import yobot_interfaces
import yobotproto
from debuglog import log_debug, log_err, log_warn, log_crit, log_info
from html_fmt import simplify_css, process_input, insert_smileys
import smileys_rc
from gui_util import qlw_delitem, qlw_additem, TINY_VERTICAL_SCROLLBAR_STYLE, stylesheet_append
import datetime
import yobotops
import re

strip_html_regexp = re.compile(r"<[^>]*>|<.+/>")

def _gen_striped_gradient(basecolor):
    """Just generate a standard gradient, for use as a background"""
    g = QLinearGradient()
    g.setSpread(g.ReflectSpread)
    g.setStart(0,0)
    g.setFinalStop(2, 2)
    g.setColorAt(0.0, QColor(basecolor))
    g.setColorAt(0.35, QColor(0,0,0,0))
    g.setColorAt(0.75, QColor(0,0,0,0))
    g.setColorAt(1.0, QColor(basecolor))
    return g

class _ChatText(object):
    _styles_initialized = False
    defaultFmt = QTextBlockFormat()
    defaultFmt.setBottomMargin(2.5)
    
    archFmt = QTextBlockFormat()
    archFmt.setBackground(QBrush(QColor("#EEEEEE")))
    
    infoFmt = QTextBlockFormat()
    errFmt = QTextBlockFormat()
    emoteFmt = QTextBlockFormat()
    
    #gradient for emotes...        
    emoteFmt.setBackground(QBrush(_gen_striped_gradient("#f2e4d5")))
    
    #Qt.Dense4Pattern
    errFmt.setBackground(QBrush(_gen_striped_gradient("#ff8e8e"),))
    infoFmt.setBackground(QBrush(_gen_striped_gradient("#33cc00"),))
    
    @staticmethod
    def print_colors():
        p = QApplication.palette()
        for c in ("Window", "Background", "WindowText", "Foreground", "Base", "AlternateBase",
                  "ToolTipBase", "ToolTipText", "Text", "Button", "ButtonText",
                  "BrightText"):
            print c, p.color(getattr(QPalette, c)).name()
    
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
        sb = self.qtb.verticalScrollBar()
        sb.setValue(sb.maximum())

    def append(self, *args, **kwargs):
        "This is monkeypatched during runtime. Appends text to the instance's qtb widget"
    

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
        qlw_additem(str(username), self.users, self.lw, icon=QIcon(":/icons/res/16x16/actions/dialog-cancel.png"))
    def remove(self, username):
        qlw_delitem(str(username), self.users, self.lw)
        
class ChatWindow(ChatPane):
    defaultBacklogCount = 50
    appearance_config = {}
    use_relsize = False
    def __init__(self, client, parent=None, type=IM, acct_obj=None, target=None,
                 factory=None, initial_text="",tabwidget = None):
        """Factory takes a target username and an account object. Supposed to respawn/activate a
        chat window"""
        self.users = {} #dict containing the name of the user mapped to the model object..
        self.type = type
        self.target = target
        self.account = acct_obj
        self.factory = factory
        self._initial_text = initial_text
        if not target or not acct_obj:
            log_err( "must have target and account for chatwindow")
            return

        ChatPane.__init__(self, parent, tabcontainer=tabwidget, title=target)
    
    def setupWidgets(self):
        self.widgets = chatwindow_auto.Ui_w_chatwindow()
        w = self.widgets
        w.setupUi(self)
        
        self.ignore_list = _IgnoreList(w.ignorelist)
        self.setWindowTitle(self.target)
        #and some key press events..
        w.input.keyPressEvent = self._inputKeyPressEvent
        w.input.mouseDoubleClickEvent = self._input_mouseDoubleClickEvent
        w.input.setHtml("")
        
        self._send_html = yobotops.improto_supports_html(self.account.improto)
        
        w.convtext.setHtml(self._initial_text)
        del self._initial_text
        
        self.show_join_leave_messages = False
        if self.type == CHAT:
            w.menuView.addAction(w.actionShow_User_List)
            w.menuView.addAction(w.actionShow_Ignore_List)
            w.menuView.addAction(w.actionShow_Join_Leave)
            w.menuView.addAction(w.actionShow_Topic)
            w.menuActions.addAction(w.actionLeave)
            w.actionShow_User_List.setChecked(True)
            w.actionShow_Ignore_List.setChecked(True)
            w.actionShow_Topic.setChecked(True)
            w.userlist.clear()
            w.ignorelist.clear()
            w.menuView.addAction(w.actionShow_User_List)
            signal_connect(w.actionLeave, SIGNAL("activated()"), self.leaveRoom)
            signal_connect(w.actionShow_Join_Leave, SIGNAL("toggled(bool)"),
                           lambda b: setattr(self, "show_join_leave_messages", b))
            
        elif self.type == IM:
            w.chat_topic.hide()
            w.userlists.hide()
            signal_connect(w.actionShow_Backlog, SIGNAL("activated()"),
                           lambda: self.account.getBacklog(self.target, self.defaultBacklogCount))
            #todo: use a dialog for this, perhaps...
            
        self.current_action_target = ""
        w.userlist.clear()
        
        stylesheet_append(w.userlist, TINY_VERTICAL_SCROLLBAR_STYLE)
        stylesheet_append(w.convtext, TINY_VERTICAL_SCROLLBAR_STYLE)
        stylesheet_append(w.ignorelist, TINY_VERTICAL_SCROLLBAR_STYLE)
        
        w.userlists.resize(w.userlist.height(), 100)
                
        self._init_input()
        self._init_menu()
        self.get_config()
        self.load_appearance_config()
        self.chat_text = _ChatText(self.widgets.convtext)
        
        self.zoom_variations = 0
        def log_zoom(in_fn):
            def fn(*args, **kwargs):
                #log_debug(self.zoom_variations)
                in_fn(*args, **kwargs)
            return fn
        @log_zoom
        def convtext_zoomIn(range=1):
            self.zoom_variations += range
            w.convtext.__class__.zoomIn(w.convtext, range)
        @log_zoom
        def convtext_zoomOut(range=1):
            self.zoom_variations -= range
            w.convtext.__class__.zoomOut(w.convtext, range)
            
        @log_zoom
        def reset_zoom():
            if self.zoom_variations == 0: return
            elif self.zoom_variations > 0: w.convtext.__class__.zoomOut(w.convtext, self.zoom_variations)
            elif self.zoom_variations < 0: w.convtext.__class__.zoomIn(w.convtext, abs(self.zoom_variations))
            self.zoom_variations = 0
        @log_zoom
        def _wheelEvent(event):
            if not event.modifiers() & Qt.CTRL:
                w.convtext.__class__.wheelEvent(w.convtext, event)
                return
            if event.delta() > 0:
                #zoom in
                convtext_zoomIn()
            else:
                convtext_zoomOut()            
        w.convtext.wheelEvent = _wheelEvent
        signal_connect(w.zoom_orig, SIGNAL("clicked()"), reset_zoom)
        signal_connect(w.zoom_in, SIGNAL("clicked()"), convtext_zoomIn)
        signal_connect(w.zoom_out, SIGNAL("clicked()"), convtext_zoomOut)
        
        left, top, right, bottom = self.centralWidget().layout().getContentsMargins()
        self.centralWidget().layout().setContentsMargins(left, 0, right, bottom)
        
################################################################################
############################# INPUT WIDGET METHODS #############################
################################################################################
    def _init_input(self):
        w = self.widgets
        #bold
        signal_connect(w.bold, SIGNAL("toggled(bool)"),
                       lambda bold: w.input.setFontWeight(75 if bold else 50))
        
        #color handling
        
        signal_connect(w.fg_color, SIGNAL("clicked()"), self._choosecolor)
        fgcolor = w.input.textColor()
        self.fgcolor_button_change_color(fgcolor)
        
        #fontsize handling
        current_size = int(w.input.currentFont().pointSize())
        def _setSize(i):
            try:
                w.input.setFontPointSize(float(i))
            except Exception, e:
                log_err(e)
        signal_connect(w.fontsize, SIGNAL("valueChanged(int)"), _setSize)
        
        #for updating the formatting buttons
        signal_connect(w.input, SIGNAL("currentCharFormatChanged(QTextCharFormat)"),
                       self._currentCharFormatChanged)        
        
    def _choosecolor(self, set_color=None):
        w = self.widgets
        def _onClicked(color):
            w.input.setTextColor(color)
            self.fgcolor_button_change_color(color)
        if not set_color:
            cdlg = QColorDialog(self)
            signal_connect(cdlg, SIGNAL("colorSelected(QColor)"), _onClicked)
            ret = cdlg.open()
        else:
            _onClicked(set_color)
    def _currentCharFormatChanged(self,format):
        self.widgets.font.setCurrentFont(format.font())
        self.widgets.fontsize.setValue(int(format.fontPointSize()))
        self.widgets.bold.setChecked(format.fontWeight() >= 75)
        self.widgets.italic.setChecked(format.fontItalic())
        self.widgets.underline.setChecked(format.fontUnderline())
        self.fgcolor_button_change_color(format.foreground().color())
    def _inputKeyPressEvent(self, event):
        w = self.widgets
        key = event.key()
        modifiers = event.modifiers()
        if key == Qt.Key_Return and not modifiers:
            self.sendMsg()
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

    
    @classmethod
    def get_config(self):
        "set appearance configuration object. no need to set it each time"
        if not self.appearance_config:
            c = yobot_interfaces.component_registry.get_component("client-config")
            if c:
                self.appearance_config = c.globals.get("appearance", {"nothing":None})
            else:
                self.appearance_config = {}
        return self.appearance_config

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
            if c.get("show_joinpart", False): w.actionShow_Join_Leave.setChecked(True)
            
            self.use_relsize = c.get("use_html_relsize", False)
    
    def fgcolor_button_change_color(self, color):
        stylesheet="""
        QAbstractButton, :flat {
            margin:2px;
            background-color:%s;
            border:none;
            border-radius:3px
            }
        :hover {
            border-width:1.5px;
            border-color:black;
            border-style:solid;
            }
        """
        self.widgets.fg_color.setStyleSheet(stylesheet % (color.name(),))

###############################################################################
######################### CONVERSATION DISPLAY METHODS ########################
###############################################################################
    def _init_menu(self):
        "Initializes context menu for usernames"
        if not self.type == CHAT: return
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
        
###########################################################################
############################# SEND/RECEIVE/EVENT METHODS###################
###########################################################################
    def sendMsg(self):
        w = self.widgets
        if not w.input.toPlainText():
            log_debug("empty input")
            return
        if self._send_html:
            txt = unicode(w.input.toHtml().toUtf8(), "utf-8")
            txt = simplify_css(txt.encode("utf-8"))
        else:
            txt = unicode(w.input.toPlainText().toUtf8(), "utf-8")
            if not txt: return
        log_warn(txt)
        
        w.input.clear()
        
        chat = True if self.type == CHAT else False
        self.account.sendmsg(self.target, str(txt), chat=chat)
        
    def gotMsg(self, msg_obj):
        #get time..
        w = self.widgets
        if msg_obj.who in self.ignore_list:
            log_debug("ignoring message from", msg_obj.who)
            return
        fmt = _ChatText.defaultFmt
        colon_ish = ":"
        #determine format...
        if (msg_obj.yprotoflags & yobotproto.YOBOT_BACKLOG or
            msg_obj.prplmsgflags & yobotproto.PURPLE_MESSAGE_DELAYED):
            fmt = _ChatText.archFmt
        elif msg_obj.yprotoflags & yobotproto.PURPLE_MESSAGE_SYSTEM:
            fmt = _ChatText.errFmt
        elif strip_html_regexp.sub("", msg_obj.txt).startswith("/me "):
            fmt = _ChatText.emoteFmt
            colon_ish = "**"
        
        who = msg_obj.who
        if not who and msg_obj.prplmsgflags & yobotproto.PURPLE_MESSAGE_SYSTEM:
            who = "SYSTEM MESSAGE"
        whocolor = "darkblue" if msg_obj.prplmsgflags & yobotproto.PURPLE_MESSAGE_SEND else "darkred"
        whostyle = "color:%s;font-weight:bold;text-decoration:none;" % (whocolor,)
        msg_str = (("""<a href='YOBOT_INTERNAL/%s' style='%s'>""" % (who, whostyle)) +
                   ("(%s) " % (msg_obj.timeFmt,) if w.actionTimestamps.isChecked() else "") +
                   ("%s</a>%s " % (msg_obj.who,colon_ish)))
        
        formatted = process_input(msg_obj.txt, self.use_relsize)
        formatted = insert_smileys(formatted, self.account.improto, ":smileys/smileys", 24, 24)
        log_debug(formatted)
        msg_str += formatted
        msg_str = unicode(msg_str, "utf-8")
        
        self.chat_text.append(msg_str, fmt)
    
    def userJoined(self, user):
        qlw_additem(user, self.users, self.widgets.userlist)
        if self.show_join_leave_messages:
            self.chat_text.append("<b>%s</b> Has Joined %s" % (user, self.target), _ChatText.infoFmt)
    def userLeft(self, user):
        qlw_delitem(user, self.users, self.widgets.userlist)
        if self.show_join_leave_messages:
            self.chat_text.append("<b>%s</b> Has Left %s" % (user, self.target), _ChatText.infoFmt)
    def topicChanged(self, topic):
        #do something...
        self.widgets.chat_topic.setText(topic)
        self.chat_text.append("Topic changed to: <i>%s</i>" % (topic), _ChatText.infoFmt)
    def leaveRoom(self):
        self.account.leaveRoom(self.target)
    def roomLeft(self):
        self.chat_text.append("Left %s at %s" % (self.target, datetime.datetime.now()),
                              _ChatText.errFmt)
        
if __name__ == "__main__":
    import sys
    import random
    from yobotclass import YobotAccount
    from string import ascii_letters
    def fillwindow(chatwindow):
        chatwindow.show_join_leave_messages = True
        chatwindow.chat_text.append("emoting something " * 3, _ChatText.emoteFmt)
        
        for i in xrange(40):
            chatwindow.userJoined("".join(random.sample(ascii_letters, 10)))
            chatwindow.users
            chatwindow.ignore_list.add("".join(random.sample(ascii_letters, 10)))
        
        chatwindow.topicChanged("ALL YOUR BASE ARE BELONG TO US! ")
        
        def spamtext(text="Some Text", iterations=100, format=_ChatText.defaultFmt):
            for i in xrange(iterations):
                chatwindow.chat_text.append(text, format)
        
        chatwindow.chat_text.append("emoting something " * 3, _ChatText.emoteFmt)
        spamtext("Archive Text", format=_ChatText.archFmt)
        spamtext("Error Text", format=_ChatText.errFmt)
        spamtext("Info Text", format=_ChatText.infoFmt)
        #chatwindow.chat_text.append("somereallylongtext"*50, _ChatText.infoFmt)
        chatwindow.chat_text.append("emoting something " * 3, _ChatText.emoteFmt)
        
        textopts = ([("This is normal Text ", _ChatText.defaultFmt)] * 5) + [
            ("This is error text ", _ChatText.errFmt),
            ("This is archive text ", _ChatText.archFmt),
            ("This is informative text", _ChatText.infoFmt),
            ("This is emoted text ", _ChatText.emoteFmt)
        ]
        
        for i in xrange(500):
            t = random.choice(textopts)
            chatwindow.chat_text.append(t[0] * 3, t[1])
    
    app = QApplication(sys.argv)
    first = ChatWindow(None, target="first", acct_obj=YobotAccount(), type=CHAT)
    second = ChatWindow(None, target="second", acct_obj=YobotAccount(), type=CHAT)
    third = ChatWindow(None, target="third", acct_obj=YobotAccount(), type=IM)
    #fillwindow(first)
    #fillwindow(second)
    
    app.exec_()