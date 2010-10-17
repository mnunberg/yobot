# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '_config_dialog.ui'
#
# Created: Sat Oct 16 01:38:23 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_config_dialog(object):
    def setupUi(self, config_dialog):
        config_dialog.setObjectName("config_dialog")
        config_dialog.resize(326, 300)
        config_dialog.setTabPosition(QtGui.QTabWidget.North)
        config_dialog.setTabShape(QtGui.QTabWidget.Rounded)
        config_dialog.setDocumentMode(True)
        config_dialog.setMovable(True)
        self.general_tab = QtGui.QWidget()
        self.general_tab.setObjectName("general_tab")
        self.formLayout = QtGui.QFormLayout(self.general_tab)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName("formLayout")
        self.label = QtGui.QLabel(self.general_tab)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.agent_address = QtGui.QLineEdit(self.general_tab)
        self.agent_address.setObjectName("agent_address")
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.agent_address)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/res/16x16/categories/preferences-other.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        config_dialog.addTab(self.general_tab, icon, "")
        self.accounts_tab = QtGui.QWidget()
        self.accounts_tab.setObjectName("accounts_tab")
        self.verticalLayout = QtGui.QVBoxLayout(self.accounts_tab)
        self.verticalLayout.setObjectName("verticalLayout")
        self.accounts = QtGui.QTreeWidget(self.accounts_tab)
        self.accounts.setColumnCount(2)
        self.accounts.setObjectName("accounts")
        self.accounts.headerItem().setText(0, "Account")
        self.accounts.headerItem().setText(1, "Protocol")
        self.verticalLayout.addWidget(self.accounts)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 10, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.account_add = QtGui.QPushButton(self.accounts_tab)
        self.account_add.setObjectName("account_add")
        self.horizontalLayout.addWidget(self.account_add)
        self.account_del = QtGui.QPushButton(self.accounts_tab)
        self.account_del.setObjectName("account_del")
        self.horizontalLayout.addWidget(self.account_del)
        self.account_edit = QtGui.QPushButton(self.accounts_tab)
        self.account_edit.setObjectName("account_edit")
        self.horizontalLayout.addWidget(self.account_edit)
        self.verticalLayout.addLayout(self.horizontalLayout)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/res/16x16/apps/preferences-contact-list.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        config_dialog.addTab(self.accounts_tab, icon1, "")
        self.appearance_tab = QtGui.QWidget()
        self.appearance_tab.setObjectName("appearance_tab")
        self.gridLayout = QtGui.QGridLayout(self.appearance_tab)
        self.gridLayout.setVerticalSpacing(12)
        self.gridLayout.setObjectName("gridLayout")
        self.sample_text = QtGui.QPlainTextEdit(self.appearance_tab)
        self.sample_text.setMaximumSize(QtCore.QSize(16777215, 50))
        self.sample_text.setStyleSheet("None")
        self.sample_text.setObjectName("sample_text")
        self.gridLayout.addWidget(self.sample_text, 2, 0, 1, 2)
        self.select_color = QtGui.QPushButton(self.appearance_tab)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/icons/format-fill-color.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.select_color.setIcon(icon2)
        self.select_color.setObjectName("select_color")
        self.gridLayout.addWidget(self.select_color, 0, 1, 1, 1)
        self.scrollArea = QtGui.QScrollArea(self.appearance_tab)
        self.scrollArea.setStyleSheet("QScrollArea {\n"
"border-radius:6px;\n"
"border:3px groove palette(dark);\n"
"margin:4px;\n"
"}")
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtGui.QWidget(self.scrollArea)
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 294, 132))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout_2 = QtGui.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_2.setVerticalSpacing(0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.html_relsize = QtGui.QCheckBox(self.scrollAreaWidgetContents)
        self.html_relsize.setObjectName("html_relsize")
        self.gridLayout_2.addWidget(self.html_relsize, 0, 0, 1, 2)
        self.show_joinpart = QtGui.QCheckBox(self.scrollAreaWidgetContents)
        self.show_joinpart.setObjectName("show_joinpart")
        self.gridLayout_2.addWidget(self.show_joinpart, 1, 0, 1, 2)
        self.use_sizelimit = QtGui.QCheckBox(self.scrollAreaWidgetContents)
        self.use_sizelimit.setObjectName("use_sizelimit")
        self.gridLayout_2.addWidget(self.use_sizelimit, 2, 0, 1, 2)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem1, 5, 0, 1, 1)
        self.sizelimits = QtGui.QFrame(self.scrollAreaWidgetContents)
        self.sizelimits.setStyleSheet("QFrame {\n"
"border:2px groove palette(dark);\n"
"border-radius:5px;\n"
"background:none;\n"
"margin:0px;\n"
"padding:0px;\n"
"}\n"
"QLabel {border:none;\n"
"text-align:center;}\n"
"QSpinBox {\n"
"margin:0px;;\n"
"padding:0px;\n"
"border-width:1px;\n"
"padding-right:20px;\n"
"background:argb(0,0,0,0);\n"
"}\n"
"::up-button, ::down-button {\n"
"subcontrol-origin:padding;\n"
"width:20px;\n"
"margin-right:1px;\n"
"border-width:1px;\n"
"background:palette(dark);\n"
"border-style:inset;\n"
"}\n"
"::up-button {margin-top:2px;}\n"
"::down-button {margin-bottom:2px;}\n"
"::up-arrow, ::down-arrow {\n"
"width:5px;\n"
"height:3px;\n"
"background:palette(text);\n"
"}")
        self.sizelimits.setFrameShape(QtGui.QFrame.NoFrame)
        self.sizelimits.setFrameShadow(QtGui.QFrame.Raised)
        self.sizelimits.setObjectName("sizelimits")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.sizelimits)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setMargin(0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtGui.QLabel(self.sizelimits)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.sizelimit_min = QtGui.QSpinBox(self.sizelimits)
        self.sizelimit_min.setStyleSheet("None")
        self.sizelimit_min.setAlignment(QtCore.Qt.AlignCenter)
        self.sizelimit_min.setSuffix("")
        self.sizelimit_min.setPrefix("")
        self.sizelimit_min.setMinimum(6)
        self.sizelimit_min.setMaximum(48)
        self.sizelimit_min.setObjectName("sizelimit_min")
        self.horizontalLayout_2.addWidget(self.sizelimit_min)
        self.label_3 = QtGui.QLabel(self.sizelimits)
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        self.sizelimit_max = QtGui.QSpinBox(self.sizelimits)
        self.sizelimit_max.setAlignment(QtCore.Qt.AlignCenter)
        self.sizelimit_max.setSuffix("")
        self.sizelimit_max.setMaximum(48)
        self.sizelimit_max.setObjectName("sizelimit_max")
        self.horizontalLayout_2.addWidget(self.sizelimit_max)
        self.label_4 = QtGui.QLabel(self.sizelimits)
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_2.addWidget(self.label_4)
        self.gridLayout_2.addWidget(self.sizelimits, 4, 0, 1, 2)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout.addWidget(self.scrollArea, 3, 0, 1, 2)
        self.select_font = QtGui.QPushButton(self.appearance_tab)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/icons/format-text-color.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.select_font.setIcon(icon3)
        self.select_font.setObjectName("select_font")
        self.gridLayout.addWidget(self.select_font, 0, 0, 1, 1)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/icons/icons/format-stroke-color.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        config_dialog.addTab(self.appearance_tab, icon4, "")

        self.retranslateUi(config_dialog)
        config_dialog.setCurrentIndex(1)
        QtCore.QObject.connect(self.use_sizelimit, QtCore.SIGNAL("toggled(bool)"), self.sizelimits.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(config_dialog)

    def retranslateUi(self, config_dialog):
        config_dialog.setWindowTitle(QtGui.QApplication.translate("config_dialog", "TabWidget", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("config_dialog", "Preferred Agent", None, QtGui.QApplication.UnicodeUTF8))
        config_dialog.setTabText(config_dialog.indexOf(self.general_tab), QtGui.QApplication.translate("config_dialog", "General", None, QtGui.QApplication.UnicodeUTF8))
        self.account_add.setText(QtGui.QApplication.translate("config_dialog", "Add", None, QtGui.QApplication.UnicodeUTF8))
        self.account_del.setText(QtGui.QApplication.translate("config_dialog", "Remove", None, QtGui.QApplication.UnicodeUTF8))
        self.account_edit.setText(QtGui.QApplication.translate("config_dialog", "Edit...", None, QtGui.QApplication.UnicodeUTF8))
        config_dialog.setTabText(config_dialog.indexOf(self.accounts_tab), QtGui.QApplication.translate("config_dialog", "Accounts", None, QtGui.QApplication.UnicodeUTF8))
        self.sample_text.setPlainText(QtGui.QApplication.translate("config_dialog", "The quick brown fox jumps over the lazy dog", None, QtGui.QApplication.UnicodeUTF8))
        self.select_color.setText(QtGui.QApplication.translate("config_dialog", "Color..", None, QtGui.QApplication.UnicodeUTF8))
        self.html_relsize.setText(QtGui.QApplication.translate("config_dialog", "Use Relative HTML Sizes", None, QtGui.QApplication.UnicodeUTF8))
        self.show_joinpart.setText(QtGui.QApplication.translate("config_dialog", "Show User Join/Leave Messages", None, QtGui.QApplication.UnicodeUTF8))
        self.use_sizelimit.setText(QtGui.QApplication.translate("config_dialog", "Limit minimum/maximum size:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("config_dialog", "From", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("config_dialog", "To", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("config_dialog", "pt", None, QtGui.QApplication.UnicodeUTF8))
        self.select_font.setText(QtGui.QApplication.translate("config_dialog", "Font..", None, QtGui.QApplication.UnicodeUTF8))
        config_dialog.setTabText(config_dialog.indexOf(self.appearance_tab), QtGui.QApplication.translate("config_dialog", "Appearance", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    config_dialog = QtGui.QTabWidget()
    ui = Ui_config_dialog()
    ui.setupUi(config_dialog)
    config_dialog.show()
    sys.exit(app.exec_())

