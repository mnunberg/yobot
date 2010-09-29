#!/usr/bin/env python
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os.path
import sys


#long, boring, linear code.. but less of a headache than using designer

def point_to_html(x):
    #copied from libpurple/protocols/yahoo/util.c
    if (x < 9):
            return 1
    if (x < 11): 
            return 2
    if (x < 13):
            return 3
    if (x < 17):
            return 4
    if (x < 25):
            return 5
    else:
            return 6

connect = QObject.connect
def mk_selectfile_layout(parent=None):
    layout = QHBoxLayout()
    layout.addWidget(QLabel("Database"))
    edit = QLineEdit(parent)
    edit.setReadOnly(True)
    layout.addWidget(edit)
    button = QPushButton(parent)
    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    button.setText("...")
    button.setIcon(QIcon(":/icons/res/16x16/places/server-database.png"))
    button.setMaximumSize(45,27)
    layout.addWidget(button)
    layout.setStretch(0, 1)
    layout.setStretch(1,100)
    layout.setStretch(2,1)
    return layout, edit, button

def polish_formlayout(lo):
    lo.setRowWrapPolicy(QFormLayout.DontWrapRows)
    lo.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    lo.setLabelAlignment(Qt.AlignRight)
    lo.setFormAlignment(Qt.AlignLeft|Qt.AlignTop)

def copy_size(size):
    return QSize(size.width(), size.height())

def xfloat_range(begin,end,step):
    print "got begin", begin, "end", end, "step", step
    while begin < end:
        yield begin
        begin += step
        
def xfloat_range_decrement(begin, end, step):
    while begin > end and begin > 0:
        yield begin
        begin -= step

            
def print_qsize(sz, title=""):
    print title, "W: ", sz.width(), " H: ", sz.height()
    
class AnimatedLayout(QLayout):
    STATE_HIDDEN, STATE_VISIBLE, STATE_ANIMATING = range(3)
    USE_ANIMATIONS = True if not sys.platform.lower() == "darwin" else False
    def __init__(self, child, size, parent = None):
        super(type(self),self).__init__()
        self._name = ""
        
        child.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setSizeConstraint(QLayout.SetFixedSize)
        self.item = None
        
        self.child = child
        self.addWidget(child)
        self.mandated_size = QSize(size.width(), 0)
        self.preferred_size = size

        self.setContentsMargins(0,0,0,0)
        self.setSpacing(0)
        
        self.duration = 250
        
        self.show = self.startShow
        self.hide = self.startHide
        self.child.show = self.show
        self.child.hide = self.hide        
        self.child_state = self.STATE_VISIBLE
    
    #these two segfaulted if i tried to do anything legit with them?
    def addItem(self, item):
        self.item = item
    
    def count(self):
        if self.item:
            return 1
        return 0
    def itemAt(self, index):
        if index == 0 and self.item:
            return self.item
        else:
            return None
        
    def setGeometry(self, rect):
        if not self.child_state in (self.STATE_ANIMATING, self.STATE_VISIBLE):
            return
        #super(type(self), self).setGeometry(rect)
        self.child.setGeometry(rect)
    
    def sizeHint(self):
        return self.mandated_size
    
    def setAnimationDuration(self, msecs):
        self.duration = msecs
            
    def startShow(self):
        self._start_animation(True)
    def startHide(self):
        self._start_animation(False)
    
    def _start_animation(self, show=True):
        if not self.USE_ANIMATIONS:
            g = self.child.geometry()
            self.child_state = self.STATE_ANIMATING
            if show:
                g.setHeight(self.preferred_size.height())
            else:
                g.setHeight(0)
            self.child.setGeometry(g)
            self.mandated_size.setHeight(g.height())
            self.update()
            self.child_state = self.STATE_VISIBLE if show else self.STATE_HIDDEN
            return
            
        self.update()
        a = QPropertyAnimation(self.child, "geometry", self)
        g = self.child.geometry()
        g.setHeight(0)
        a.setStartValue(g)
        g.setHeight(self.preferred_size.height())
        a.setEndValue(g)
        a.setEasingCurve(QEasingCurve.OutQuad)
        a.setDuration(self.duration)
        def valueChanged(qv):
            r = qv.toRect()
            self.mandated_size.setHeight(r.height())
            self.update()
        connect(a, SIGNAL("valueChanged(QVariant)"), valueChanged)
        
        if not show:
            a.setDirection(a.Backward)
            connect(a, SIGNAL("finished()"), lambda: setattr(self, "child_state", self.STATE_HIDDEN))
        else:
            a.setDirection(a.Forward)
            connect(a, SIGNAL("finished()"), lambda: setattr(self, "child_state", self.STATE_VISIBLE))
        
        self.child_state=self.STATE_ANIMATING
        a.start(a.DeleteWhenStopped)

    
    def setVisible(self, b):
        "convenience method"
        if b:
            self.startShow()
        else:
            self.startHide()        


class TGui(QMainWindow):
    FILE_EXISTING, FILE_NEW = range(2)
    FONT, COLOR, FORMAT_RESET = range(3)
    def __init__(self, parent=None):
        "Sets up the layout"
        QMainWindow.__init__(self, parent)
        #make the main layout and central widget...
        self.setCentralWidget(QWidget(self))
        self.main_layout = QVBoxLayout(self.centralWidget())
        self.layout().setSizeConstraint(QLayout.SetFixedSize)
        self.show()
        
        #Form layout for account and room options...
        self.account = QComboBox(self)
        self.account.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.room = QComboBox(self)
        self.room.setEditable(True)
        self.room.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        form_ar = QFormLayout()
        polish_formlayout(form_ar)
        
        form_ar.setWidget(0, form_ar.LabelRole, QLabel("Account", self))
        form_ar.setWidget(0, form_ar.FieldRole, self.account)
        
        form_ar.setWidget(1, form_ar.LabelRole, QLabel("Room", self))
        form_ar.setWidget(1, form_ar.FieldRole, self.room)
        
        self.main_layout.addLayout(form_ar)
        
        #trivia, type, interval | amount, anagrams, trivia
        twin = QHBoxLayout();
        right = QFormLayout(); polish_formlayout(right)
        left = QFormLayout(); polish_formlayout(left)
        
        self.questions_type = QComboBox(self)
        self.questions_type.addItems(("Mix", "Anagrams", "Trivia"))
        self.post_interval = QSpinBox(self)
        self.post_interval.setSuffix(" sec")
        self.answer_timeout = QSpinBox(self)
        self.answer_timeout.setSuffix(" sec")
        self.amount = QSpinBox(self)
        self.percent_anagrams = QSpinBox(self)
        self.percent_anagrams.setSuffix("%")
        self.percent_trivia = QSpinBox()
        self.percent_trivia.setSuffix("%")
        
        l_left = list()
        l_left.append(("Type",  self.questions_type))
        l_left.append(("Interval",  self.post_interval))
        l_left.append(("Timeout",  self.answer_timeout))
        
        l_right = list()
        l_right.append(("Amount",  self.amount))
        l_right.append(("Anagrams",  self.percent_anagrams))
        l_right.append(("Trivia",  self.percent_trivia))
        
        for form,  l in ((left,  l_left), (right,  l_right)):
            for i in range(len(l)):
                form.setWidget(i,  QFormLayout.LabelRole,  QLabel(l[i][0], self))
                form.setWidget(i,  QFormLayout.FieldRole,  l[i][1])
        
        del l_left
        del l_right
        
        twin.addLayout(left)
        twin.addLayout(right)
        self.main_layout.addLayout(twin)
        
        self.questions_opts = QGroupBox(self)
        self.questions_opts.setTitle("Trivia Options (Categories)")
        self.questions_opts.setFlat(False)
        layout = QVBoxLayout()
        self.questions_opts.setLayout(layout)
        
        file_layout, self.questions_database, self.select_questions_dbfile = mk_selectfile_layout(self.questions_opts)
        layout.addLayout(file_layout)
        
        self.questions_use_categories = QCheckBox("Categories..")
        layout.addWidget(self.questions_use_categories)
        
        bwlist = QHBoxLayout()
        self.questions_blacklist, self.questions_whitelist = QRadioButton("Blacklist", self.questions_opts), QRadioButton("Whitelist", self.questions_opts)
        bwlist.addWidget(self.questions_blacklist)
        bwlist.addWidget(self.questions_whitelist)
        bwlist.addItem(QSpacerItem(1,1,QSizePolicy.Expanding, QSizePolicy.Minimum))
        
                        
        self.questions_categories_params = QFrame(self.questions_opts)
        self.questions_categories_params.setStyleSheet("font-size:8pt")
        catlayout = QGridLayout(self.questions_categories_params)
        self.questions_categories_params.setLayout(catlayout)
        catlayout.addLayout(bwlist, 0, 0, 1, 2)
        catlayout.addWidget(QLabel("Categories", self.questions_categories_params), 1, 0, Qt.AlignCenter)
        catlayout.addWidget(QLabel("Selected", self.questions_categories_params), 1, 1, Qt.AlignCenter)
        catlayout.setContentsMargins(0,0,0,0)
        
        self.questions_categories, self.selected_categories = QListWidget(self.questions_categories_params), QListWidget(self.questions_categories_params)
        catlayout.addWidget(self.questions_categories, 2, 0)
        catlayout.addWidget(self.selected_categories, 2, 1)
        
        self.categories_animation = AnimatedLayout(self.questions_categories_params, QSize(100,125),)
        
        #layout.addWidget(self.questions_categories_params)
        layout.addLayout(self.categories_animation)
        
        self.main_layout.addWidget(self.questions_opts)
        
        self.anagrams_opts = QGroupBox(self)
        self.anagrams_opts.setTitle("Anagram Options (Lengths, Patterns)")
        layout = QVBoxLayout()
        self.anagrams_opts.setLayout(layout)
        f_layout, self.anagrams_database, self.select_anagrams_dbfile = mk_selectfile_layout(self.anagrams_opts)
        layout.addLayout(f_layout)
        hb = QHBoxLayout()
        self.anagrams_letters_min, self.anagrams_letters_max = QSpinBox(self.anagrams_opts), QSpinBox(self.anagrams_opts)
        self.anagrams_letters_min.setPrefix("From ")
        self.anagrams_letters_min.setSuffix(" To")
        self.anagrams_letters_max.setSuffix(" Letters")
        hb.addWidget(self.anagrams_letters_min)
        hb.addWidget(self.anagrams_letters_max)
        layout.addLayout(hb)
        
        self.anagrams_caps_hint = QCheckBox("Capitalize First Letter", self.anagrams_opts)
        self.anagrams_use_nfixes = QCheckBox("Use Prefixes and Suffixes", self.anagrams_opts)
        layout.addWidget(self.anagrams_caps_hint)
        layout.addWidget(self.anagrams_use_nfixes)
        
        self.suffix_prefix_options = QFrame(self.anagrams_opts)
        self.suffix_prefix_options.setStyleSheet("font-size:8pt")
        nfix_layout = QGridLayout()
        nfix_layout.setContentsMargins(0,0,0,0)
        self.suffix_prefix_options.setLayout(nfix_layout)
        nfix_layout.addWidget(QLabel("Prefixes"), 0, 0, Qt.AlignCenter)
        nfix_layout.addWidget(QLabel("Suffixes"), 0, 1, Qt.AlignCenter)
                
        #make the layout for the entry buttons
        for params in ((0, "prefix"), (1, "suffix")):
            index, type = params
            list_ = QListWidget(self.suffix_prefix_options)
            nfix_layout.addWidget(list_, 1, index)
            setattr(self, type + "_list", list_)
            hb = QHBoxLayout()
            edit = QLineEdit(self.suffix_prefix_options)
            add = QToolButton(self.suffix_prefix_options)
            add.setText("+")
            del_ = QToolButton(self.suffix_prefix_options)
            del_.setText("-")
            hb.addWidget(edit)
            hb.addWidget(add)
            hb.addWidget(del_)
            hb.setSpacing(0)
            setattr(self, type + "_input", edit)
            setattr(self, type + "_add", add)
            setattr(self, type + "_del", del_)
            nfix_layout.addLayout(hb, 2, index)
            
        #layout.addWidget(self.suffix_prefix_options)
        
        self.nfix_animation = AnimatedLayout(self.suffix_prefix_options, QSize(100,125))
        layout.addLayout(self.nfix_animation)
        self.main_layout.addWidget(self.anagrams_opts)
        
        
        self.updatedb_bool = QCheckBox("Register Usage", self)
        self.main_layout.addWidget(self.updatedb_bool)
        
        
        #make a new layout for the font button, don't let it expand horizontally if there's no need
        cf_layout = QHBoxLayout()
        if sys.platform.lower() == "darwin":
            print "hi"
            #self.change_font = QPushButton(self)
            self.change_font = QToolButton(self)
            self.change_font.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            self.change_font.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            self.change_font_extrastyle = """ border:4px solid #000000; border-radius:6px;
                        text-align:center; background-color:white; """
        else:
            self.change_font = QPushButton(self)
            self.change_font.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            self.change_font_extrastyle = ""
        self.change_font.setStyleSheet("QAbstractButton {" + self.change_font_extrastyle + "}")
        self.change_font.setText("Font")
        self.change_font.setIcon(QIcon(":/icons/icons/format-text-color.png"))
        self.font_menu = QMenu(self.change_font)
        self.action_change_font_style = self.font_menu.addAction(QIcon(":/icons/icons/format-text-bold.png"),"Style and Face")
        self.action_change_font_color = self.font_menu.addAction(QIcon(":/icons/icons/format-fill-color.png"),"Color")
        self.action_change_font_reset = self.font_menu.addAction(QIcon(":/icons/icons/dialog-close.png"), "Reset Formatting")
        cf_layout.addStretch(25)
        cf_layout.addWidget(self.change_font, stretch=75)
        cf_layout.addStretch(25)
        self.main_layout.addLayout(cf_layout)
        
        #control buttons:
        bbox = QHBoxLayout()
        bbox.addStretch(0)
        for action, icon in (
            ("start", "media-playback-start.png"),
            ("pause", "media-playback-pause.png"),
            ("stop", "media-playback-stop.png"),
            ("next", "media-skip-forward.png")):
            button = QToolButton(self)
            button.setIcon(QIcon(":/icons/res/16x16/actions/" + icon))
            bbox.addWidget(button)
            setattr(self, action, button)
        bbox.addStretch(-1)
        bbox.setSpacing(3)
        self.main_layout.addLayout(bbox)
        
        #actions:
        self.actionConnect = QAction(QIcon(":/icons/icons/network-connect.png"), "Connect..", self)
        self.actionConnect.setCheckable(True)
        
        self.actionLoad = QAction(QIcon(":/icons/res/16x16/actions/document-open.png"), "Load", self)
        self.actionSave = QAction(QIcon(":/icons/res/16x16/actions/document-save.png"), "Save", self)
        self.actionSave_As = QAction(QIcon(":/icons/res/16x16/actions/document-save-as.png"), "Save As..", self)
        
        self.menubar = QMenuBar(self)
        self.menu_profile = QMenu("Profile", self.menubar)
        self.menu_profile.addAction(self.actionLoad)
        self.menu_profile.addAction(self.actionSave)
        self.menu_profile.addAction(self.actionSave_As)
        
        self.menu_actions = QMenu("Actions", self.menubar)
        self.menu_actions.addAction(self.actionConnect)
        self.menu_components = QMenu("Components", self.menubar)
        self.menubar.addMenu(self.menu_profile)
        self.menubar.addMenu(self.menu_actions)
        self.menubar.addMenu(self.menu_components)
        #self.menubar.setGeometry(QRect(0,0, 329, 29))
        self.setMenuBar(self.menubar)
        
        self.signal_util()
        
    
    def select_file(self, field, initial_path="", select_type=FILE_EXISTING, caption=""):
        """Select a file. The caller may wish to attach a signal to the field's
        textChanged signal to process further actions"""
        dlgcls = QFileDialog.getOpenFileName if select_type == self.FILE_EXISTING else QFileDialog.getSaveFileName
        #first see if initial_path is specified, and use its basename,
        #else use the basename of the existing file in the field
        if initial_path:
            initial_path = os.path.dirname(initial_path)
        else:
            if field.text():
                initial_path = os.path.basename(str(field.text()))
            #else, just use the "" value
        fname = dlgcls(self, caption, initial_path)
        if fname:
            field.setText(fname)
    
    def type_changed(self, text):
        w = self
        text = str(text).lower()
        if text == "mix":
            w.questions_opts.show()
            w.anagrams_opts.show()
        elif text == "anagrams":
            w.anagrams_opts.show()
            w.questions_opts.hide()
        elif text == "trivia":
            w.questions_opts.show()
            w.anagrams_opts.hide()
            
    def font_color_change(self, type=FONT):
        if type == self.FONT:
            font, b = QFontDialog.getFont(self.current_font, None, "Select Font",
                                          QFontDialog.DontUseNativeDialog)
            if not b:
                return
            self.current_font = font
        elif type == self.COLOR:
            color = QColorDialog.getColor(self.current_color, None, "select color",
                                          QColorDialog.DontUseNativeDialog)
            if not color.isValid():
                return
            self.current_color = color
        elif type == self.FORMAT_RESET:
            self.current_color = QColor()
            self.current_font = QFont()
        
        self._update_fmtstr()
        self._gen_font_stylesheet()
    
        
    def _gen_font_stylesheet(self):
        self.change_font.setStyleSheet(("QAbstractButton {" + 
          ("font-weight: bold; " if self.current_font.bold() else "") +
          ("font-style: italic; " if self.current_font.italic() else "") +
          ("text-decoration: underline; " if self.current_font.underline() else "") +
          ("font-size: %dpt; " % (self.current_font.pointSize(),)) +
          ("font-family: %s; " % (self.current_font.family(),)) +
          ("color: %s; " % (self.current_color.name(),))
        + self.change_font_extrastyle + " } "))

    
    def _update_fmtstr(self):
        fmt_open = "<font face='%s' size='%d' absz='%d' color='%s'>" % (
            self.current_font.family(), point_to_html(self.current_font.pointSize()),
            self.current_font.pointSize(), self.current_color.name())
        fmt_close = ""
        for f, tag in (("bold", "b"), ("italic", "i"), ("underline", "u")):
            if getattr(self.current_font, f)():
                fmt_open += "<%s>" % (tag,)
                fmt_close += "</%s>" % (tag,)
        fmt_close += "</font>"
        self.fmtstr = fmt_open + "%s" + fmt_close

    
    def signal_util(self):
        "wire up signals and events"
        w = self
        signal_connect = QObject.connect
        def _sync_minmax_min(i):
            if w.anagrams_letters_max.value() < i:
                w.anagrams_letters_max.setValue(i)
        def _sync_minmax_max(i):
            if w.anagrams_letters_min.value() > i:
                w.anagrams_letters_min.setValue(i)
                
        #synchronize letter min/max values
        signal_connect(w.anagrams_letters_min, SIGNAL("valueChanged(int)"), _sync_minmax_min)
        signal_connect(w.anagrams_letters_max, SIGNAL("valueChanged(int)"), _sync_minmax_max)
        
        #synchronize pct values
        signal_connect(w.percent_anagrams, SIGNAL("valueChanged(int)"),
                       lambda i: w.percent_trivia.setValue(100-i))
        signal_connect(w.percent_trivia, SIGNAL("valueChanged(int)"),
                       lambda i: w.percent_anagrams.setValue(100-i))
        
        #show/hide specific parameters
        signal_connect(w.questions_type, SIGNAL("currentIndexChanged(QString)"), self.type_changed)
        
        #for extended options
        signal_connect(w.questions_use_categories, SIGNAL("toggled(bool)"), self.categories_animation.setVisible)
        signal_connect(w.anagrams_use_nfixes, SIGNAL("toggled(bool)"), self.nfix_animation.setVisible)
        
        #file selection:
        signal_connect(w.select_questions_dbfile, SIGNAL("clicked()"),
                       lambda: self.select_file(self.questions_database, caption="Select Questions DB"))
        signal_connect(w.select_anagrams_dbfile, SIGNAL("clicked()"),
                       lambda: self.select_file(self.anagrams_database, caption="Select Anagram DB"))
        
        signal_connect(w.change_font, SIGNAL("clicked()"), lambda: self.font_menu.exec_(QCursor().pos()))
        self.current_font = QFont()
        self.current_color = QColor()
        self.fmtstr = "%s"
        signal_connect(w.action_change_font_color, SIGNAL("activated()"), lambda: self.font_color_change(self.COLOR))
        signal_connect(w.action_change_font_style, SIGNAL("activated()"), lambda: self.font_color_change(self.FONT))
        signal_connect(w.action_change_font_reset, SIGNAL("activated()"), lambda: self.font_color_change(self.FORMAT_RESET))
        
        
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    mw = TGui()
    app.exec_()
    
