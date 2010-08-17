#!/usr/bin/env python

import yobotproto
import yobotops
import yobotclass
import collections
import sys


def account_connected(pyevt, acctlist):
    acctlist[pyevt.objid].connected = True

def account_added(pyevt,acctlist):
    acctlist[pyevt.objid].registered = True

def account_disconnected(pyevt, acctlist):
    acctlist[pyevt.objid].connected = False

def room_joined(pyevt,acctlist):
    acctlist[pyevt.objid].chats.add(pyevt.txt)

def room_left(pyevt,acctlist):
    acctlist[pyevt.objid].chats.remove(pyevt.txt)
    
eventhandlers = collections.defaultdict(lambda: lambda x,y: None)
eventhandlers.update({
    yobotproto.YOBOT_EVENT_ACCT_REGISTERED: account_added,
    yobotproto.YOBOT_EVENT_CONNECTED: account_connected,
    yobotproto.YOBOT_EVENT_DISCONNECTED: account_disconnected,
    yobotproto.YOBOT_EVENT_ROOM_JOINED: room_joined,
    yobotproto.YOBOT_EVENT_ROOM_LEFT: room_left
}
)