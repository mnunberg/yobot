# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'buddy_entry.ui'
#
# Created: Wed Aug 18 23:10:36 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_be(object):
    def setupUi(self, be):
        be.setObjectName("be")
        be.resize(245, 31)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(be.sizePolicy().hasHeightForWidth())
        be.setSizePolicy(sizePolicy)
        self.gridLayout = QtGui.QGridLayout(be)
        self.gridLayout.setMargin(0)
        self.gridLayout.setHorizontalSpacing(3)
        self.gridLayout.setVerticalSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.protostatus = QtGui.QLabel(be)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.protostatus.sizePolicy().hasHeightForWidth())
        self.protostatus.setSizePolicy(sizePolicy)
        self.protostatus.setMinimumSize(QtCore.QSize(24, 24))
        self.protostatus.setText("")
        self.protostatus.setObjectName("protostatus")
        self.gridLayout.addWidget(self.protostatus, 0, 0, 3, 1)
        self.status = QtGui.QLabel(be)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.status.setFont(font)
        self.status.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.status.setObjectName("status")
        self.gridLayout.addWidget(self.status, 2, 1, 1, 1)
        self.buddyicon = QtGui.QLabel(be)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buddyicon.sizePolicy().hasHeightForWidth())
        self.buddyicon.setSizePolicy(sizePolicy)
        self.buddyicon.setMinimumSize(QtCore.QSize(24, 24))
        self.buddyicon.setText("")
        self.buddyicon.setObjectName("buddyicon")
        self.gridLayout.addWidget(self.buddyicon, 0, 2, 3, 1)
        self.name = QtGui.QLabel(be)
        font = QtGui.QFont()
        font.setWeight(50)
        font.setBold(False)
        self.name.setFont(font)
        self.name.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.name.setObjectName("name")
        self.gridLayout.addWidget(self.name, 1, 1, 1, 1)

        self.retranslateUi(be)
        QtCore.QMetaObject.connectSlotsByName(be)

    def retranslateUi(self, be):
        be.setWindowTitle(QtGui.QApplication.translate("be", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.status.setText(QtGui.QApplication.translate("be", "status message", None, QtGui.QApplication.UnicodeUTF8))
        self.name.setText(QtGui.QApplication.translate("be", "Buddy Name", None, QtGui.QApplication.UnicodeUTF8))

