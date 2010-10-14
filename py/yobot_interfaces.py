#!/usr/bin/env python
from zope.interface import (Attribute, Interface, implements, implementedBy,
                            directlyProvides)

from debuglog import log_debug, log_info, log_err, log_crit, log_warn

class IYobotUIPlugin(Interface):
    """Interface a UI plugin must implement"""
    plugin_name = Attribute("plugin_name", "identifier for plugin")
    def accountConnected(account_object):
        "when an account is connected"
    def connectProgress(account_object, message):
        "Called when an account is connecting..."
    def accountConnectionFailed(account_object, error_message):
        "when a connection has failed"
    def accountConnectionRemove(account_object):
        "called when an account is removed from the backend"
    def gotMessage(account_object, message_object):
        """Hook when a message (chat or IM) is received)"""
    def roomJoined(account_object, room_name):
        "When a room is joined"
    def roomLeft(account_object, room_name):
        "When an account leaves a room"
    def chatUserJoined(account_object, room_name, user_name):
        "When a user joins a room"
    def chatUserLeft(account_object, room_name, user_name):
        "When a user leaves a room"
        
class IClientRequests(Interface):
    """These are for the few request that must originate from a client object
    (most have a specific account related and are thus requested using the account
    object directly)"""
    def connect(user_name, password, protocol_constant,
                proxy_host = None, proxy_port = None, proxy_type = None,
                proxy_username = None, proxy_password = None):
        """This will create a new account object and attempt to connect it.
        the proxy options are all strings"""
    def disconnectAll(fromServerBoolean):
        """This will disconnect all accounts currently registered,
        if fromServer is True, then a disconnection request will be forwarded to
        the main relay so that the account is entirely relinquished from the control
        of the YoBot infrastructure"""
    def registerPlugin(plugin_object):
        """Register a plugin which provides IYobotUIPlugin"""
    def unregisterPlugin(plugin_object):
        """Unregister a plugin"""
        
class IMVCNode(Interface):
    """Attributes for Qt's MVC architcture subclasses"""
    def parent():
        "returns the parent node"
    def childCount():
        "returns the amount of children this node has"
    status = Attribute("status", "status code")
    status_message = Attribute("status_message", "optional text explaining the status")
    icon = Attribute("icon", "icon data")
        
class IMVCTree(Interface):
    def __iter__():
        "must be iterable"
    def __len__():
        "must be countable"
    def __getitem__():
        "must be indexable"
    def beginAdd(index):
        "call when something is about to be added to index"
    def endAdd():
        "insertion done"
    def beginRemove(index):
        "call when about to remove item from index"
    def endRemove():
        "removal done"

class IClientAccountStore(IMVCTree):
    """Wrapper class for global client account store"""
    
class IAccountCommon(Interface):
    id = Attribute("the account ID")
    name = Attribute("the account name")
    improto = Attribute("the protocol constant")

class IClientAccount(IAccountCommon):
    blist = Attribute("this is a buddy list")

class IAccountOperations(IClientAccount):
    """This is provided by an account object..."""
    def addUser(user_name):
        "add a buddy to the server buddy list"
    def delUser(user_name):
        "delete a buddy from the server buddy list"
    def getBacklog(conversation_name, message_count):
        "retrieve a log of messages"
    def joinchat(room_name):
        "join a chatroom"
    def leaveRoom(room_name):
        "leave a chatroom"
    def connect():
        "connect this acount"
    def disconnect():
        "disconnect this account"
    def fetchBuddies(self):
        "fetch the buddy list from the server"
    def sendmsg(to_conversation_name, message_text, destination_is_chat=False):
        "send a message to a conversion"
    def getOfflines():
        "fetch offline messages received since the last client disconnected"
    def statusChange(status_constant, status_message):
        "request to change the server-side status"
        
class IAccountHooks(IClientAccount):
    def gotBuddyStatus(buddy_name, status_constant, message=None):
        "called when a buddy on this account's blist"
    def gotBuddyIcon(buddy_name, binary_icon_data):
        "called when a buddy icon changes"

class IClientBackend(Interface):
    accounts = Attribute("accounts", "Global account store")
    reactor = Attribute("reactor", "The reactor")

class IClientOperations(Interface):
    """Requests sent to the server"""
    def addAcct(account_object):
        "adds an account to the store"
    def delAcct(account_object):
        "deletes an account from the store and disconnects it"
    def addreqAuthorize(account_object, contact_name):
        """Approve contact_name's request to add you to his/her list"""
    def addreqDeny(account_object, contact_name):
        """deny an add request"""
    def sendMsg(account_object, message_object):
        """send a message"""
    def joinRoom(account_object, room_name):
        """join a room"""
    def leaveRoom(account_object, room_name):
        """Leave a room"""
    def addUser(account_object, user_name):
        """request user_name for permission to add him/her to your list"""
    def delUser(account_object, user_name):
        """remove user_name from your buddy list"""
    def ignoreUser(account_object, user_name):
        """ignore messages from user_name"""
    def fetchBuddies(account_object):
        """fetch buddies for account from server list"""
    def fetchBuddyIcons(account_object):
        """get buddy icons for your buddies"""
    def getOfflines(account_object):
        """fetch offline messages"""
    def getBacklog(account_object, contact_name, message_count):
        """get log of conversations between account_object and contact_name"""
    def statusChange(account_object, status_constant, status_message):
        """change your status"""
    def disconnectAccount(account_object, fromServer=False):
        """disconnect account.. see the documentation for disconnectAll on IClientRequests"""
    def disconnectAll():
        """see documentation """
    
    def callLater(delay, fn, *args, **kwargs):
        "delayed callback. returns handle"
    def cancelCallLater(handle):
        "cancels a delayed callback"

class ComponentRegistry(object):
    def __init__(self):
        self._objects = {}
        self._plugins = set()
        self._active_plugins = set()
        self.known_ids = ("gui-main", "account-store", "account-model", "client-svc",
                          "client-operations", "joined-rooms", "reactor",
                          "client-config", "yobot-config-dir")
    def register_component(self, id, object):
        if not id in self.known_ids:
            raise Exception("unknown component", id)
        elif id in self._objects.keys():
            raise Exception("this object exists already")
        else:
            self._objects[id] = object
    def get_component(self, id):
        return self._objects.get(id, None)
    def register_plugin(self, plugin_object):
        if not plugin_object in self._plugins:
            self._plugins.add(plugin_object)
    def unregister_plugin(self, plugin_object):
        if plugin_object in self._plugins:
            self._plugins.remove(plugin_object)
    def activate_plugin(self, plugin_object):
        self._active_plugins.add(plugin_object)
    def unactivate_plugin(self, plugin_object):
        if plugin_object in self._active_plugins:
            self._active_plugins.remove(plugin_object)
    def get_plugins(self):
        return self._plugins
    def get_active_plugins(self):
        return tuple(self._active_plugins)

component_registry = ComponentRegistry()
global_states = {}

def get_yobot_homedir():
    """Simple utility function. Order is: (1) the "yobot-config-dir" plugin,
    (2) the YOBOT_USER_DIR environment variable, (3) $HOME/.yobot"""
    from os import environ
    from os.path import expanduser, join
    
    #see if we've been passed an option on the command line:
    e = component_registry.get_component("yobot-config-dir")
    if e: return e
    
    e = environ.get("YOBOT_USER_DIR")
    if e: return e
    
    return join(expanduser("~"), ".yobot")
    