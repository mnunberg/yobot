#!/usr/bin/env python
# -*- coding: utf-8 -*-
from HTMLParser import HTMLParser
import re
import sys
import smiley

re_int = re.compile("\d+")

def point_to_html(x):
    #copied from libpurple/protocols/yahoo/util.c
    if (x < 9): return 1
    if (x < 12): return 2
    if (x < 15): return 3
    if (x < 17): return 4
    if (x < 25): return 5
    if (x < 35): return 6
    return 7

def point_to_html_str(x):
    if (x <= 6): return "xx-small"
    if (x <= 9): return "x-small"
    if (x <= 15): return "medium"
    if (x <= 20): return "large"
    if (x <= 25): return "x-large"
    return "xx-large"

fontsize_style_regexp = re.compile(r'font-size\s*:\s*(\d+)(pt|px)\s*;?', re.I)

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

class Attr(object):
    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError, e:
            return lambda v, *args, **kwargs: getattr(self, "genopt")(name, v, *args, **kwargs)
    def genopt(self, opt, value):
        return ' %s="%s" ' % (opt, value)        
        
a = Attr()

def add_tag(tag, begin_l, end_l):
    begin_l.append("<%s>" % (tag))
    end_l.append("</%s>" % (tag))

class OutgoingParser(HTMLParser):
    result = ""
    end_tags = [] #should use a Queue for this eventually..
    cts = True
    def handle_starttag(self, name, attrs):
        d = {}
        for k, v in attrs:
            d[k] = v
        attrs = d
        d = _parse_style(attrs.get("style"))
        if name == "body": #get font..
            #do not submit any "default" formatting, if not requested
            self.cts = True
        elif name == "span": #get formatting...
            begin_l, end_l = ([],[])
            decoration = d.get('text-decoration')
            if decoration and 'underline' in decoration:
                add_tag("u", begin_l, end_l)
            font_style = d.get('font-style')
            if font_style and 'italic' in font_style:
                add_tag("i", begin_l, end_l)
            font_weight = d.get('font-weight')
            if font_weight and int(font_weight) > 400:
                add_tag("b", begin_l, end_l)

            _font_tag_begin = "<font "
            have_font_attrs = False
            font = d.get("font-family")
            if font:
                have_font_attrs = True
                _font_tag_begin += a.face(font.strip("\'\""))
            color = d.get("color")
            if color:
                have_font_attrs = True
                _font_tag_begin += a.color(color)
                
            osz = d.get("font-size")
            if osz:
                print osz
                if osz.endswith("pt"): #absolute:
                    _font_tag_begin += a.absz(osz.split("pt")[0])
                    _font_tag_begin += ' style="font-size:%s;" ' % (osz)
                    _font_tag_begin += a.size(point_to_html(int(osz.split("pt")[0])))
                elif osz.isdigit():
                    #omit abst and font-size, just use CSS...
                    _font_tag_begin += ' style="font-size:%s;" ' % (osz)
            if have_font_attrs:
                _font_tag_begin += ">"
                self.result += (
                    "".join(begin_l) +
                    re.sub(r"\s+", " ", _font_tag_begin)
                    )
                end_l.append("</font>")
            
            if end_l:
                self.end_tags.append("".join(end_l))
        else:
            self.end_tags.append("")

    def handle_endtag(self, name):
        try:
            end = self.end_tags.pop()
        except IndexError:
            return
        if end:
            self.result += end
            
    def handle_data(self, data):
        if self.cts:
            self.result += data
    def handle_entityref(self, name):
        self.result += "&%s;" % (name,)
    def reset(self):
        HTMLParser.reset(self)
        self.result = ""
        self.end_tags = []
        self.cts = False

class IncomingParser(HTMLParser):
    _result = []
    #each element in result will 
    result = ""
    _txt_tmp = ""
    end_tags = []
    use_relsize = False
    def handle_starttag(self, name, attrs):
        name = name.lower()
        d = {}
        for k, v in attrs:
            d[str(k.lower())] = str(v.lower())
        attrs = d
        
        def restore(tag):
            self.result += "<" + tag
            for attr, vals in attrs.items():
                self.result += ' %s="%s" ' % (attr, vals)
            self.result += ">"
            self.end_tags.append("</%s>" % (tag,))
    
        if self.use_relsize:
            if name == "font":
                sz = attrs.get("size", "")
                if sz and (sz.endswith("pt") or sz.endswith("px")):
                    sz = re_int.match(sz)
                    if sz: attrs["size"] = "%s" % (str(point_to_html(int(sz.group(0)))),)
                
                if attrs.get("size"):
                    attrs.pop("absz", "")
                else:
                    sz = attrs.get("absz")
                    if sz:
                        if sz.isdigit(): attrs["size"] = sz
                        else: print "WARNING: INVALID VALUE FOR ABSZ (%s)" % (sz,)
        
            if attrs.get("style"):
                m = fontsize_style_regexp.search(attrs["style"])
                if m:
                    def repl(m):
                        return "font-size:%s;" % (point_to_html_str(int(m.group(1))))
                    attrs["style"] = fontsize_style_regexp.sub(repl, attrs["style"])
                    attrs.pop("size", None)
        else:
            #no point in converting relative sizes to absolute ones, thus we only
            #need to convert the non-standard yahoo-based absz attribute
            if name == "font":
                #yahoo uses absz attribute
                absz = attrs.get("absz")
                if absz:
                    tmp = attrs.get("style")
                    if tmp:
                        tmp += " font-size:%dpt;" % (int(absz),)
                        attrs["style"] = tmp
                    else:
                        attrs["style"] = "font-size:%dpt;" % (int(absz),)
                    attrs.pop("size", "")
        #replace "structure" tags with a simple font tag
        if name in ("head", "script", "body", "html", "p"):
            if len(attrs):
                restore("font")
            else:
                self.end_tags.append("")
            return
        restore(name)
    
    def handle_endtag(self, name):
        try:
            end = self.end_tags.pop()
        except IndexError:
            return
        if end:
            self.result += end
            
    def handle_data(self, data):
        self.result += data
    def handle_entityref(self, name):
        self.result += "&" + name + ";"
            

class SmileyParser(HTMLParser):
    """This should really go into the IncomingParser..."""
    def __init__(self):
        HTMLParser.__init__(self)
        self.reset()
    def reset(self):
        self.current_text = ""
        self.result = ""
        HTMLParser.reset(self)
        self.close()
    def handle_starttag(self, tag, attrs):
        #flush previous result:
        self.smileyreplace()
        self.result += self.current_text
        self.current_text = ""
        oldattr = attrs
        attrs = {}
        for k, v in oldattr:
            attrs[k] = v
        self.result += "<%s %s>" % (tag,
                                    " ".join(["%s='%s'" % (k,v) for k, v in attrs.items()]))
    def handle_endtag(self, tag):
        #flush again...
        self.smileyreplace()
        self.result += self.current_text
        self.current_text = ""
        self.result += "</%s>" % (tag,)
    def handle_data(self, data):
        self.current_text += data
    def handle_entityref(self, name):
        self.current_text += "&" + name + ";"
    def getresult(self):
        return self.result + self.current_text
    def feed(self, data, **kwargs):
        """kwargs are x, y, path_prefix, and improto"""
        self.smiley_params = kwargs
        try:
            self.smiley_params["regexp"] = smiley.htmlescaped.regexp[kwargs["improto"]]
        except KeyError, e:
            print e
            self.smiley_params["regexp"] = smiley.htmlescaped.regexp[smiley.DEFAULT_SCHEME]
            self.smiley_params["improto"] = smiley.DEFAULT_SCHEME
        HTMLParser.feed(self, data)
    def smileyreplace(self):
        if not self.current_text: return
        self.current_text = self.smiley_params["regexp"].sub(
            self.regexp_repl, self.current_text)
    def regexp_repl(self, m):
        try:
            smiley_name = smiley.htmlescaped.resourcetable[
                (m.group(0), self.smiley_params["improto"])]
            return '<img src="%s/%s" height="%d" width="%d"/>' % (
                self.smiley_params["path_prefix"], smiley_name,
                self.smiley_params["y"], self.smiley_params["x"])
        except KeyError, e:
            print e, "OOPS"
            return m.group(0)


_outgoing_parser = OutgoingParser()
_incoming_parser = IncomingParser()
_smiley_parser = SmileyParser()

def simplify_css(txt):
    _outgoing_parser.reset()
    _outgoing_parser.feed(txt)
    return re.sub("\n","",_outgoing_parser.result)

def process_input(txt, use_relsize=True, use_samesize=False):
    _incoming_parser.result = ""
    _incoming_parser.use_relsize = use_relsize
    _incoming_parser.feed(txt)
    return _incoming_parser.result.strip()

def insert_smileys(txt, improto, path_prefix, x=24, y=24):
    #process smileys
    _smiley_parser.reset()
    _smiley_parser.feed(txt, improto=improto, path_prefix=path_prefix, x=x, y=y)
    return _smiley_parser.getresult()
    
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
<span style=" text-decoration: underline;">underline :-&gt;</span>normal</p></body></html>
"""

    INPUT_TXT="""
<b><font color='#007100'><font face='Trebuchet MS' size='6' absz='32'>HAI</font></font></b>
    """
    INPUT_WITH_STYLE="""
<b><font color='#007100'><font face='Trebuchet MS' size='6' absz='32' style="foo:bar;">HAI :-&gt :)) :( :(( :)) ;</font></font></b>
        """
    INPUT_UNICODE="""
    <font size='6' absz='32'>t_k_220: هااااااااااااااااااااااااااااااااااااى مكن نتعرف على بنت من مصر انا من </font>
    """
    INPUT_PLAIN="hi :-&lt; :-&gt;"
    print "simplify_css: ", simplify_css(HTML)
    #print ""
    #print "process_input", process_input(INPUT_TXT)
    #print ""
    #print "process_input", process_input(INPUT_WITH_STYLE)
    #print ""
    #print "process_input", process_input(INPUT_UNICODE)
    #print ""
    #print "process_input - smileys", insert_smileys(process_input(INPUT_PLAIN), 1, "foo")
    #print "process_input", process_input(HTML)
    #ret = process_input(INPUT_WITH_STYLE)
    #print insert_smileys(ret, 1, "foo", 16, 16)