# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '_config_dialog.ui'
#
# Created: Tue Oct 12 23:10:03 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_config_dialog(object):
    def setupUi(self, config_dialog):
        config_dialog.setObjectName("config_dialog")
        config_dialog.resize(327, 282)
        config_dialog.setTabPosition(QtGui.QTabWidget.North)
        config_dialog.setTabShape(QtGui.QTabWidget.Rounded)
        config_dialog.setDocumentMode(True)
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
        config_dialog.addTab(self.general_tab, "")
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
        config_dialog.addTab(self.accounts_tab, "")
        self.appearance_tab = QtGui.QWidget()
        self.appearance_tab.setObjectName("appearance_tab")
        self.gridLayout = QtGui.QGridLayout(self.appearance_tab)
        self.gridLayout.setVerticalSpacing(12)
        self.gridLayout.setObjectName("gridLayout")
        self.select_font = QtGui.QPushButton(self.appearance_tab)
        self.select_font.setObjectName("select_font")
        self.gridLayout.addWidget(self.select_font, 0, 0, 1, 1)
        self.sample_text = QtGui.QPlainTextEdit(self.appearance_tab)
        self.sample_text.setObjectName("sample_text")
        self.gridLayout.addWidget(self.sample_text, 2, 0, 1, 2)
        self.select_color = QtGui.QPushButton(self.appearance_tab)
        self.select_color.setObjectName("select_color")
        self.gridLayout.addWidget(self.select_color, 0, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 5, 0, 1, 1)
        self.html_relsize = QtGui.QCheckBox(self.appearance_tab)
        self.html_relsize.setObjectName("html_relsize")
        self.gridLayout.addWidget(self.html_relsize, 3, 0, 1, 2)
        self.show_joinpart = QtGui.QCheckBox(self.appearance_tab)
        self.show_joinpart.setObjectName("show_joinpart")
        self.gridLayout.addWidget(self.show_joinpart, 4, 0, 1, 2)
        config_dialog.addTab(self.appearance_tab, "")

        self.retranslateUi(config_dialog)
        config_dialog.setCurrentIndex(2)
        QtCore.QMetaObject.connectSlotsByName(config_dialog)

    def retranslateUi(self, config_dialog):
        config_dialog.setWindowTitle(QtGui.QApplication.translate("config_dialog", "TabWidget", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("config_dialog", "Preferred Agent", None, QtGui.QApplication.UnicodeUTF8))
        config_dialog.setTabText(config_dialog.indexOf(self.general_tab), QtGui.QApplication.translate("config_dialog", "General", None, QtGui.QApplication.UnicodeUTF8))
        self.account_add.setText(QtGui.QApplication.translate("config_dialog", "Add", None, QtGui.QApplication.UnicodeUTF8))
        self.account_del.setText(QtGui.QApplication.translate("config_dialog", "Remove", None, QtGui.QApplication.UnicodeUTF8))
        self.account_edit.setText(QtGui.QApplication.translate("config_dialog", "Edit...", None, QtGui.QApplication.UnicodeUTF8))
        config_dialog.setTabText(config_dialog.indexOf(self.accounts_tab), QtGui.QApplication.translate("config_dialog", "Accounts", None, QtGui.QApplication.UnicodeUTF8))
        self.select_font.setText(QtGui.QApplication.translate("config_dialog", "Font..", None, QtGui.QApplication.UnicodeUTF8))
        self.sample_text.setPlainText(QtGui.QApplication.translate("config_dialog", "The quick brown fox jumps over the lazy dog", None, QtGui.QApplication.UnicodeUTF8))
        self.select_color.setText(QtGui.QApplication.translate("config_dialog", "Color..", None, QtGui.QApplication.UnicodeUTF8))
        self.html_relsize.setText(QtGui.QApplication.translate("config_dialog", "Use Relative HTML Sizes", None, QtGui.QApplication.UnicodeUTF8))
        self.show_joinpart.setText(QtGui.QApplication.translate("config_dialog", "Show User Join/Leave Messages", None, QtGui.QApplication.UnicodeUTF8))
        config_dialog.setTabText(config_dialog.indexOf(self.appearance_tab), QtGui.QApplication.translate("config_dialog", "Appearance", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    config_dialog = QtGui.QTabWidget()
    ui = Ui_config_dialog()
    ui.setupUi(config_dialog)
    config_dialog.show()
    sys.exit(app.exec_())

