#!/usr/bin/env python
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
import lxml.html
import re
from lxml.html import Element
from xml import sax

re_int = re.compile("\d+")

def _parse_style(e):
    d = {}
    s = e.attrib.get("style", None)
    if not s: return d
    for sa in s.split(";"):
        try:
            k, v = sa.split(":")
        except ValueError:
            continue
        d[k.strip()] = v.strip()
    return d
    

def simplify_css(txt):
    txt = lxml.html.fromstring(txt)
    body = txt.body
    resultLine = body.find("body/p")
    if not resultLine: return
    resultLine.tag = "font"
    
    #clear the garbage..
    resultLine.attrib.clear()
    #now get the body attributes and apply them to the tag..
    d = _parse_style(body)
    if d:
        font = d.get('font-family', "")
        size = d.get('font-size', "10")
        m = re_int.match(size)
        if m:
            size = m.group(0)
        resultLine.attrib['face'] = font
        resultLine.attrib['absz'] = size
    for e in resultLine.iterdescendants():
        if not e.text: continue
        tagnames = []
        d = _parse_style(e)
        if d:
            decoration = d.get('text-decoration')
            if decoration and 'underline' in decoration:
                tagnames.append("u")
            font_style = d.get('font-style')
            if font_style and 'italic' in font_style:
                tagnames.append("i")
            font_weight = d.get('font-weight')
            if font_weight and int(font_weight) > 400:
                tagnames.append("b")
            #commented out: shouldn't happen
            #if not len(tags):
            #    tags.append(Element("font"))
            
            first_tag = tags.pop(0)
            if len(tags):
                last_tag = tags.pop()
                if len(tags):
                    for t in tags:
                        first_tag.append(t)
                first_tag.append(last_tag)
                last_tag.text = e.text
            else:
                first_tag.text = e.text
            resultLine.append(first_tag)
    return lxml.html.tostring(resultLine)

parser = sax.make_parser()
