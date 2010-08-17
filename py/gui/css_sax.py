#!/usr/bin/env python

from xml.sax.handler import ContentHandler
from xml.sax import make_parser, parseString
from lxml.html import fromstring, tostring
import re
import sys
re_int = re.compile("\d+")

def _parse_style(txt):
    d = {}
    s = txt
    if not s: return d
    for sa in s.split(";"):
        try:
            k, v = sa.split(":")
        except ValueError:
            continue
        d[k.strip()] = v.strip()
    return d


class Parser(ContentHandler):
    result = ""
    end_tags = [] #should use a Queue for this eventually...
    def startDocument(self):
        pass
    def endDocument(self):
        pass
    def startElement(self, name, attrs):
        d = _parse_style(attrs.getValue("style"))
        if name == "body": #get font..
            #this is really a font tag..
            self.result += "<font "
            if not d:
                end_tags.append("</font>")
                return
            font = d.get('font-family', "")
            size = d.get('font-size', "10")
            m = re_int.match(size)
            if m:
                size = m.group(0)
            self.result += "face=%s absz='%s'" % (font, size)
            self.result += ">"
            self.end_tags.append("</font>")
        elif name == "span": #get formatting...
            end_fmt = ""
            decoration = d.get('text-decoration')
            if decoration and 'underline' in decoration:
                self.result += "<u>"
                end_fmt += "</u>"
            font_style = d.get('font-style')
            if font_style and 'italic' in font_style:
                self.result += "<i>"
                end_fmt += "</i>"
            font_weight = d.get('font-weight')
            if font_weight and int(font_weight) > 400:
                self.result += "<b>"
                end_fmt += "</b>"
            if end_fmt:
                self.end_tags.append(end_fmt)
        else:
            #sys.stderr.write("unhandled: " + name +"\n")
            #sys.stderr.flush()
            self.end_tags.append("")

    def endElement(self, name):
        try:
            end = self.end_tags.pop()
        except IndexError:
            return
        if end:
            self.result += end
    def characters(self, content):
        self.result += content


_parser = Parser()

def simplify_css(txt):
    _parser.result = ""
    body = fromstring(txt)
    body = tostring(body.body)
    parseString(body, _parser)
    return _parser.result

if __name__ == "__main__":
    HTML="""
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head>
<body style=" font-family:'Lucida Grande'; font-size:10pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">normal
<span style=" font-style:italic;">italic</span>
<span style=" font-weight:600; font-style:italic;">bold</span>
<span style=" font-weight:600;"> bold not italic </span>normal
<span style=" text-decoration: underline;">underline </span>normal</p></body></html>
"""
    for _ in xrange(1000):
        res = simplify_css(HTML)    
    print res