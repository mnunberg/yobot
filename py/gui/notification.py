# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'notification.ui'
#
# Created: Mon Aug 23 19:33:00 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(243, 80)
        self.gridLayout = QtGui.QGridLayout(Form)
        self.gridLayout.setMargin(2)
        self.gridLayout.setObjectName("gridLayout")
        self.iconlabel = QtGui.QLabel(Form)
        self.iconlabel.setObjectName("iconlabel")
        self.gridLayout.addWidget(self.iconlabel, 0, 0, 1, 1)
        self.account = QtGui.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setWeight(75)
        font.setBold(True)
        self.account.setFont(font)
        self.account.setObjectName("account")
        self.gridLayout.addWidget(self.account, 0, 2, 1, 2)
        self.message = QtGui.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.message.setFont(font)
        self.message.setTextFormat(QtCore.Qt.LogText)
        self.message.setScaledContents(False)
        self.message.setWordWrap(True)
        self.message.setObjectName("message")
        self.gridLayout.addWidget(self.message, 1, 0, 2, 4)
        self.accept = QtGui.QPushButton(Form)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setWeight(75)
        font.setBold(True)
        self.accept.setFont(font)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/res/16x16/actions/dialog-ok-apply.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.accept.setIcon(icon)
        self.accept.setIconSize(QtCore.QSize(16, 16))
        self.accept.setObjectName("accept")
        self.gridLayout.addWidget(self.accept, 4, 3, 1, 1)
        self.discard = QtGui.QPushButton(Form)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setWeight(75)
        font.setBold(True)
        self.discard.setFont(font)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/res/16x16/actions/dialog-close.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.discard.setIcon(icon1)
        self.discard.setIconSize(QtCore.QSize(16, 16))
        self.discard.setObjectName("discard")
        self.gridLayout.addWidget(self.discard, 4, 2, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 14, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 3, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.iconlabel.setText(QtGui.QApplication.translate("Form", "<icon>", None, QtGui.QApplication.UnicodeUTF8))
        self.account.setText(QtGui.QApplication.translate("Form", "Account", None, QtGui.QApplication.UnicodeUTF8))
        self.message.setText(QtGui.QApplication.translate("Form", "some text here some more text", None, QtGui.QApplication.UnicodeUTF8))
        self.accept.setText(QtGui.QApplication.translate("Form", "Accept", None, QtGui.QApplication.UnicodeUTF8))
        self.discard.setText(QtGui.QApplication.translate("Form", "Cancel", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
