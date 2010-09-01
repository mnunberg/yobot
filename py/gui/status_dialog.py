# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'status_dialog.ui'
#
# Created: Wed Sep  1 01:19:07 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_status_dialog(object):
    def setupUi(self, status_dialog):
        status_dialog.setObjectName("status_dialog")
        status_dialog.resize(313, 116)
        self.gridLayout = QtGui.QGridLayout(status_dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.status_list = QtGui.QComboBox(status_dialog)
        self.status_list.setObjectName("status_list")
        self.gridLayout.addWidget(self.status_list, 1, 1, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(status_dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 4, 0, 1, 2)
        self.label = QtGui.QLabel(status_dialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.message = QtGui.QLineEdit(status_dialog)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.message.setFont(font)
        self.message.setText("")
        self.message.setObjectName("message")
        self.gridLayout.addWidget(self.message, 2, 1, 1, 1)

        self.retranslateUi(status_dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), status_dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), status_dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(status_dialog)

    def retranslateUi(self, status_dialog):
        status_dialog.setWindowTitle(QtGui.QApplication.translate("status_dialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("status_dialog", "Status", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    status_dialog = QtGui.QDialog()
    ui = Ui_status_dialog()
    ui.setupUi(status_dialog)
    status_dialog.show()
    sys.exit(app.exec_())

