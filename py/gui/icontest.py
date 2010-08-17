#!/usr/bin/env python
from PyQt4 import QtGui, QtCore
import sys

app = QtGui.QApplication(sys.argv)
button = QtGui.QPushButton()
button.setIcon(QtGui.QIcon.fromTheme("format-text-bold",QtGui.QIcon("./icons/format-text-bold.png")))
button.show()

app.exec_()

