#!/usr/bin/env python
import re
import sqlite3.dbapi2 as sqlite3
import pickle

class TriviaDBError(Exception): pass
class DBLayoutUnknown(TriviaDBError): pass
class DBError(TriviaDBError): pass
def _regexp(self):
    r = re.compile(expr)
    return bool(r.match(item))

class _YobotTriviaBase(object):
    def __init__(self, filename):
        self.dbfile = filename
        self.connected = False
        self.connection = None
        self.cursor = None
    def connectdb(self):
        if self.connected: return
        self.connection = sqlite3.connect(self.dbfile)
        self.connection.row_factory = sqlite3.Row
        self.connection.text_factory = str
        self.connection.create_function("regexp", 2, _regexp)
        self.cursor = self.connection.cursor()
        self.validatedb()
    def validatedb(self):
        """Initial validation functions. The base implementation does nothing,
        override this"""
        pass
    def disconnectdb(self):
        if not self.connected or not self.connection: return
        self.connection.close()
        self.connection = None
        self.cursor = None
        self.connected = False
    def __del__(self):
        self.disconnectdb()
        super(_YobotTriviaBase, self).__del__()

class QuestionsDB(_YobotTriviaBase):
    def getquestion(self, categories=[], blacklist=True, register_usage=False):
        """-> {"question", "answers", "category", "id"}"""
        rstr = ""
        if categories:
            categories = list(categories)
            l = ["'" + s + "'" for s in categories]
            if self.blacklist:
                rstr += "NOT "
            category_expr = "category==" + l.pop()
            if len(l):
                l.insert(0, "")
                category_expr += " or category==".join(l)
            rstr += "(" + category_expr + ")"
            rstr = "WHERE " + rstr
            log_warn(rstr)
        res = self.cursor.execute("""
                                    SELECT * FROM questions
                                     %s
                                     ORDER BY frequency ASC, random()
                                     LIMIT 1
                                    """ % (rstr,)).fetchone()
        if register_usage:
            self.cursor.execute("""
                                  UPDATE questions
                                   SET frequency = (frequency+1)
                                    WHERE id = ?
                                  """, (res["id"],))
            self.connection.commit()
        
        alt_answers = pickle.loads(res["alt_answers"])
        answers = (res["answer"],) + ( alt_answers if alt_answers else ())
        
        return {"question":res["question"],
               "answers":answers,
               "id":res["id"],
               "category":res["category"]}
    def validatedb(self):
        try:
            self.cursor.execute("""
                SELECT id, frequency, question, answer, alt_answers FROM questions LIMIT 1""").fetchone()[0]
        except Exception, e:
            raise DBError(e)
        
class AnagramDB(_YobotTriviaBase):
    def getanagram(self, minlen, maxlen, prefix_exclude=(), suffix_exclude=()):
        "-> word"
        #determine whether we can use a regex here..
        prepend = ""
        append = ""
        rstr = ""
        if prefix_exclude: prepend += "|".join(prefix_exclude)
        if suffix_exclude: append += "|".join(suffix_exclude)
        if prepend or append: rstr = "word NOT REGEXP '%s' AND" % (prepend + ".*" + append,)
            
        word = self.cursor.execute("""SELECT word FROM words
                                                    WHERE %s LENGTH(word) >= ? AND
                                                    LENGTH(word) <= ?
                                                ORDER BY random()
                                                LIMIT 1
                                              """ % (rstr,),
                                              (minlen, maxlen)).fetchone()
        if not word:
            return None
        word = word[0]
        return word
    def validatedb(self):
        try:
            self.cursor.execute("SELECT word FROM words LIMIT 1").fetchone()[0]
        except Exception, e:
            raise DBError(e)