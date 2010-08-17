#!/usr/bin/python
CONV_TYPE_CHAT = 1<<0
CONV_TYPE_IM = 1<<1

from collections import defaultdict
import sqlite3

class MessageLogger(object):
    #for some reason this really DOES improve performance!
    _cache = defaultdict(lambda: {}) #[account_name,protocol_name]->[other_user]->id
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
        except sqlite3.OperationalError:
            #type == chat or IM, from/to are self explanatory, except in chat,
            #to is the room name, and from is the user who has entered chat e.g. the account
            c.execute("""
                      CREATE TABLE conversations (
                        id INTEGER PRIMARY KEY, -- foreign key
                        type INTEGER NOT NULL, -- chat or IM
                        protocol_name TEXT NOT NULL, -- we need to store this as text because persistent storage cannot change
                                        -- unlike the protocol
                        account_name TEXT NOT NULL, -- who this conversation belongs to
                        other_user TEXT NOT NULL, -- who the account has conversed with, or the name of the chatroom
                        UNIQUE (type, protocol_name, account_name, other_user)
                      )
                      """)
            c.execute("""
                      CREATE TABLE messages (
                        conv_id INTEGER, -- foreign key for conversation table
                        body TEXT, -- message body
                        who TEXT, -- whoever sent this message
                        timestamp REAL, -- timestamp
                        FOREIGN KEY(conv_id) REFERENCES conversations(id) --
                        UNIQUE (conv_id, body, who, timestamp) -- try to prevent duplicate messages
                      )
                      """
                      )
    
    def _getConvId(self, protocol_name, account_name, other_user):
        conv_id = None
        try:
            conv_id = self._cache[account_name,protocol_name][other_user]
        except KeyError:
            res = self._cursor.execute("""
                           SELECT id FROM conversations
                            WHERE protocol_name =?
                            AND account_name =?
                            AND other_user =?
                           """, (protocol_name, account_name, other_user)).fetchone()
            if res:
                conv_id = res["id"]
                self._cache[account_name,protocol_name][other_user] = conv_id
        return conv_id
    
    def logMsg(self, type, protocol_name, account_name, other_user, body, who, timestamp):
        """Inserts a message into the database"""
        insert_fmt = ("""INSERT INTO messages (who, body, timestamp, conv_id)
                        VALUES (?, ?, ?, ?)""")
        
        #try to look up the conversation the cache before we query the DB...
        conv_id = self._getConvId(protocol_name, account_name, other_user)
        if not conv_id:
            self._cursor.execute("""
                               INSERT INTO conversations (type, protocol_name, account_name, other_user)
                               VALUES (?, ?, ?, ?)
                               """, (type, protocol_name, account_name, other_user))
            conv_id = self._cursor.lastrowid            
        self._cursor.execute(insert_fmt, (who, body, timestamp, conv_id))
    
    def getMsgs(protocol_name, account_name, other_user, count=50):
        """(type, [[timestamp, who, body], ...])"""
        msgs = []
        type = None
        conv_id = self._getConvId(protocol_name, account_name, other_user)
        if not conv_id:
            return (type, msgs)
        #get type:
        type = self._cursor.execute("""
                                    SELECT type FROM conversations
                                        WHERE id = ?
                                        LIMIT 1
                                    """, (conv_id,)).fetchone()[0]
        
        for m in self._cursor.execute("""
                                      SELECT timestamp, who, body FROM messages
                                        WHERE conv_id = ?
                                        LIMIT ?
                                        ORDER BY timestamp
                                      """, (conv_id, count)):
            msgs += [res["timestamp"], res["who"], res["body"]]
        return (type, msgs)
    
    def dump(self):
        for row in self._cursor.execute("select * from conversations"):
            print row
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
    for _ in xrange(1,100000):
        logger.logMsg(CONV_TYPE_IM, "yahoo", choice(randstrings), "someone", "Hello", "someone",time())
    logger.commit()