#!/usr/bin/env python
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys
#import notification2 as notification
import notification

def setExpanding(obj):
    obj.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

app = QApplication(sys.argv)
mw = QMainWindow()
widget = QFrame(mw)
widget.setLayout(QHBoxLayout())
stackedwidget = QStackedWidget(widget)
widget.layout().setSizeConstraint(QLayout.SetMinimumSize)
widget.layout().addWidget(stackedwidget)



notice_widget = QWidget()
notice_ui = notification.Ui_Form()
notice_ui.setupUi(notice_widget)
stackedwidget.addWidget(notice_widget)

_shadow = QGraphicsDropShadowEffect(notice_ui.message)
mw.show()
app.exec_()
