# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main_auto.ui'
#
# Created: Fri Sep 17 20:49:29 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(274, 568)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.mainLayout = QtGui.QGridLayout(self.centralwidget)
        self.mainLayout.setContentsMargins(3, 0, 3, 0)
        self.mainLayout.setObjectName("mainLayout")
        spacerItem = QtGui.QSpacerItem(20, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Ignored)
        self.mainLayout.addItem(spacerItem, 0, 0, 1, 1)
        self.blist = QtGui.QTreeView(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(99)
        sizePolicy.setHeightForWidth(self.blist.sizePolicy().hasHeightForWidth())
        self.blist.setSizePolicy(sizePolicy)
        self.blist.setAutoScrollMargin(28)
        self.blist.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.blist.setIconSize(QtCore.QSize(28, 20))
        self.blist.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.blist.setIndentation(10)
        self.blist.setUniformRowHeights(False)
        self.blist.setHeaderHidden(True)
        self.blist.setObjectName("blist")
        self.mainLayout.addWidget(self.blist, 1, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 274, 29))
        self.menubar.setObjectName("menubar")
        self.menu = QtGui.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menuChat = QtGui.QMenu(self.menubar)
        self.menuChat.setObjectName("menuChat")
        self.menuSet_Status = QtGui.QMenu(self.menuChat)
        self.menuSet_Status.setObjectName("menuSet_Status")
        self.menuHelo = QtGui.QMenu(self.menubar)
        self.menuHelo.setObjectName("menuHelo")
        self.menuExtensions = QtGui.QMenu(self.menubar)
        self.menuExtensions.setObjectName("menuExtensions")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setMovable(True)
        self.toolBar.setIconSize(QtCore.QSize(16, 16))
        self.toolBar.setFloatable(False)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.ToolBarArea(QtCore.Qt.TopToolBarArea), self.toolBar)
        self.noticebox = QtGui.QDockWidget(MainWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.noticebox.sizePolicy().hasHeightForWidth())
        self.noticebox.setSizePolicy(sizePolicy)
        self.noticebox.setMaximumSize(QtCore.QSize(524287, 400))
        self.noticebox.setAutoFillBackground(False)
        self.noticebox.setFloating(False)
        self.noticebox.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
        self.noticebox.setObjectName("noticebox")
        self.notice_w = QtGui.QWidget()
        self.notice_w.setObjectName("notice_w")
        self.gridLayout_3 = QtGui.QGridLayout(self.notice_w)
        self.gridLayout_3.setMargin(0)
        self.gridLayout_3.setSpacing(0)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.notices = QtGui.QStackedWidget(self.notice_w)
        self.notices.setMinimumSize(QtCore.QSize(256, 0))
        self.notices.setFrameShadow(QtGui.QFrame.Plain)
        self.notices.setLineWidth(0)
        self.notices.setObjectName("notices")
        self.gridLayout_3.addWidget(self.notices, 0, 0, 1, 1)
        self.noticebox.setWidget(self.notice_w)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(8), self.noticebox)
        self.actionAbout = QtGui.QAction(MainWindow)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/help-about.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionAbout.setIcon(icon)
        self.actionAbout.setObjectName("actionAbout")
        self.actionSend_IM = QtGui.QAction(MainWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/icons/irc-voice.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSend_IM.setIcon(icon1)
        self.actionSend_IM.setObjectName("actionSend_IM")
        self.actionJoin_Room = QtGui.QAction(MainWindow)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/icons/irc-join-channel.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionJoin_Room.setIcon(icon2)
        self.actionJoin_Room.setObjectName("actionJoin_Room")
        self.actionQuit = QtGui.QAction(MainWindow)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/icons/application-exit.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionQuit.setIcon(icon3)
        self.actionQuit.setObjectName("actionQuit")
        self.actionNewconn = QtGui.QAction(MainWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/icons/icons/network-connect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionNewconn.setIcon(icon4)
        self.actionNewconn.setObjectName("actionNewconn")
        self.actionGo_Invisible = QtGui.QAction(MainWindow)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/icons/icons/user-invisible.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionGo_Invisible.setIcon(icon5)
        self.actionGo_Invisible.setObjectName("actionGo_Invisible")
        self.actionAddUser = QtGui.QAction(MainWindow)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/icons/icons/list-add-user.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionAddUser.setIcon(icon6)
        self.actionAddUser.setObjectName("actionAddUser")
        self.actionIgnoreUser = QtGui.QAction(MainWindow)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(":/icons/icons/im-ban-user.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionIgnoreUser.setIcon(icon7)
        self.actionIgnoreUser.setObjectName("actionIgnoreUser")
        self.actionAdd = QtGui.QAction(MainWindow)
        self.actionAdd.setObjectName("actionAdd")
        self.actionIgnore = QtGui.QAction(MainWindow)
        self.actionIgnore.setObjectName("actionIgnore")
        self.actionInvis = QtGui.QAction(MainWindow)
        self.actionInvis.setObjectName("actionInvis")
        self.actionDisconnect_All_Server = QtGui.QAction(MainWindow)
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap(":/icons/icons/format-disconnect-node.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionDisconnect_All_Server.setIcon(icon8)
        self.actionDisconnect_All_Server.setObjectName("actionDisconnect_All_Server")
        self.actionQuit_And_Disconnect_all_from_Server = QtGui.QAction(MainWindow)
        self.actionQuit_And_Disconnect_all_from_Server.setIcon(icon8)
        self.actionQuit_And_Disconnect_all_from_Server.setObjectName("actionQuit_And_Disconnect_all_from_Server")
        self.actionDisconnect_Account_Client = QtGui.QAction(MainWindow)
        self.actionDisconnect_Account_Client.setIcon(icon8)
        self.actionDisconnect_Account_Client.setObjectName("actionDisconnect_Account_Client")
        self.actionDisconnect_Account_Server = QtGui.QAction(MainWindow)
        self.actionDisconnect_Account_Server.setIcon(icon8)
        self.actionDisconnect_Account_Server.setObjectName("actionDisconnect_Account_Server")
        self.actionAppearHiddenToContact = QtGui.QAction(MainWindow)
        self.actionAppearHiddenToContact.setIcon(icon5)
        self.actionAppearHiddenToContact.setObjectName("actionAppearHiddenToContact")
        self.actionSendMessage = QtGui.QAction(MainWindow)
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap(":/icons/icons/message-new.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSendMessage.setIcon(icon9)
        self.actionSendMessage.setObjectName("actionSendMessage")
        self.actionDelete = QtGui.QAction(MainWindow)
        self.actionDelete.setIcon(icon7)
        self.actionDelete.setObjectName("actionDelete")
        self.actionStatusAway = QtGui.QAction(MainWindow)
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap(":/icons/icons/user-away.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionStatusAway.setIcon(icon10)
        self.actionStatusAway.setObjectName("actionStatusAway")
        self.actionStatusAvailable = QtGui.QAction(MainWindow)
        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap(":/icons/icons/user-online.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionStatusAvailable.setIcon(icon11)
        self.actionStatusAvailable.setObjectName("actionStatusAvailable")
        self.actionStatusInvisible = QtGui.QAction(MainWindow)
        self.actionStatusInvisible.setIcon(icon5)
        self.actionStatusInvisible.setObjectName("actionStatusInvisible")
        self.actionStatusBusy = QtGui.QAction(MainWindow)
        icon12 = QtGui.QIcon()
        icon12.addPixmap(QtGui.QPixmap(":/icons/icons/user-busy.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionStatusBusy.setIcon(icon12)
        self.actionStatusBusy.setObjectName("actionStatusBusy")
        self.actionStatusCustom = QtGui.QAction(MainWindow)
        icon13 = QtGui.QIcon()
        icon13.addPixmap(QtGui.QPixmap(":/icons/icons/extended-away.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionStatusCustom.setIcon(icon13)
        self.actionStatusCustom.setObjectName("actionStatusCustom")
        self.menu.addAction(self.actionNewconn)
        self.menu.addSeparator()
        self.menu.addAction(self.actionDisconnect_Account_Client)
        self.menu.addAction(self.actionDisconnect_Account_Server)
        self.menu.addAction(self.actionDisconnect_All_Server)
        self.menu.addAction(self.actionQuit_And_Disconnect_all_from_Server)
        self.menu.addAction(self.actionQuit)
        self.menuChat.addAction(self.actionSend_IM)
        self.menuChat.addAction(self.actionJoin_Room)
        self.menuChat.addSeparator()
        self.menuChat.addAction(self.actionGo_Invisible)
        self.menuChat.addAction(self.menuSet_Status.menuAction())
        self.menuHelo.addAction(self.actionAbout)
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menuChat.menuAction())
        self.menubar.addAction(self.menuExtensions.menuAction())
        self.menubar.addAction(self.menuHelo.menuAction())
        self.toolBar.addAction(self.actionNewconn)
        self.toolBar.addAction(self.actionGo_Invisible)
        self.toolBar.addAction(self.actionJoin_Room)
        self.toolBar.addAction(self.actionSend_IM)
        self.toolBar.addAction(self.actionAddUser)
        self.toolBar.addAction(self.actionIgnoreUser)

        self.retranslateUi(MainWindow)
        self.notices.setCurrentIndex(-1)
        QtCore.QObject.connect(self.actionQuit, QtCore.SIGNAL("activated()"), MainWindow.close)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Yobot", None, QtGui.QApplication.UnicodeUTF8))
        self.menu.setTitle(QtGui.QApplication.translate("MainWindow", "Client", None, QtGui.QApplication.UnicodeUTF8))
        self.menuChat.setTitle(QtGui.QApplication.translate("MainWindow", "Chat", None, QtGui.QApplication.UnicodeUTF8))
        self.menuSet_Status.setTitle(QtGui.QApplication.translate("MainWindow", "Set Status", None, QtGui.QApplication.UnicodeUTF8))
        self.menuHelo.setTitle(QtGui.QApplication.translate("MainWindow", "Help", None, QtGui.QApplication.UnicodeUTF8))
        self.menuExtensions.setTitle(QtGui.QApplication.translate("MainWindow", "Extensions", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Actions", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAbout.setText(QtGui.QApplication.translate("MainWindow", "About", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSend_IM.setText(QtGui.QApplication.translate("MainWindow", "Send IM", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSend_IM.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+M", None, QtGui.QApplication.UnicodeUTF8))
        self.actionJoin_Room.setText(QtGui.QApplication.translate("MainWindow", "Join Room", None, QtGui.QApplication.UnicodeUTF8))
        self.actionJoin_Room.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+J", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setText(QtGui.QApplication.translate("MainWindow", "Quit (And Disconnect All From Client)", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+Q", None, QtGui.QApplication.UnicodeUTF8))
        self.actionNewconn.setText(QtGui.QApplication.translate("MainWindow", "New Connection", None, QtGui.QApplication.UnicodeUTF8))
        self.actionNewconn.setToolTip(QtGui.QApplication.translate("MainWindow", "Add a New Connection", None, QtGui.QApplication.UnicodeUTF8))
        self.actionNewconn.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+N", None, QtGui.QApplication.UnicodeUTF8))
        self.actionGo_Invisible.setText(QtGui.QApplication.translate("MainWindow", "Go Invisible", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAddUser.setText(QtGui.QApplication.translate("MainWindow", "Add", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAddUser.setToolTip(QtGui.QApplication.translate("MainWindow", "Add a user to your buddy list", None, QtGui.QApplication.UnicodeUTF8))
        self.actionIgnoreUser.setText(QtGui.QApplication.translate("MainWindow", "Ignore", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAdd.setText(QtGui.QApplication.translate("MainWindow", "Add", None, QtGui.QApplication.UnicodeUTF8))
        self.actionIgnore.setText(QtGui.QApplication.translate("MainWindow", "Ignore", None, QtGui.QApplication.UnicodeUTF8))
        self.actionInvis.setText(QtGui.QApplication.translate("MainWindow", "Invis", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDisconnect_All_Server.setText(QtGui.QApplication.translate("MainWindow", "Disconnect All (Server)", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDisconnect_All_Server.setToolTip(QtGui.QApplication.translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Lucida Grande\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Disconnect <span style=\" font-style:italic;\">all</span> accounts from protocol server. <span style=\" color:#aa0000;\">This account will be unavailable to all connected clients</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit_And_Disconnect_all_from_Server.setText(QtGui.QApplication.translate("MainWindow", "Quit (And Disconnect All From Server)", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDisconnect_Account_Client.setText(QtGui.QApplication.translate("MainWindow", "Disconnect Account (Client)", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDisconnect_Account_Server.setText(QtGui.QApplication.translate("MainWindow", "Disconnect Account (Server)", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAppearHiddenToContact.setText(QtGui.QApplication.translate("MainWindow", "Appear Invisible To Contact", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSendMessage.setText(QtGui.QApplication.translate("MainWindow", "Send Message", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDelete.setText(QtGui.QApplication.translate("MainWindow", "Delete", None, QtGui.QApplication.UnicodeUTF8))
        self.actionStatusAway.setText(QtGui.QApplication.translate("MainWindow", "Away", None, QtGui.QApplication.UnicodeUTF8))
        self.actionStatusAvailable.setText(QtGui.QApplication.translate("MainWindow", "Available", None, QtGui.QApplication.UnicodeUTF8))
        self.actionStatusInvisible.setText(QtGui.QApplication.translate("MainWindow", "Invisible", None, QtGui.QApplication.UnicodeUTF8))
        self.actionStatusBusy.setText(QtGui.QApplication.translate("MainWindow", "Busy", None, QtGui.QApplication.UnicodeUTF8))
        self.actionStatusCustom.setText(QtGui.QApplication.translate("MainWindow", "Custom..", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

