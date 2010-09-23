#!/usr/bin/env python
import sys
sys.path.append("../")
import yobot_interfaces
import yobotproto
from client_support import YCAccount, SimpleNotice
from gui import gui_util
from gui.gui_util import signal_connect, ConnectionWidget
import PyQt4
from PyQt4.QtGui import (QComboBox, QMainWindow, QStandardItemModel, QStandardItem,
                         QIcon, QPixmap, QImage, QPainter, QDialog, QMessageBox,
                         QApplication, QFont, QTextEdit, QColorDialog, QPalette,
                         QListWidget, QListWidgetItem, QStyledItemDelegate,
                         QStyleOptionViewItem, QRegion, QWidget, QBrush, QStyle,
                         QPen, QPushButton, QStyleOption, QMenu, QAction, QCursor,
                         QTreeView, QLineEdit, QButtonGroup, QFileDialog, QErrorMessage,
                         QFontDialog, QColor, QDockWidget, QSizePolicy,
                         qDrawBorderPixmap, qDrawShadeLine, qDrawShadePanel, QStackedWidget,
                         QGridLayout, QLayout, QFrame,
                         QGraphicsDropShadowEffect, QSpacerItem)


from PyQt4.QtCore import (QPoint, QSize, QModelIndex, Qt, QObject, SIGNAL, QVariant,
                          QAbstractItemModel, QRect, QRectF, QPointF, QT_VERSION)


from debuglog import log_debug, log_info, log_err, log_crit, log_warn
import sqlite3.dbapi2 as sqlite3
import pickle
import lxml.html
import re
from time import time
from collections import defaultdict
import random
from gui.html_fmt import point_to_html
import os.path
import yobotops
from cgi import escape as html_escape

import datetime


import gui_new
#trivia types
TYPE_ANAGRAMS, TYPE_TRIVIA, TYPE_BOTH = range(1, 4)

TRIVIA_ROOT = "/home/mordy/src/purple/py/triviabot"

article_start_re = re.compile("^(the|a) ")

def get_categories_list(dbname):
    dbconn = sqlite3.connect(dbname)
    ret = []
    for r in dbconn.cursor().execute("select distinct category from questions"):
        ret.append(r[0])
    return ret


def scramble_word(word):
    return "".join(random.sample(word, len(word)))

class TriviaGui(gui_new.TGui):
    def __init__(self, parent=None):
        gui_new.TGui.__init__(self, parent)
        self.widgets = self
        w = self.widgets
        self.model = yobot_interfaces.component_registry.get_component("account-model")
        self.client_ops = yobot_interfaces.component_registry.get_component("client-operations")
        assert self.client_ops
        
        def _handle_connect(username, password, improto, **proxy_params):
            self.client_ops.connect(username, password, improto, **proxy_params)
        
        def offset_pos_fn():
            return QPoint(0, self.menubar.height())
        self.connwidget = gui_util.OverlayConnectionWidget(offset_pos_fn, _handle_connect, self)
        signal_connect(w.actionConnect, SIGNAL("toggled(bool)"), self.connwidget.setVisible)
        signal_connect(self.connwidget.widgets.conn_close, SIGNAL("clicked()"),
                       lambda: w.actionConnect.setChecked(False))
        if not self.model:
            w.actionConnect.setChecked(True)
            self.model = gui_util.AccountModel(None)
            self.menubar.show()
        else:
            self.connwidget.hide()

        
        #notification widgets:
        qdw = QFrame(self)
        self.notification_shadow = QGraphicsDropShadowEffect(qdw)
        self.notification_shadow.setBlurRadius(10.0)
        qdw.setFrameShadow(qdw.Raised)
        qdw.setGraphicsEffect(self.notification_shadow)
        qdw.setFrameShape(qdw.StyledPanel)
        qdw.setAutoFillBackground(True)
        gui_util.set_bg_opacity(qdw, 240)
        qsw = QStackedWidget(qdw)
        qdw.setLayout(QGridLayout())
        qdw.layout().setSizeConstraint(QLayout.SetMinimumSize)
        qdw.layout().addWidget(qsw)

        self._notification_dlg = qdw
        self.qdw = qdw
        self.qsw = qsw
        self.notifications = gui_util.NotificationBox(qdw, qsw, noTitleBar=False)
        #self.qdw.show()
        
        #resize/show events
        def _force_bottom(event, superclass_fn):
            log_err("")
            superclass_fn(self.qdw, event)
            self.qdw.move(0, self.height()-self.qdw.height())
        self.qdw.resizeEvent = lambda e: _force_bottom(e, QWidget.resizeEvent)
        self.qdw.showEvent = lambda e: _force_bottom(e, QWidget.showEvent)
        
        #set up account menu
        w.account.setModel(self.model)
        
        for a in ("start", "stop", "pause", "next"):
            gui_util.signal_connect(getattr(w, a), SIGNAL("clicked()"),
                                    lambda cls=self, a=a: getattr(cls, a + "_requested")())
            getattr(w, a).setEnabled(False)
        w.start.setEnabled(True)
                
        self.anagrams_prefix_blacklist = set()
        self.anagrams_suffix_blacklist = set()
        
        #listWidgetItems
        def _add_nfix(typestr):
            txt = getattr(w, typestr + "_input").text()
            if not txt:
                return
            txt = str(txt)
            st = getattr(self, "anagrams_" + typestr + "_blacklist")
            target = getattr(w, typestr + "_list")
            if not txt in st:
                target.addItem(txt)
                st.add(txt)
            getattr(w, typestr + "_input").clear()
        def _remove_nfix(typestr):
            target = getattr(w, typestr + "_list")
            st = getattr(self, "anagrams_" + typestr + "_blacklist")
            item = target.currentItem()
            if item:
                txt = str(item.text())
                assert txt in st
                target.takeItem(target.row(item))
                st.remove(txt)
            else:
                log_warn("item is None")
        for nfix in ("suffix", "prefix"):
            signal_connect(getattr(w, nfix + "_add"), SIGNAL("clicked()"),
                lambda typestr=nfix: _add_nfix(typestr))
            signal_connect(getattr(w, nfix + "_del"), SIGNAL("clicked()"),
                lambda typestr=nfix: _remove_nfix(typestr))
            
        #hide the extended options
        w.questions_categories_params.hide()
        w.suffix_prefix_options.hide()
        
        self.resize(self.minimumSizeHint())
    
        #connect signals for enabling the start button
        signal_connect(w.account, SIGNAL("currentIndexChanged(int)"), self._enable_start)
        signal_connect(w.room, SIGNAL("activated(int)"), self._enable_start)
        signal_connect(w.room, SIGNAL("editTextchanged(QString)"), self._enable_start)
        signal_connect(w.questions_database, SIGNAL("textChanged(QString)"), self.questions_dbfile_changed)
        signal_connect(w.questions_database, SIGNAL("textChanged(QString)"), self._validate_questions_db)
        signal_connect(w.anagrams_database, SIGNAL("textChanged(QString)"), self._validate_anagrams_db)
        
        signal_connect(w.questions_database, SIGNAL("textChanged(QString)"), self._enable_start)
        signal_connect(w.anagrams_database, SIGNAL("textChanged(QString)"), self._enable_start)
        
        #category list for questions:
        self.selected_questions_categories = set()
        def _unselect(lwitem):
            row = w.selected_categories.row(lwitem)
            self.selected_questions_categories.remove(str(lwitem.text()))
            self.widgets.selected_categories.takeItem(row)
        def _select(lwitem):
            category = str(lwitem.text())
            if not category in self.selected_questions_categories:
                log_debug("Adding", category)
                self.selected_questions_categories.add(category)
                w.selected_categories.addItem(category)
        signal_connect(w.questions_categories, SIGNAL("itemDoubleClicked(QListWidgetItem*)"), _select)
        signal_connect(w.selected_categories, SIGNAL("itemDoubleClicked(QListWidgetItem*)"), _unselect)
        
        #formatting and color
        self.fmtstr = "%s"
        self.font = None
        self.color = None
        self.font_menu = QMenu()
        self.action_change_font_style = self.font_menu.addAction(QIcon(":/icons/icons/format-text-bold.png"),"Style and Face")
        self.action_change_font_color = self.font_menu.addAction(QIcon(":/icons/icons/format-fill-color.png"),"Color")
        self.action_change_font_reset = self.font_menu.addAction(QIcon(":/icons/icons/dialog-close.png"), "Reset Formatting")
        def _reset_formatting():
            self.font = None
            self.color = None
            self._gen_font_stylesheet()
            self._update_fmtstr()
        signal_connect(self.action_change_font_color, SIGNAL("activated()"),
                       lambda: self.change_formatting(color=True))
        signal_connect(self.action_change_font_style, SIGNAL("activated()"),
                       lambda: self.change_formatting(style=True))
        signal_connect(self.action_change_font_reset, SIGNAL("activated()"), _reset_formatting)
        signal_connect(w.change_font, SIGNAL("clicked()"),
                       lambda: self.font_menu.exec_(QCursor().pos()))
        
        self.anagrams_db_is_valid = False
        self.questions_db_is_valid = False
        
        #profile stuff..
        signal_connect(w.actionLoad, SIGNAL("activated()"), lambda: self.profile_handler(load=True))
        signal_connect(w.actionSave, SIGNAL("activated()"), lambda: self.profile_handler(save=True))
        signal_connect(w.actionSave_As, SIGNAL("activated()"), lambda: self.profile_handler(save_as=True))
        self.current_profile_name = ""
                
        w.suffix_prefix_options.sizeHint = lambda: QSize(1,1)
        w.questions_categories_params.sizeHint = lambda: QSize(1,1)
                
        self.show()
        

    
    def change_formatting(self, style=False, color=False):
        if color:
            self.color = QColorDialog.getColor(self.color if self.color else QColor())
        elif style:
            self.font = QFontDialog.getFont(self.font if self.font else QFont())[0]
        self._gen_font_stylesheet()
        self._update_fmtstr()
    
    def _update_fmtstr(self):
        if not self.font and not self.color:
            return
        fmt_begin = fmt_end = ""
        _font = "<font "
        if self.font:
            if self.font.bold():
                fmt_begin += "<b>"
                fmt_end += "</b>"
            if self.font.italic():
                fmt_begin += "<i>"
                fmt_end += "</i>"
            if self.font.underline():
                fmt_begin += "<u>"
                fmt_end += "</u>"
            _font += "face='%s' size='%d' absz='%d' " % (self.font.family(),
                point_to_html(self.font.pointSize()),self.font.pointSize())
        
        if self.color:
            _font += "color='%s' " % (self.color.name())
        _font += ">"
        fmt_begin += _font
        fmt_end += "</font>"
        self.fmtstr = fmt_begin + "%s" + fmt_end
    
    
    def _validate_anagrams_db(self, db):
        dbconn = None
        db = str(db)
        try:
            assert os.path.exists(db)
            dbconn = sqlite3.connect(db)
            cursor = dbconn.cursor()
            cursor.execute("select word from words limit 1").fetchone()[0]
            self.anagrams_db_is_valid = True
        except Exception, e:
            log_err(e)
            self.anagrams_db_is_valid = False
            QErrorMessage(self).showMessage("Anagrams database is invalid: " + str(e))
        finally:
            if dbconn:
                dbconn.close()
    def _validate_questions_db(self, db):
        dbconn = None
        db = str(db)
        try:
            assert os.path.exists(db)
            dbconn = sqlite3.connect(db)
            cursor = dbconn.cursor()
            cursor.execute("select id, frequency, question, answer, alt_answers from questions limit 1").fetchone()[0]
            self.questions_db_is_valid = True
        except Exception, e:
            log_err(e)
            self.questions_db_is_valid = False
            QErrorMessage(self).showMessage("Questions database is invalid: " + str(e))
        finally:
            if dbconn:
                dbconn.close()
    
    def _gen_font_stylesheet(self):
        stylesheet = ""
        if self.font:
            if self.font.bold():
                stylesheet += "font-weight: bold;"
            if self.font.italic():
                stylesheet += "font-style: italic;"
            if self.font.underline():
                stylesheet += "text-decoration: underline;"
            stylesheet += "font-size: %dpt;" % (self.font.pointSize())
            stylesheet += "font-family: %s;" % (self.font.family())
        if self.color:
            stylesheet += "color: %s;" % (self.color.name(),)
        
        self.widgets.change_font.setStyleSheet(stylesheet)
    
    
    def _dbs_are_valid(self):
        type = str(self.widgets.questions_type.currentText()).lower()
        if type == "mix" and not ( self.anagrams_db_is_valid and self.questions_db_is_valid):
            return False
        elif type == "anagrams" and not self.anagrams_db_is_valid:
            return False
        elif type == "trivia" and not self.questions_db_is_valid:
            return False        
        return True
        
    def _enable_start(self, *args):
        w = self.widgets
        if w.account.currentText() and w.room.currentText() and self._dbs_are_valid():
            w.start.setEnabled(True)
        else:
            w.start.setEnabled(False)        
            
    #some hooks
    def questions_dbfile_changed(self, dbname):
        self.widgets.questions_categories.clear()
        try:
            l = get_categories_list(str(dbname))
        except Exception, e:
            log_err(e)
            return
        for s in l:
            if s:
                self.widgets.questions_categories.addItem(str(s))
    @staticmethod
    def create_profile_mappings():
        #make a tuple.
        #format: (cast_fn, get_fn, set_fn)
        d = {}
        
        #integers
        for a in ("post_interval", "answer_timeout", "percent_anagrams", "percent_trivia",
                  "amount", "anagrams_letters_min", "anagrams_letters_max"):
            d[a] = ("int", "value", "setValue")
        
        #strings
        for a in ("anagrams_database", "questions_database"):
            d[a] = ("str", "text", "setText")
        
        #booleans
        for a in ("updatedb_bool", "anagrams_caps_hint", "questions_blacklist",
                  "questions_use_categories", "anagrams_use_nfixes"):
            d[a] = ("bool", "isChecked", "setChecked")
        
        #room combobox
        d["room"] = ("str", "currentText", "addItem")
        
        return d
        #for accounts, we need to do some special handling because they are
        #referenced by index
    
    def save_profile(self, profile_name):
        try:
            f = open(profile_name, "w")
            f.write("#Yobot Trivia Profile Settings automatically generated on %s\n" %
                    str(datetime.datetime.now()))
            f.write("#Configuration is case-sensitive. Use 'True' and 'False' for boolean values\n")
            f.write("#this file is parsed directly using python's eval\n")
            
            d = TriviaGui.create_profile_mappings()
            for k, v in d.items():
                #k is the attribute
                field = getattr(self.widgets, k)
                cast, getter, setter = v
                value = getattr(field, getter)() if getter else field
                
                if cast == "str":
                    value = str(value)
                #if not value and cast == "bool":
                #    value = int(value)
                if not value and cast == "str":
                    value = ""
                    
                f.write(k + "=" + repr(value) + "\n")
            
            #for account..
            acct_index = self.widgets.account.currentIndex()
            acct_index = self.model.index(acct_index)
            account = acct_index.internalPointer()
            if account:
                f.write("account_username=" + account.user + "\n")
                f.write("account_improto=" + yobotops.imprototostr(account.improto) + "\n")
            
            #for complex types
            for c in ("anagrams_suffix_blacklist", "anagrams_prefix_blacklist",
                      "selected_questions_categories"):
                log_info(getattr(self, c))
                f.write(c + "=" + repr(getattr(self, c)) + "\n")
            
            #for font and color:
            if self.font:
                f.write("font=" + self.font.toString() + "\n")
            if self.color:
                f.write("color=" + self.color.name() + "\n")
            #for type, just write the current type
            f.write("questions_type=" + self.widgets.questions_type.currentText() + "\n")
            #for the blacklists/whitelists..
            
            f.close()
            return True
        except Exception, e:
            QErrorMessage(self).showMessage(str(e))
            return False

    def load_profile(self, profile_name):
        d = TriviaGui.create_profile_mappings()
        try:
            f = open(profile_name, "r")
            for l in f.readlines():
                if l.strip()[0] in ("#", ";"):
                    continue
                k, v = [s.strip() for s in l.split("=")]
                dkey = d.get(k, None)
                if not dkey:
                    #complex handling
                    if k in ("anagrams_prefix_blacklist", "anagrams_suffix_blacklist"):
                        tmp = k.split("_")[1]
                        getattr(self, k).clear()
                        getattr(self, k).update([str(s) for s in eval(v)])
                        getattr(self.widgets, tmp + "_list").clear()
                        getattr(self.widgets, tmp + "_list").addItems(list(getattr(self, k)))
                    elif k == "selected_questions_categories":
                        getattr(self, k).clear()
                        getattr(self, k).update(eval(v))
                        getattr(self.widgets, "selected_categories").clear()
                        getattr(self.widgets, "selected_categories").addItems(list(getattr(self, k)))
                    elif k == "font":
                        self.font = QFont()
                        self.font.fromString(v)
                        self._gen_font_stylesheet()
                        self._update_fmtstr()
                    elif k == "color":
                        self.color = QColor(v)
                        self._gen_font_stylesheet()
                        self._update_fmtstr()
                    else:
                        log_warn("unknown key", k)
                    continue
                cast, getter, setter = dkey
                field = getattr(self.widgets, k)
                #getattr(field, setter)(eval(cast)(v))
                getattr(field, setter)(eval(v))
            f.close()
            return True
        except Exception, e:
            QErrorMessage(self).showMessage(str(e))
            return False
        
    def profile_handler(self, load=False, save=False, save_as=False):
        if load:
            profile = QFileDialog.getOpenFileName(self, "Select Profile", TRIVIA_ROOT)
            if profile and self.load_profile(profile):
                self.current_profile_name = profile
        elif save:
            if self.current_profile_name:
                self.save_profile(self.current_profile_name)
        elif save_as:
            profile = QFileDialog.getSaveFileName(self, "Save Profile", TRIVIA_ROOT)
            if profile:
                self.save_profile(profile)
                
    def start_requested(self):
        log_err("implement me")
    def stop_requested(self):
        log_err("implement me")
    def pause_requested(self):
        log_err("implement me")
    def next_requested(self):
        log_err("implement me")
        
    def got_notification(self, notification_object):
        self.notifications.addItem(notifications)
        self._notification_dlg.show()
    def del_notification(self, notification_object):
        self.notifications.delItem(notification_object)

class _QAData(object):
    question = None
    answers = []
    id = -1
    category = None
    type = None
    
    def ask_string(self):
        pass
    def hint_string(self):
        pass
    def is_correct(self, answer):
        for a in self.answers:
            if a.lower() in answer.lower():
                return True
        return False


class _QuestionData(_QAData):
    def ask_string(self):
        return "Category %s: %s" % (self.category, self.question)
    def hint_string(self):
        ret = ""
        longest = max(self.answers)
        m = article_start_re.match(longest)
        if m:
            ret += longest[m.start():m.end()]
            longest = longest[m.end():]
            
        answer_len = len(longest)
        hint_len = 0
        
        if answer_len < 6:
            hint_len = 1
        elif answer_len < 10:
            hint_len = 3
        else:
            hint_len = 6
        
        ret += longest[0:hint_len] + ("_" * hint_len) + "[%d]" % (answer_len-hint_len)
        return ret

class _AnagramData(_QAData):
    def ask_string(self):
        return "Anagram: " + scramble_word(self.answers[0])
    def hint_string(self):
        #first and last letter
        if len (self.answers[0]) < 3:
            return ""
        return self.answers[0][0] + ("_" * (len(self.answers[0])-2)) + self.answers[0][-1]
        
class TriviaBot(object):
    help_text = ("Welcome to Yobot Trivia. Commands are prefixed with '!', "
                 "type !help for a list of commands"
                )
    def __init__(self, questions_db = None, anagrams_db = None, timeout=30,
                 interval=15, pct_trivia=50, pct_anagram=50, register_usage=True,
                 n_trivia = 35, type=None, categories=None, categories_is_blacklist = False,
                 wordlen_min = 0, wordlen_max = 0):
        if not questions_db and not anagrams_db:
            raise Exception("Either anagrams or questions db must be specified")
            
        #open databases:
        def _regexp(expr, item):
            r = re.compile(expr)
            return r.match(item) is not None
            
        if questions_db:
            self.questions_dbfile = questions_db
            self.questions_dbconn = sqlite3.connect(questions_db)
            self.questions_dbconn.row_factory = sqlite3.Row
            self.questions_dbconn.text_factory = str
            self.questions_dbconn.create_function("regexp", 2, _regexp)
            self.questions_dbcursor = self.questions_dbconn.cursor()
        if anagrams_db:
            self.anagrams_dbfile = anagrams_db
            self.anagrams_dbconn = sqlite3.connect(anagrams_db)
            self.anagrams_dbcursor = self.anagrams_dbconn.cursor()
            self.anagrams_dbconn.row_factory = sqlite3.Row
            self.anagrams_dbconn.text_factory = str
            self.anagrams_dbconn.create_function("regexp", 2, _regexp)
            self.anagrams_min = wordlen_min
            self.anagrams_max = wordlen_max
        self.scores = defaultdict(float)
        self.hint_requested = False
        self.register_usage = register_usage
        self.client_ops = yobot_interfaces.component_registry.get_component("client-operations")
        if not self.client_ops:
            raise Exception("client-operations not found")
        self.write_question = None
        
        self.timeout = timeout
        self.interval = interval
        self.timeout_cb = None
        self.next_cb = None
        
        self.n_asked_questions = 0.0
        self.n_asked_anagrams = 0.0
        self.n_trivia = n_trivia
        
        self.current_question = None
        self.current_question_type = None
        
        self.pct_trivia = pct_trivia
        self.pct_anagram = pct_anagram
        
        if questions_db and not anagrams_db:
            self.type = TYPE_TRIVIA
        elif anagrams_db and not questions_db:
            self.type = TYPE_ANAGRAMS
        else:
            self.type = TYPE_BOTH
            
        self.current_qa_object = None
        self.qa_object_questions = _QuestionData()
        self.qa_object_anagrams = _AnagramData()
        
        self.questions_categories = set()
        self.questions_categories_is_blacklist = False
        
        self.anagram_suffix_exclude = set()
        self.anagram_prefix_exclude = set()
        self.anagrams_caps_hint = False
        #start it..
        
    @property
    def n_asked_total(self):
        return float(self.n_asked_anagrams + self.n_asked_questions)
    
    def start(self):
        self.post_dispatcher()
    
    def post_dispatcher(self):
        if self.n_asked_total >= self.n_trivia:
            self.trivia_finished()
            return
        #determine which type of post to send
        if self.type == TYPE_TRIVIA:
            log_warn("questions")
            type = TYPE_TRIVIA
        elif self.type == TYPE_ANAGRAMS:
            log_warn("anagrams")
            type = TYPE_ANAGRAMS
        else:
            log_warn("mix")
            log_warn("trying...", self.n_asked_anagrams, self.n_asked_total)
            try:
                pct_current = (self.n_asked_anagrams/self.n_asked_total)*100.0
                log_err(pct_current, self.pct_anagram)
                if self.pct_anagram > pct_current:
                    type = TYPE_ANAGRAMS
                else:
                    type = TYPE_TRIVIA
            except ZeroDivisionError, e:
                log_err(e)
                if self.pct_anagram < self.pct_trivia:
                    type = TYPE_TRIVIA
                else:
                    type = TYPE_ANAGRAMS                    
        if type == TYPE_TRIVIA:
            log_err("trivia")
            fn = self._set_question
            self.current_qa_object = self.qa_object_questions
        elif type == TYPE_ANAGRAMS:
            fn = self._set_anagram
            self.current_qa_object = self.qa_object_anagrams
        
        fn()
        self.current_question_type = type
        self.hint_requested = False
        self.write_chat(self.current_qa_object.ask_string())
        self.time_asked = time()
        self.timeout_cb = self.client_ops.callLater(self.timeout, self._timeout_cb)
        
    def _set_anagram(self):
        log_err(self.anagrams_min, self.anagrams_max)
        #determine whether we can use a regex here..
        prepend = ""
        append = ""
        rstr = ""
        if len(self.anagram_prefix_exclude):
            prepend += "|".join(self.anagram_prefix_exclude)
        if len(self.anagram_suffix_exclude):
            append += "|".join(self.anagram_suffix_exclude)
        if prepend or append:
            rstr = "word NOT REGEXP '%s' AND" % (prepend + ".*" + append,)
            
        word = self.anagrams_dbcursor.execute("""SELECT word FROM words
                                                    WHERE %s LENGTH(word) >= ? AND
                                                    LENGTH(word) <= ?
                                                ORDER BY random()
                                                LIMIT 1
                                              """ % (rstr,),
                                              (self.anagrams_min, self.anagrams_max)).fetchone()
        if not word:
            log_err("can't get word")
            self.qa_object_anagrams.answers = []
            return False
        word = word[0]
        if self.anagrams_caps_hint:
            word = word.capitalize()
        log_err(word)
        self.qa_object_anagrams.answers = [word]
        self.n_asked_anagrams += 1
        return True
        
    def _set_question(self, category=None):
        log_err("")
        rstr = ""
        if len(self.questions_categories):
            l = ["'" + s + "'" for s in self.questions_categories]
            if self.questions_categories_is_blacklist:
                rstr += "NOT "
            category_expr = "category==" + l.pop()
            if len(l):
                l.insert(0, "")
                category_expr += " or category==".join(l)
            rstr += "(" + category_expr + ")"
            rstr = "WHERE " + rstr
            log_warn(rstr)
        res = self.questions_dbcursor.execute("""
                                    SELECT * FROM questions
                                     %s
                                     ORDER BY frequency ASC, random()
                                     LIMIT 1
                                    """ % (rstr,)).fetchone()
        if self.register_usage:
            self.questions_dbcursor.execute("""
                                  UPDATE questions
                                   SET frequency = (frequency+1)
                                    WHERE id = ?
                                  """, (res["id"],))
        
        alt_answers = pickle.loads(res["alt_answers"])
        answers = (res["answer"],) + ( alt_answers if alt_answers else ())
        
        self.qa_object_questions.answers = answers
        self.qa_object_questions.category = res["category"]
        self.qa_object_questions.id = res["id"]
        self.qa_object_questions.question = res["question"]
        self.n_asked_questions += 1
        return True
                
    def command_responder(self, user, command_name):
        #hint
        ret = ""
        if command_name == "hint":
            if not self.current_qa_object:
                return
            ret = self.current_qa_object.hint_string()
            if not ret:
                ret = "Couldn't get hint"
                self.hint_requested = False
            else:
                self.hint_requested = True
        elif command_name == "scores":
            if not len(self.scores):
                return
            ret = "Scores: "
            for k, v in sorted(self.scores.items(), key=lambda i: i[1]):
                ret += "%s : %0.1f, " % (k, v)
        elif command_name == "leader":
            if not len(self.scores):
                return
            ret = "Leader: "
            leader = sorted(self.scores.items(), key=lambda i: i[1])[0]
            name, score = leader
            ret += "%s with %0.1f points" % (name, score)
        elif command_name == "help":
            ret = "commands: hint scores leader"
        else:
            ret = self.help_text
        self.write_chat(ret)
        
    def got_response(self, user, response):
        if response.startswith("!"):
            response = response.strip("!")
            self.command_responder(user, response)
            return
        #not a command, must be an answer...
        if not (self.current_qa_object and self.current_qa_object.is_correct(response)):
            return
        #we have an answer
        answer_time = int(time() - self.time_asked)
        if answer_time   < 3:
            points = 100
        elif answer_time < 5:
            points = 50
        elif answer_time < 10:
            points = 25
        elif answer_time < 15:
            points = 10
        else:
            points = 5
        points = float(points)
        if self.hint_requested:
            points /= 2
        self.scores[user] += points
        
        if self.timeout_cb:
            self.client_ops.cancelCallLater(self.timeout_cb)
            self.timeout_cb = None
        self.timeout_cb = None
        self.write_chat(
            "%s awarded %0.1f points [%0.1f total] for answer %s. "
            "Response time was %d secs. "
            "Next question in %d secs" %
            (user, points, self.scores[user], self.current_qa_object.answers[0], answer_time, self.interval))
        self.current_qa_object = None
        self.next_question()
        
    def _trivia_finished(self):
        pass
    
    def write_chat(self, message):
        log_err("override me!")
    
    def trivia_finished(self):
        log_err("override me")
    
    def _timeout_cb(self):
        #post an answer message, and then move on to the next question...
        self.write_chat("Answer is %s" % (self.current_qa_object.answers[0],))
        self.post_dispatcher() #no timeout here
        
    def next_question(self):
        self.next_cb = self.client_ops.callLater(self.interval, self.post_dispatcher)
    
    def _cleanup(self):
        if self.timeout_cb:
            self.client_ops.cancelCallLater(self.timeout_cb)
            self.timeout_cb = None
        if self.next_cb:
            self.client_ops.cancelCallLater(self.next_cb)
            self.next_cb = None
        self.current_qa_object = None
        self.current_question_type = None
        
    def skip(self):
        if self.current_question_type == TYPE_ANAGRAMS:
            self.n_asked_anagrams -= 1
        elif self.current_question_type == TYPE_TRIVIA:
            self.n_asked_questions -= 1
        
        self._cleanup()
        self.post_dispatcher()
    
    def pause(self):
        if self.current_question_type == TYPE_ANAGRAMS:
            self.n_asked_anagrams -= 1
        elif self.current_question_type == TYPE_TRIVIA:
            self.n_asked_questions -= 1

        self._cleanup()
        self.write_chat("paused")
        
    def unpause(self):
        self.post_dispatcher()
        
    def stop(self):
        self._cleanup()
        self.trivia_finished()        
    
    def __del__(self):
        anagrams_dbconn = getattr(self, "anagrams_dbconn")
        questions_dbconn = getattr(self, "questions_dbconn")
        if anagrams_dbconn:
            anagrams_dbconn.close()
        if questions_dbconn:
            questions_dbconn.close()
        super(TriviaBot, self).__del__()
        
class TriviaPlugin(object):
    yobot_interfaces.implements(yobot_interfaces.IYobotUIPlugin)
    plugin_name = "triviabot"
    def __init__(self):
        self.gui = TriviaGui()        
        self.room = None
        self.pending_room = None
        self.gui.start_requested = self.start_requested
        self.triviabot = None
        
        #test stuff
        self.gui.widgets.questions_type.setCurrentIndex(2)
        self.gui.widgets.questions_database.setText("/home/mordy/src/yobot/py/triviabot/foo.sqlite")
        self.gui.widgets.anagrams_database.setText("/home/mordy/src/yobot/py/triviabot/words.db")
        self.gui.widgets.anagrams_letters_min.setValue(5)
        self.gui.widgets.room.insertItem(0, "muc@muc.debmed.mordnet")
        self.gui.widgets.room.setCurrentIndex(0)
        self.gui.widgets.account.setCurrentIndex(0)
        log_err("done")
    #plugin hooks
    def accountConnected(self, acct):
        if self.triviabot: self.triviabot.stop()
    def accountConnectionFailed(self, acct, msg):
        r = SimpleNotice(acct, msg)
        self.gui.notifications.addItem(r)
        if self.triviabot: self.triviabot.stop()
    def accountConnectionRemoved(self, acct):
        if self.triviabot: self.triviabot.stop()
        
    def gotMessage(self, acct, msg):
        if (not self.triviabot or
            msg.name != self.room or 
            msg.prplmsgflags & (yobotproto.PURPLE_MESSAGE_DELAYED|
                                yobotproto.PURPLE_MESSAGE_SEND)):
            return

        user = msg.who
        e = lxml.html.fromstring(msg.txt)
        txt = e.text_content()
        self.triviabot.got_response(user, txt)
        
    def roomJoined(self, acct, room_name):
        if room_name == self.pending_room and acct == self.account:
            self._start_trivia()
        
    def chatUserJoined(self, acct, room, user):
        pass
    def chatUserLeft(self, acct, room, user):
        pass
    def gotRequest(self, request_obj):
        log_err("")
        self.gui.got_notification(request_obj)
    def delRequest(self, request_obj):
        self.gui.del_notification(request_obj)
    
    #trivia hooks
    def start_requested(self):
        w = self.gui.widgets
        self.room = self.gui.widgets.room.currentText()
        if not self.room:
            QErrorMessage(self.gui).showMessage("No room selected")
            return
        self.room = str(self.room)
        if not w.questions_database and not w.anagrams_database:
            QErrorMessage(self.gui).showMessage("No databases specified")
            return
        #get current account and room, see if we've joined it yet
        joined_rooms = yobot_interfaces.component_registry.get_component("joined-rooms")
        if joined_rooms is None:
            raise Exception("joined-rooms component does not exist")
        
        int_index = self.gui.widgets.account.currentIndex()
        index = self.gui.model.index(int_index)
        account = index.internalPointer()
        self.account = account
        
        if not self.room in joined_rooms[account]:
            #send request to join the room
            account.joinchat(self.room)
            self.pending_room = self.room
            return
        
        self._start_trivia()
        
    def _start_trivia(self):
        #get parameters from the gui
        w = self.gui.widgets
        _kwargs = {}
        _general_opts = {}
        _general_opts["interval"] = w.post_interval.value()
        _general_opts["timeout"] = w.answer_timeout.value()
        _general_opts["pct_anagram"] = w.percent_anagrams.value()
        _general_opts["pct_trivia"] = w.percent_trivia.value()
        _general_opts["n_trivia"] = w.amount.value()
        _general_opts["register_usage"] = w.updatedb_bool.isChecked()
        
        _questions_opts = {}
        _questions_opts["questions_db"] = str(w.questions_database.text())
        _questions_opts["categories"] = None
        _questions_opts["categories_is_blacklist"] = False
        
        _anagrams_opts = {}
        _anagrams_opts["anagrams_db"] = str(w.anagrams_database.text())
        _anagrams_opts["wordlen_min"] = w.anagrams_letters_min.value()
        _anagrams_opts["wordlen_max"] = w.anagrams_letters_max.value()
        
        _type = w.questions_type.currentText()
        _type = str(_type).lower()
        
        _kwargs.update(_general_opts)
        if _type in ("trivia", "mix"):
            _kwargs.update(_questions_opts)
        if _type in ("anagrams", "mix"):
            _kwargs.update(_anagrams_opts)
        self.triviabot = TriviaBot(**_kwargs)
        
        
        self.gui.pause_requested = self.triviabot.pause
        self.gui.next_requested = self.triviabot.skip
        self.gui.stop_requested = self.triviabot.stop
        
        self.triviabot.write_chat = self._write_chat
        self.triviabot.trivia_finished = self._trivia_stopped
        
        #update spinboxes
        for widget, bot_var in (
            ("amount", "n_trivia"),
            ("answer_timeout", "timeout"),
            ("post_interval", "interval"),
            ("percent_trivia", "pct_trivia"),
            ("percent_anagrams", "pct_anagram"),
            ("anagrams_letters_min", "anagrams_min"),
            ("anagrams_letters_max", "anagrams_max")):
            signal_connect(getattr(w, widget), SIGNAL("valueChanged(int)"),
                           lambda i, bot_var=bot_var: setattr(self.triviabot, bot_var, i))
            #and also set the initial value:
            setattr(self.triviabot, bot_var, int(getattr(w, widget).value()))
        
        #booleans:
        for widget, bot_var in (
            ("anagrams_caps_hint", "anagrams_caps_hint"),
            ("questions_use_categories", "questions_use_categories"),
            ("anagrams_use_nfixes", "anagrams_use_nfixes")):
            signal_connect(getattr(w, widget), SIGNAL("toggled(bool)"),
                           lambda b, bot_var=bot_var: setattr(self.triviabot, bot_var, b))
            
        
        #for various blacklists and such:
        signal_connect(self.gui.widgets.questions_blacklist, SIGNAL("toggled(bool)"),
                       lambda b: setattr(self.triviabot, "questions_categories_is_blacklist", b))
        self.triviabot.questions_categories_is_blacklist = self.gui.widgets.questions_blacklist.isChecked()
        
        self.triviabot.anagram_suffix_exclude = self.gui.anagrams_suffix_blacklist
        self.triviabot.anagram_prefix_exclude = self.gui.anagrams_prefix_blacklist
        self.triviabot.questions_categories = self.gui.selected_questions_categories
        
        self.triviabot.start()
        self._set_editable_widgets(False)
        
    def _set_editable_widgets(self, enable=True):
        for w in ("questions_type", "select_anagrams_dbfile", "select_questions_dbfile",
                  "account", "room", "start"):
            getattr(self.gui.widgets, w).setEnabled(enable)
        
        for w in ("pause", "stop", "next"):
            getattr(self.gui.widgets, w).setEnabled(True if not enable else False)
        
    def _trivia_stopped(self):
        self._set_editable_widgets(True)
        del self.triviabot
        self.triviabot = None
    
    def _write_chat(self, message):
        if not self.account:
            return
        message = self.gui.fmtstr % (html_escape(message),)
        self.account.sendmsg(self.room, message, chat=True)