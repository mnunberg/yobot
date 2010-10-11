#!/usr/bin/env python
# -*- coding: utf-8 -*-
from HTMLParser import HTMLParser
import re
import sys
import smiley

re_int = re.compile("\d+")

def point_to_html(x):
    #copied from libpurple/protocols/yahoo/util.c
    if (x < 8):
            return 1
    if (x < 10): 
            return 2
    if (x < 13):
            return 3
    if (x < 17):
            return 4
    if (x < 25):
            return 5
    if (x < 35):
            return 6
    return 7

def _relativize(s):
    pass

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

            _font_tag_begin = "<font "
            have_font_attrs = False
            font = d.get("font-family")
            if font:
                have_font_attrs = True
                _font_tag_begin += "face=%s " % (font,)
            color = d.get("color")
            if color:
                have_font_attrs = True
                _font_tag_begin += "color='%s' " % (color)
                
            size = d.get('font-size', "10")
            m = re_int.match(size)
            if m:
                size = m.group(0)
                have_font_attrs = True
                _font_tag_begin += "style='font-size:%spt;' absz='%s' " % (size,size)
                _font_tag_begin += "size='%s' " % (str(point_to_html(int(size))),)

            if have_font_attrs:
                _font_tag_begin += ">"
                self.result += _font_tag_begin
                end_fmt += "</font>"
            
            if end_fmt:
                self.end_tags.append(end_fmt)
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
    result = ""
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
        
            if not attrs.get("style"): attrs["style"]=""
            attrs["style"] += re.sub(r"(font-size\s*:\s*)(\d+)(pt|px)",
                                        lambda m: "font-size:" + str(point_to_html(int(m.group(2)))),
                                        attrs["style"])
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
            

_outgoing_parser = OutgoingParser()
_incoming_parser = IncomingParser()

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
    regexp = smiley.proto_smiley_regex[improto]
    def repl_fn(m):
        smiley_name = smiley.smiley_proto_expand_htmlescaped_only[(m.group(0), improto)]
        return '<img src="%s/%s" height="%d" width="%d"/>' % (path_prefix, smiley_name, y, x)
    return re.sub(regexp, repl_fn, txt)
    
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