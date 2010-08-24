#!/usr/bin/env python
import sys
from PyQt4 import QtGui
app = QtGui.QApplication(sys.argv)
from gui.contrib import qt4reactor
qt4reactor.install()
from twisted.internet import reactor
from yobotclass import YobotAccount, YobotMessage
from yobotnet import YobotClientService
import yobotproto
from time import time
from datetime import datetime
from client_support import ModelBase, YCAccount
import debuglog
from debuglog import log_debug, log_err, log_warn, log_crit, log_info

ID_COUNTER=1

class UIClient(object):
    """These define a bunch of hooks for the server"""
    def __init__(self):
        """Set the service"""
        self.svc = YobotClientService(self, reactor)

    def run(self):
        from gui.qyobot import YobotGui
        self.uihooks = YobotGui(self)
        self.uihooks.init_backend(self.svc.accounts)
        self.uihooks.gui_init()
        self.uihooks.mw.show()
        reactor.connectTCP("localhost", 7770, self.svc.getYobotClientFactory())
        reactor.run()
    def clientRegistered(self):
        log_info( "REGISTERED")
        log_info( "trying to register account...")
        self.test_acct()
    
    def test_acct(self, ):
        log_info("creating new test account")
        new_account = YCAccount(self.svc, "meh@10.0.0.99/", "1", yobotproto.YOBOT_JABBER)
        new_account.connect()
    def gotmsg(self, acct, msg):
        self.uihooks.gotMessage(acct, msg)
    
    def chatUserJoined(self, acct, room, user):
        self.uihooks.chatUserJoined(acct, room, user)
    
    def chatUserLeft(self, acct, room, user):
        self.uihooks.chatUserLeft(acct, room, user)
    
    def roomJoined(self, acct, room):
        log_info( "ROOM JOINED ", room)
        #fetch the users...
        acct.fetchRoomUsers(room)
    
    def gotRequest(self, request_obj):
        self.uihooks.gotRequest(request_obj)
    
    def accountConnected(self, acct):
        log_info( "ACCOUNT CONNECTED", acct)
        acct.fetchBuddies()
        self.uihooks.accountConnected(acct)
        
    def accountConnectionFailed(self, acct):
        acct._logged_in = False
        log_err( "AUTHORIZATION FAILED!", acct)
    def accountConnectionRemoved(self, acct):
        acct._logged_in = False
        log_warn( "ACCOUNT REMOVED!")
        
    #####   GUI HOOKS    #####
    def connect(self, user, passw, improto):
        user = str(user)
        passw = str(passw)
        new_account = YCAccount(self.svc, user, passw, improto)
        new_account.connect()

if __name__ == "__main__":
    debuglog.init("Client", title_color="green")
    yobotproto.yobot_proto_setlogger("Client")
    ui = UIClient()
    ui.run()