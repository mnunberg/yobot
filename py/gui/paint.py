#!/usr/bin/env python

from PyQt4 import QtCore, QtGui
import sys

app = QtGui.QApplication(sys.argv)
window = QtGui.QMainWindow()

cw = QtGui.QWidget()
window.setCentralWidget(cw)
layout = QtGui.QVBoxLayout(cw)

label1 = QtGui.QLabel()
#label1.setText("label1")
layout.addWidget(label1)

label2 = QtGui.QLabel()
label2.setText("label2")
layout.addWidget(label2)

label3 = QtGui.QLabel()
label3.setText("label3")
layout.addWidget(label3)

status_pixmap = QtGui.QPixmap("./icons/user-online.png")
proto_pixmap = QtGui.QPixmap("./icons/yahoo.png")

#combined_pixmap = QtGui.QPixmap(16, 16)
combined_pixmap = QtGui.QImage(28,28, QtGui.QImage.Format_ARGB32_Premultiplied)

painter = QtGui.QPainter(combined_pixmap)

painter.setCompositionMode(painter.CompositionMode_Source)
painter.fillRect(combined_pixmap.rect(), QtCore.Qt.transparent)

painter.setCompositionMode(painter.CompositionMode_Source)
painter.drawPixmap(QtCore.QPoint(0,0), status_pixmap)

painter.setCompositionMode(painter.CompositionMode_SourceOver)
painter.drawPixmap(QtCore.QPoint(4,4), proto_pixmap)

#painter.setCompositionMode(painter.CompositionMode_DestinationOver)
#painter.fillRect(combined_pixmap.rect(), QtCore.Qt.transparent)
painter.end()

label1.setPixmap(QtGui.QPixmap.fromImage(combined_pixmap))
label2.setPixmap(status_pixmap)
label3.setPixmap(proto_pixmap)
window.show()
app.exec_()