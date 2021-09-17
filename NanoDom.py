# $Id: NanoDom.py,v 1.2 2004/09/15 09:43:49 tarmo Exp $
#
# Copyright 2001, 2002, 2003 by Fle3 Team and contributors
#
# This file is part of Fle3.
#
# Fle3 is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Fle3 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fle3; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Extremely light-weight SAX->DOM->XML translator."""

import sys, time, re
import zipfile
from types import UnicodeType
from Shared.DC.xml.xmllib import illegal

"""
Plan of SAX event handling:

- start: TAG + attributes
- data: CDATA
  - stat: sub TAG+attrs
  - data
  - end sub
  - ...
- end: TAG

When we have an object that can be created, we do that in the appropriate
END event. The start attrs, data and all subelement info should be somewhere.


"""

def escape(s, quote=None):
    """Replace special characters '&', '<' and '>' by SGML entities."""
    s = s.replace("&", "&amp;") # Must be done first!
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    if quote:
        s = s.replace('"', "&quot;")
    return s

def strip_non_xml(s,encoding='utf-8'):
    # Remove all characters not allowed in XML (mainly control characters)
    # NOTE: This content WILL just disappear! Dangerous!
    if type(s)==UnicodeType:
        us=s
    else:
        us=unicode(s,encoding)
    if illegal.search(us):
        clean_s=u""
        for c in us:
##        #Surrogates: D800-DBFF and DC00-DFFF
##         if c in u'\u0009\u000a\u000d' or \
##                (c>=u'\u0020' and c<=u'\ud7ff') or \
##                (c>=u'\ud800' and c<=u'\udfff') or \
##                (c>=u'\ue000' and c<=u'\ufffd') or \
##                (c>=u'\u10000' and c<=u'\u10ffff'):
##             clean_s+=c
            # TODO! Replace according to var _illegal_!!
            if not (c<u'\u0009' or (c>u'\u000d' and c<u'\u0020') or
                    c in u'\u000b\u000c'):
                clean_s+=c
    else:
        clean_s=us
    if type(s)==UnicodeType:
        return clean_s
    return clean_s.encode(encoding)

def to_utf8(s):
    return s.encode('utf-8')

def to_unicode(s,encoding='utf-8'):
    if not s:
        return u''
    if type(s)==UnicodeType:
        return s
    try:
        return unicode(s,encoding)
    except UnicodeError:
        return unicode(s,'iso-8859-1')




class TextNode:
    def __init__(self,text):
        self.tagName=''
        self.nodeName=''
        self.nodeValue=to_unicode(text)

    def writexml(self,out):
        out.write(u'%s' % escape(strip_non_xml(self.nodeValue)))

class Element(TextNode):
    def __init__(self,name):
        self.tagName=name
        self.nodeName=self.tagName
        self.childNodes=[]
        self.attrs={}
        self.nodeValue=u''
        self.firstChild=None
    def getAttribute(self,name):
        try:
            return self.attrs[name]
        except KeyError:
            return u''
    def setAttribute(self,name,value):
        self.attrs[name]=to_unicode(value)
    def appendChild(self,node):
        self.childNodes.append(node)
        #print '%s / %s' % (self.tagName, node.tagName)
        if not self.firstChild:
            self.firstChild=self.childNodes[0]

    def writexml(self,out):
        att=u''
        for (name,value) in self.attrs.items():
            att+=u' %s="%s"' % (name,escape(strip_non_xml(value),quote=1))
        if not self.childNodes:
            out.write(u'<%s%s/>' % (self.tagName,att))
        else:
            out.write(u'<%s%s>' % (self.tagName,att))
            for node in self.childNodes:
                node.writexml(out)
            out.write(u'</%s>' % self.tagName)

    def getElementsByTagName(self,tag):
        return self.__recursebyname(tag,[])

    def __recursebyname(self,tag,matches):
        if self.tagName==tag or tag=='*':
            matches.append(self)
        for child in self.childNodes:
            try:
                matches=child.__recursebyname(tag,matches)
            except AttributeError:
                pass
        return matches

class DOM(Element):
    def __init__(self):
        Element.__init__(self,'')
    def createElement(self,name):
        elem=Element(name)
        elem.ownerDocument=self
        return elem
    def createTextNode(self,text):
        node=TextNode(text)
        node.ownerDocument=self
        return node

    def writexml(self,out):
        out.write(u'<?xml version="1.0" ?>\n')
        for node in self.childNodes:
            node.writexml(out)

class NanoDom:
    """Receives SAX events and produces a DOM."""

    def __init__(self,parser=None):
        if parser:
            parser.CharacterDataHandler=self.handle_data
            parser.StartElementHandler=self.handle_starttag
            parser.EndElementHandler=self.handle_endtag
        self.dom=DOM()
        self.traversal=[]
        self.traversal.append(self.dom)

    # Event multiplexers
    def handle_starttag(self,tag,attrs):
        elem = self.dom.createElement(tag)
        attrdict={}
        prev=None
        for x in attrs:
            if prev:
                attrdict[prev]=x
                prev=None
            else:
                prev=x
        for (name,value) in attrdict.items():
            elem.setAttribute(name,value)
        self.traversal[-1].appendChild(elem)
        self.traversal.append(elem)

    def handle_data(self,data):
        elem=self.traversal[-1]
        node=self.dom.createTextNode(data)
        elem.appendChild(node)

    def handle_endtag(self,tag):
        self.traversal.pop()
        #print "ENDED %s" % tag

#EOF



