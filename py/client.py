#!/usr/bin/env python
#for py2exe to work properly:
from lxml import _elementpath as _dummy
import yobot_plugins
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from yobotclass import YobotAccount, YobotMessage
from yobotnet import YobotClientService
import yobotproto
from client_support import ModelBase, YCAccount
from debuglog import log_debug, log_err, log_warn, log_crit, log_info
import yobot_interfaces
from collections import defaultdict
import debuglog
import sys

class YobotClientFactory(ClientFactory):
    def startedConnecting(self, connector):
        #super(type(self),self).startedConnecting(connector)
        log_debug("")
    def clientConnectionFailed(self, connector, reason):
        #super(type(self),self).connectionFailed(connector, reason)
        log_debug("")
    def clientConnectionLost(self, connector,reason):
        #super(type(self),self).clientConnectionLost(connector, reason)
        log_debug("")

class UIClient(object):
    """These define a bunch of hooks for the server"""
    yobot_interfaces.implements(yobot_interfaces.IClientOperations)
    def __init__(self, username=None, password=None, improto=None):
        """Set the service"""
        #set up the client configuration:
        self.config = yobot_interfaces.component_registry.get_component("client-config")
        if not self.config:
            import client_config
            import os.path
            self.config = client_config.ClientConfig(
                os.path.join(yobot_interfaces.get_yobot_homedir(),"client.conf"),autocreate=True)
            yobot_interfaces.component_registry.register_component("client-config", self.config)
        self.config.save()
        self.svc = YobotClientService(self, reactor)
        self.plugins = set()
        self.joined_rooms = defaultdict(lambda: [])
        yobot_interfaces.component_registry.register_component("client-operations", self)
        yobot_interfaces.component_registry.register_component("joined-rooms", self.joined_rooms)
        self.connector = None
    def registerPlugin(self, plugin_object):
        assert yobot_interfaces.IYobotUIPlugin.providedBy(plugin_object)
        self.plugins.add(plugin_object)
    
    def _plugin_hook_invoke(self, hook_name, hook_args):
        for p in self.plugins:
            try:
                getattr(p, hook_name)(*hook_args)
            except AttributeError, e:
                #first make sure that the actual exception comes from not having
                #the plugin implementing the hook, and not e.g. bad arguments or some
                #other error
                if not getattr(p, hook_name, None):
                    log_err("Object %r has not implemented %s" % (p, hook_name))
                else:
                    raise
    def run(self, address, port):
        for p in yobot_interfaces.component_registry.get_active_plugins():
            self.registerPlugin(p())
        self.connectToAgent(address, port)
        reactor.run()
    def clientRegistered(self):
        log_info("REGISTERED")        
        self.autoconnect()
    
    def autoconnect(self):
        log_info("autoconnecting..")
        #auto-connect all accounts in our config..
        if self.config and self.config.do_autoconnect:
            config = self.config
            for a in config.accounts:
                log_debug("found account: %s/%s" % (a["name"], a["improto"]))
                if not a.get("autoconnect", False):
                    continue
                #create positional arguments:
                user, password, improto = a.get("name"), a.get("password"), a.get("improto")
                if not (user and password and improto):
                    continue
                improto = getattr(yobotproto, improto, -1)
                if improto == -1:
                    continue
                args = (user, password, improto)
                kwargs = {}
                if a.get("use_proxy", False):
                    while True:
                        if not (a.get("proxy_address") and a.get("proxy_type")):
                            break
                        kwargs["proxy_host"] = a["proxy_address"]
                        kwargs["proxy_type"] = a["proxy_type"].lower()
                        kwargs["proxy_port"] = int(a["proxy_port"]) if a["proxy_port"] else None
                        kwargs["proxy_username"] = a.get("proxy_username", None)
                        kwargs["proxy_password"] = a.get("proxy_password", None)
                        break
                self.connect(*args, **kwargs)

    
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
    def topicChanged(self, acct, room, topic):
        from gui import yahoo_captcha
        import re
        self._plugin_hook_invoke("topicChanged", (acct, room, topic))
        if acct.improto == yobotproto.YOBOT_YAHOO:
            m = re.search(r"http://\S*captcha\S*", topic, re.I)
            if m:
                url = m.group(0)
                prompter = yahoo_captcha.CaptchaPrompter()
                prompter.prompt(url)
            else:
                log_err("NO MATCH!!!")
        
    def roomJoined(self, acct, room):
        self.joined_rooms[acct].append(room)
        self._plugin_hook_invoke("roomJoined", (acct, room))
        log_info("ROOM JOINED:", room)
    def roomLeft(self, acct, room):
        try:
            self.joined_rooms[acct].remove(room)
        except Exception, e:
            log_err("couldn't remove room %s from room list for account %s: %s" %(
                room, str(acct), str(e)))
        self._plugin_hook_invoke("roomLeft", (acct, room))
    def gotRequest(self, request_obj):
        self._plugin_hook_invoke("gotRequest", (request_obj,))
    def delRequest(self, acct, refid):
        self._plugin_hook_invoke("delRequest", (acct, refid))
    
    def accountConnected(self, acct):
        log_info( "ACCOUNT CONNECTED", acct)
        self._plugin_hook_invoke("accountConnected", (acct,))
    def connectProgress(self, acct, msg):
        self._plugin_hook_invoke("connectProgress",(acct, msg))
    def accountConnectionFailed(self, acct, txt):
        acct._logged_in = False
        log_err( "AUTHORIZATION FAILED!", txt, acct)
        self._plugin_hook_invoke("accountConnectionFailed", (acct, txt))

    def accountConnectionRemoved(self, acct):
        acct._logged_in = False
        self._plugin_hook_invoke("accountConnectionRemoved", (acct,))
        log_warn( "ACCOUNT REMOVED!")
    
    #agent handlers:
    def _agentconn_failed(self, connector, reason):
        #remove all accounts first:
        self.disconnectAll(True) #arg doesn't matter
        self.svc.accounts.clear()
        
    #####   GUI HOOKS    #####
    def connectToAgent(self, address=None, port=None, disconnect_from_server=True):
        try:
            self.disconnectAll(disconnect_from_server)
        except Exception, e:
            log_warn(e)
        if not address and not port:
            _address = self.config.globals.get("agent_address", "localhost:7770")
            log_err(_address)
            a = _address.rsplit(":")
            if len(a) >= 2:
                address = a[0]
                port = int(a[1])
            else:
                address = a[0]
                port = 7770
        elif address and not port:
            port = 7770
        
                
        log_debug("creating new factory")
        f = YobotClientFactory()
        self.svc.polishClientFactory(f)
        f.clientConnectionFailed = self._agentconn_failed
        f.clientConnectionLost = self._agentconn_failed
        log_debug("reactor.connect")
        if self.connector:
            log_debug("disconnecting current connector")
            self.connector.disconnect()
        self.connector = reactor.connectTCP(address, port, f)
    
    def connect(self, user, passw, improto, **proxy_params):
        user = str(user)
        passw = str(passw)
        new_account = YCAccount(self.svc, user, passw, improto, **proxy_params)
        new_account.connect()
    
    def uiClosed(self):
        #stop the reactor..
        log_err("")
        reactor.stop()
    
    def disconnectAll(self, fromServer):
        if fromServer:
            self.svc.disconnectAll()
        else:
            return
            log_err("reactor.stop")
            #reactor.stop()
    
    def callLater(cls, delay, fn, *args, **kwargs):
        ret = reactor.callLater(delay, fn, *args, **kwargs)
        return ret
    def cancelCallLater(cls, handle):
        handle.cancel()

def startup(args=sys.argv):
    import optparse
    options = optparse.OptionParser()
    options.add_option("-p", "--plugin", dest="selected_plugins", action="append",
                       help="include this plugin")
    options.add_option("-U", "--username", dest="username",
                       help="use this IM username")
    options.add_option("-P", "--password", dest="password",
                       help="use this password")
    options.add_option("-I", "--improto", dest="improto",
                       help="use this IM protocol [see documentation for a list]")
    options.add_option("-c", "--config-dir", dest="configdir",
                       help="client configuration directory",
                       default=yobot_interfaces.get_yobot_homedir())
    options.add_option("--use-proxy", dest="use_proxy", action="store_true",
                       help="use env proxy settings", default=False)
    options.add_option("--agent-address", dest="agent_addrinfo",
                       help="agent server:port")
    
    options, args = options.parse_args(args)
    
    #set our configuration directory
    yobot_interfaces.component_registry.register_component("yobot-config-dir", options.configdir)
    
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
    
    tmp = options.agent_addrinfo
    if tmp:
        tmp = tmp.rsplit(":", 1)
        address = tmp[0]
        if len(tmp) >= 2:
            port = int(tmp[1])
    else:
        #no address specified on the command line
        address, port = None, None
        
    debuglog.init("Client", title_color="green")
    yobotproto.yobot_proto_setlogger("Client")
    ui = UIClient()
    ui.run(address, port)

if __name__ == "__main__":
    startup()
