#!/usr/bin/env python
#for py2exe to work properly:
from lxml import _elementpath as _dummy

import yobot_plugins
from twisted.internet import reactor
from yobotclass import YobotAccount, YobotMessage
from yobotnet import YobotClientService
import yobotproto
from client_support import ModelBase, YCAccount
from debuglog import log_debug, log_err, log_warn, log_crit, log_info
import yobot_interfaces
from triviabot import triviabot
from collections import defaultdict
import debuglog
import sys
ID_COUNTER=1

class UIClient(object):
    """These define a bunch of hooks for the server"""
    yobot_interfaces.implements(yobot_interfaces.IClientOperations)
    def __init__(self, username=None, password=None, improto=None):
        """Set the service"""
        self.svc = YobotClientService(self, reactor)
        self.plugins = set()
        self.joined_rooms = defaultdict(lambda: [])
        yobot_interfaces.component_registry.register_component("client-operations", self)
        yobot_interfaces.component_registry.register_component("joined-rooms", self.joined_rooms)
        
    def registerPlugin(self, plugin_object):
        assert yobot_interfaces.IYobotUIPlugin.providedBy(plugin_object)
        self.plugins.add(plugin_object)
    
    def _plugin_hook_invoke(self, hook_name, hook_args):
        for p in self.plugins:
            getattr(p, hook_name)(*hook_args)
    def run(self):
        #self.uihooks = YobotGui(self, self.svc.accounts)
        #self.trivia = triviabot.TriviaGui()
        for p in yobot_interfaces.component_registry.get_active_plugins():
            self.registerPlugin(p())
        reactor.connectTCP("localhost", 7770, self.svc.getYobotClientFactory())
        #self.registerPlugin(self.uihooks)
        reactor.run()
    def clientRegistered(self):
        log_info( "REGISTERED")
        log_info( "trying to register account...")
        self.test_acct()
    
    def test_acct(self):
        return
        log_info("creating new test account")
        new_account = YCAccount(self.svc, "meh@10.0.0.99/", "1", yobotproto.YOBOT_JABBER)
#            proxy_host="localhost", proxy_port="3128", proxy_type="http")
        new_account.connect()
    def gotmsg(self, acct, msg):
        self._plugin_hook_invoke("gotMessage", (acct, msg))
    
    def chatUserJoined(self, acct, room, user):
        self._plugin_hook_invoke("chatUserJoined", (acct, room, user))
    
    def chatUserLeft(self, acct, room, user):
        self._plugin_hook_invoke("chatUserLeft", (acct, room, user))
    
    def roomJoined(self, acct, room):
        self.joined_rooms[acct].append(room)
        self._plugin_hook_invoke("roomJoined", (acct, room))
        log_info( "ROOM JOINED ", room)
        
    def gotRequest(self, request_obj):
        self._plugin_hook_invoke("gotRequest", (request_obj,))
    def delRequest(self, acct, refid):
        self._plugin_hook_invoke("delRequest", (acct, refid))
    
    def accountConnected(self, acct):
        log_info( "ACCOUNT CONNECTED", acct)
        self._plugin_hook_invoke("accountConnected", (acct,))
        
    def accountConnectionFailed(self, acct, txt):
        acct._logged_in = False
        log_err( "AUTHORIZATION FAILED!", txt, acct)
        self._plugin_hook_invoke("accountConnectionFailed", (acct, txt))

    def accountConnectionRemoved(self, acct):
        acct._logged_in = False
        self._plugin_hook_invoke("accountConnectionRemoved", (acct,))
        log_warn( "ACCOUNT REMOVED!")
        
    #####   GUI HOOKS    #####
    def connect(self, user, passw, improto, **proxy_params):
        user = str(user)
        passw = str(passw)
        new_account = YCAccount(self.svc, user, passw, improto, **proxy_params)
        new_account.connect()
    
    def uiClosed(self):
        #stop the reactor..
        reactor.stop()
    
    def disconnectAll(self, fromServer):
        if fromServer:
            self.svc.disconnectAll()
        else:
            reactor.stop()
    
    def callLater(cls, delay, fn, *args, **kwargs):
        ret = reactor.callLater(delay, fn, *args, **kwargs)
        return ret
    def cancelCallLater(cls, handle):
        handle.cancel()

def startup(args=sys.argv):
    import optparse
    options = optparse.OptionParser()
    options.add_option("-p", "--plugin", dest="selected_plugins", action="append", help="include this plugin")
    options.add_option("-U", "--username", dest="username", help="use this IM username")
    options.add_option("-P", "--password", dest="password", help="use this password")
    options.add_option("-I", "--improto", dest="improto", help="use this IM protocol [see documentation for a list]")
    options.add_option("-c", "--config", dest="config", help="configuration file")
    options.add_option("--use-proxy", dest="use_proxy", action="store_true", help="use env proxy settings", default=False)
    options, args = options.parse_args()
    
    if options.selected_plugins:
        #generate dict:
        name_object = {}
        for plugin in yobot_interfaces.component_registry.get_plugins():
            name_object[plugin.plugin_name] = plugin
        for p in options.selected_plugins:
            plugin_object = name_object.get(p)
            if not plugin_object:
                log_warn("couldn't find plugin", p)
                continue
            yobot_interfaces.component_registry.activate_plugin(plugin_object)
    
    debuglog.init("Client", title_color="green")
    yobotproto.yobot_proto_setlogger("Client")
    ui = UIClient()
    ui.run()

if __name__ == "__main__":
    startup()