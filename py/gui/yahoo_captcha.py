#!/usr/bin/env python
import urllib
import urllib2

import lxml.html
import time
import sys
from twisted.internet import threads

from PyQt4.QtGui import (QDialog, QErrorMessage, QPixmap, QVBoxLayout,
                         QDialogButtonBox, QLineEdit, QLabel, QApplication, QMainWindow)

from PyQt4.QtCore import QObject, SIGNAL, Qt
signal_connect = QObject.connect

URL="""http://captcha.chat.yahoo.com/go/captchat/?img=http://ab.login.yahoo.com/img/6hgsQuJZFen86OjtUT33jW4QAWjIIeWeuH.eG5Sydc0s2WH96I7jOIQNuH3m2otX9p5nDY9z0d9CHAxJfA--.jpg&.intl=us&.lang=en-US"""

class _CaptchaDialog(QDialog):
    def __init__(self, captcha_image, parent=None, title="Yahoo Captcha",
                 origin_url = None):
        self.answer = ""
        QDialog.__init__(self, parent)
        self.setWindowTitle(title)
        #make layout:
        layout = QVBoxLayout(self)
        img = QLabel(self)
        img.setPixmap(captcha_image)
        layout.addWidget(img)
        edit = QLineEdit()
        edit.setStyleSheet("font-weight:bold;font-size:20px;text-align:center;")
        self.edit = edit
        layout.addWidget(edit)
        if origin_url:
            self.url_display = QLineEdit(self)
            self.url_display.setText(origin_url)
            self.url_display.setReadOnly(True)
            self.layout.addWidget(QLabel("Source:"))
            self.layout.addWidget(self.url_display)
        bbox = QDialogButtonBox(QDialogButtonBox.Ok)
        layout.addWidget(bbox)
        signal_connect(bbox, SIGNAL("accepted()"), self.accept)
        self.setWindowModality(Qt.WindowModal)
        signal_connect(self, SIGNAL("accepted()"), lambda: setattr(self, "answer", str(self.edit.text())))

class ImageGetError(Exception): pass
class ImageDataError(Exception): pass
class IncorrectResponse(Exception): pass
class FormParseError(Exception): pass

class CaptchaPrompter(object):
    """execution flow:
    get the initial URL data, then display a dialog, keep it in memory and keep track
    of its answer code, if any.. then process some more.. etc.
    make wrapper functions for things that block, so that they can be placed within actual
    threads...
    Deferreds should be used for getting the initial data from the yahoo captcha page,
    and for submitting the data back. Use Qt's signal system for getting input from the
    user.. and fire a deferred based on that
    """
    def __init__(self, qt_parent=None):
        self.qt_parent = qt_parent
        
    def prompt(self, url):
        d = threads.deferToThread(self.get_captcha, url)
        d.addCallback(self.mk_qpixmap)
        d.addCallback(self.show_dialog)
        d.addErrback(self.errhandler)

    #stack callbacks for twisted Deferred
    def get_captcha(self, url):
        "Rely on errback to catch our errors..."
        if url:
            uresponse = urllib2.urlopen(url)
            page_data = uresponse.read()
            e = lxml.html.fromstring(page_data)
            self.captcha_etree = e
        else:
            e = self.captcha_etree
        #get image..
        imageurl = e.xpath("//div[@class='captcha']/img")
        if not imageurl: raise ImageGetError("""e.xpath("//div[@class='captcha']/img")""" + " failed")
        if not imageurl[0].attrib.get("src"): raise ImageGetError("can't find 'src' attribute in img tag")
        imageurl = imageurl[0].attrib["src"]
        imagedata = urllib2.urlopen(imageurl).read()
        return imagedata
    
    def mk_qpixmap(self, imagedata):
        qpixmap = QPixmap()
        if not qpixmap.loadFromData(imagedata): raise ImageDataError("Couldn't load QPixmap from data")
        self.captcha_image = qpixmap
        return qpixmap
        
    def send_captcha_response(self, answer):
        form = self.captcha_etree.xpath("//form[@action='/captcha1']")
        if not form: raise FormParseError()
        form = form[0]
        form_kv = {}
        for k, v in form.fields.items():
            form_kv[k] = v
        form_kv["answer"] = str(answer)
        data = urllib.urlencode(form_kv)
        uresponse = urllib2.urlopen("http://captcha.chat.yahoo.com/captcha1", data=data)
        if "tryagain=" in uresponse.url:
            self.captcha_etree = lxml.html.fromstring(uresponse.read())
            return False
        return True
    
    def show_dialog(self, qpixmap):
        self.dlg = _CaptchaDialog(qpixmap)
        signal_connect(self.dlg, SIGNAL("accepted()"), self.dlg_cb)
        self.dlg.exec_()
    
    def dlg_cb(self):
        answer = self.dlg.answer
        d = threads.deferToThread(self.send_captcha_response, answer)
        def cb(result):
            if not result:
                raise IncorrectResponse

        d.addCallback(cb)
        d.addErrback(self.prompt_dispatcher_eb)
        d.addErrback(self.errhandler)
            
    def errhandler(self, failure):
        print "ERRHANDLER"
        msg = failure.getErrorMessage()
        print msg
        raise Exception("Grrrr")
        return failure
    
    def prompt_dispatcher_eb(self, failure):
        if failure.check(IncorrectResponse):
            self.prompt(None)
        else:
            failure.raiseException()

if __name__ == "__main__":
    opener = urllib2.build_opener(urllib2.HTTPHandler(debuglevel=1))
    urllib2.install_opener(opener)
    app = QApplication(sys.argv)
    
    from contrib import qt4reactor
    qt4reactor.install
    from twisted.internet import reactor    
    prompter = CaptchaPrompter()
    prompter.prompt(URL)
    print "DONE"
    
    reactor.run()