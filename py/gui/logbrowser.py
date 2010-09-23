# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'logbrowser.ui'
#
# Created: Fri Sep 17 20:49:29 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_logbrowser(object):
    def setupUi(self, logbrowser):
        logbrowser.setObjectName("logbrowser")
        logbrowser.resize(619, 537)
        self.gridLayout = QtGui.QGridLayout(logbrowser)
        self.gridLayout.setMargin(0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter = QtGui.QSplitter(logbrowser)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setHandleWidth(4)
        self.splitter.setObjectName("splitter")
        self.userlist = QtGui.QListWidget(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.userlist.sizePolicy().hasHeightForWidth())
        self.userlist.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setWeight(75)
        font.setBold(True)
        self.userlist.setFont(font)
        self.userlist.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.userlist.setSpacing(1)
        self.userlist.setObjectName("userlist")
        QtGui.QListWidgetItem(self.userlist)
        self.convtext = QtGui.QTextBrowser(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.convtext.sizePolicy().hasHeightForWidth())
        self.convtext.setSizePolicy(sizePolicy)
        self.convtext.setObjectName("convtext")
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)
        self.actionClose = QtGui.QAction(logbrowser)
        self.actionClose.setObjectName("actionClose")

        self.retranslateUi(logbrowser)
        QtCore.QObject.connect(self.actionClose, QtCore.SIGNAL("activated()"), logbrowser.close)
        QtCore.QMetaObject.connectSlotsByName(logbrowser)

    def retranslateUi(self, logbrowser):
        logbrowser.setWindowTitle(QtGui.QApplication.translate("logbrowser", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.userlist.setSortingEnabled(True)
        __sortingEnabled = self.userlist.isSortingEnabled()
        self.userlist.setSortingEnabled(False)
        self.userlist.item(0).setText(QtGui.QApplication.translate("logbrowser", "realllllllllllllllllllllllllllllllll", None, QtGui.QApplication.UnicodeUTF8))
        self.userlist.setSortingEnabled(__sortingEnabled)
        self.actionClose.setText(QtGui.QApplication.translate("logbrowser", "Close", None, QtGui.QApplication.UnicodeUTF8))
        self.actionClose.setShortcut(QtGui.QApplication.translate("logbrowser", "Ctrl+W", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    logbrowser = QtGui.QWidget()
    ui = Ui_logbrowser()
    ui.setupUi(logbrowser)
    logbrowser.show()
    sys.exit(app.exec_())

