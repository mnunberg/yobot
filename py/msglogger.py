#!/usr/bin/python
CONV_TYPE_CHAT = 1<<0
CONV_TYPE_IM = 1<<1

from collections import defaultdict
import sqlite3
from yobotclass import YobotMessage
import yobotproto
from debuglog import log_warn, log_err, log_debug, log_crit, log_info
class MessageLogger(object):
    #for some reason this really DOES improve performance!
    _acctcache = {} #[account_name, proto_name] -> account_id_internal
    _convcache = defaultdict(lambda: {}) #[id_internal][user] -> convid
    
    def __init__(self, db=":memory:", usecache=True):
        """Initializes database"""
        self._conn = sqlite3.connect(db)
        conn = self._conn
        conn.row_factory = sqlite3.Row
        conn.text_factory = str
        self._cursor = conn.cursor()
        c = self._cursor
        self.usecache = usecache
        try:
            c.execute("SELECT * FROM conversations LIMIT 1")
            c.execute("SELECT * FROM messages LIMIT 1")
            c.execute("SELECT * FROM accounts LIMIT 1")
        except sqlite3.OperationalError:
            #type == chat or IM, from/to are self explanatory, except in chat,
            #to is the room name, and from is the user who has entered chat e.g. the account
            c.execute("""
                      CREATE TABLE accounts (
                        internal_id INTEGER PRIMARY KEY,
                        protocol_name TEXT NOT NULL,
                        account_name TEXT NOT NULL,
                        UNIQUE (account_name, protocol_name)
                        )
                      """)
            c.execute("""
                      CREATE TABLE conversations (
                        id INTEGER PRIMARY KEY, -- foreign key
                        type INTEGER NOT NULL, -- chat or IM
                        account_id_internal INTEGER,
                        other_user TEXT NOT NULL, -- who the account has conversed with, or the name of the chatroom
                        FOREIGN KEY(account_id_internal) REFERENCES accounts(internal_id)
                        UNIQUE (type, account_id_internal, other_user)
                      )
                      """)
            c.execute("""
                      CREATE TABLE messages (
                        conv_id INTEGER, -- foreign key for conversation table
                        body TEXT, -- message body
                        other_user TEXT, -- other user
                        who TEXT, -- whoever sent this message
                        timestamp REAL, -- timestamp
                        type INTEGER NOT NULL, -- type like in the conversations table
                        account_id_internal INTEGER NOT NULL,
                        FOREIGN KEY(conv_id) REFERENCES conversations(id), --
                        FOREIGN KEY(account_id_internal) REFERENCES accounts(internal_id),
                        UNIQUE (conv_id, body, who, timestamp) -- try to prevent duplicate messages
                      )
                      """
                      )    
    def _getConvId(self, account_id_internal, other_user):
        conv_id = None
        try:
            conv_id = self._convcache[account_id_internal][other_user]
        except KeyError:
            res = self._cursor.execute("""
                           SELECT id FROM conversations
                            WHERE account_id_internal =?
                            AND other_user =?
                           """, (account_id_internal, other_user)).fetchone()
            if res:
                conv_id = res["id"]
                self._convcache[account_id_internal][other_user] = conv_id
        return conv_id
    
    def _get_account_id_internal(self, account_name, protocol_name):
        id = self._acctcache.get((account_name, protocol_name))
        if not id:
            res = self._cursor.execute("""
                                       SELECT internal_id FROM accounts
                                        WHERE account_name=?
                                        AND protocol_name=?
                                       """, (account_name, protocol_name)).fetchone()
            if res:
                id = res["internal_id"]
                self._acctcache[(account_name, protocol_name)] = id
        return id
    
    def logMsg(self, type, account_name, protocol_name, other_user, body, who, timestamp):
        """Inserts a message into the database"""
        insert_fmt = ("""INSERT INTO messages (who, body, timestamp, conv_id, account_id_internal, type, other_user)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""")
        
        account_id_internal = self._get_account_id_internal(account_name, protocol_name)
        if not account_id_internal:
            self._cursor.execute("""
                                 INSERT INTO accounts (account_name, protocol_name)
                                 VALUES (?, ?)""", (account_name, protocol_name))
            account_id_internal = self._cursor.lastrowid
            
        conv_id = self._getConvId(account_id_internal, other_user)
        if not conv_id:
            self._cursor.execute("""
                               INSERT INTO conversations (type, account_id_internal, other_user)
                               VALUES (?, ?, ?)
                               """, (type, account_id_internal, other_user))
            conv_id = self._cursor.lastrowid            
        self._cursor.execute(insert_fmt, (who, body, timestamp, conv_id, account_id_internal, type, other_user))
    
    
    def getMsgs(self, account_name, protocol_name, other_user=None, timerange=None,type=None,count=50):
        """-> list of message, in order of time"""
        account_id_internal = self._get_account_id_internal(account_name, protocol_name)
        if not account_id_internal:
            return
        where_params = { "account_id_internal" : account_id_internal }
        if other_user:
            conv_id = self._getConvId(account_id_internal, other_user)
            if not conv_id:
                return
            where_params["conv_id"] = conv_id
        
        query_string = "SELECT timestamp, who, body, type, other_user FROM messages WHERE "
        value_l = []
        ands = []
        for k, v in where_params.items():
            ands.append(k + "=? ")
            value_l.append(v)
            
        query_string += " AND ".join(ands)
        
        if timerange:
            start, end = timerange
            query_string += " AND timestamp BETWEEN ? AND ? "
            value_l += [int(start), int(end)]
        
        query_string += "ORDER BY timestamp "
        if count:
            query_string += "LIMIT ? "
            value_l.append(count)
            
        log_warn(query_string, value_l)
        del ands
        for res in self._cursor.execute(query_string, value_l):
            msg = YobotMessage()
            msg.time = int(res["timestamp"])
            msg.name = res["other_user"]
            msg.who = res["who"]
            msg.txt = res["body"]
            type = res["type"]
            msg.yprotoflags |= yobotproto.YOBOT_MSG_TYPE_CHAT if type == CONV_TYPE_CHAT else yobotproto.YOBOT_MSG_TYPE_IM
            msg.prplmsgflags |= yobotproto.PURPLE_MESSAGE_SEND if msg.who == account_name else yobotproto.PURPLE_MESSAGE_RECV
            yield msg
        
    def dump(self):
        print "dumping accounts"
        for row in self._cursor.execute("select * from accounts"):
            print row
        print "dumping conversations"
        for row in self._cursor.execute("select * from conversations"):
            print row
        print "dumping messages"
        for row in self._cursor.execute("select * from messages"):
            print row
    def commit(self):
        self._conn.commit()
        
####testing####
if __name__ == "__main__":
    from time import time, sleep
    from os import urandom
    import string
    from random import choice
    import sys
    randstrings = []
    #get 50 random strings:
    for _ in xrange(1,50):
        randstrings.append(urandom(7))
    logger = MessageLogger(db="tmp.sqlite",usecache=True)
    #for _ in xrange(1,100):
    #    logger.logMsg(CONV_TYPE_IM, "yahoo", choice(randstrings), "someone", "Hello", "someone",time())
    #logger.commit()
    logger.logMsg(CONV_TYPE_CHAT,"acct", "yahoo", "someone", "hi", "acct", time())
    logger.commit()
    for m in logger.getMsgs("acct", "yahoo"):
        print m
        