#!/usr/bin/python
#
# Copyright (c) 1999 Butch Landingin
# All rights reserved. Written by Butch Landingin <butchland@yahoo.com>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  In accordance with the license provided for by the software upon
#  which some of the source code has been derived or used, the following acknowledgement
#  is hereby provided :
#
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
#
#

__doc__ = """HTML filter thanks to Itamar Shtull-Trauring"""
__version__='$Revision: 1.4 $'[11:-2]

import sgmllib, string

class StrippingParser(sgmllib.SGMLParser):
    from htmlentitydefs import entitydefs # replace entitydefs from sgmllib
    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
        self.result = ""
        self.endTagList = []
    def handle_data(self, data):
        if data:
            self.result = self.result + data
    def handle_charref(self, name):
        self.result = "%s&#%s;" % (self.result, name)
    def handle_entityref(self, name):
        if self.entitydefs.has_key(name):
            x = ';'
        else:
            # this breaks unstandard entities that end with ';'
            x = ''
        self.result = "%s&%s%s" % (self.result, name, x)
    def unknown_starttag(self, tag, attrs):
        """ Delete all tags except for legal ones """
        if string.lower(tag) in self.valid_tags:
            self.result = self.result + '<' + tag
            for k, v in attrs:
                if string.lower(k[0:2]) != 'on' and string.lower(v[0:10]) != 'javascript':
                    self.result = '%s %s="%s"' % (self.result, k, v)
            endTag = '</%s>' % tag
            self.endTagList.insert(0,endTag)
            self.result = self.result + '>'
    def unknown_endtag(self, tag):
        if string.lower(tag) in self.valid_tags:
            self.result = "%s</%s>" % (self.result, tag)
            remTag = '</%s>' % tag
            self.endTagList.remove(remTag)
    def cleanup(self):
        """ Append missing closing tags """
        for j in range(len(self.endTagList)):
                self.result = self.result + self.endTagList[j]
def strip(s, valid_tags):
    parser = StrippingParser()
    parser.valid_tags = valid_tags
    parser.feed(s)
    parser.close()
    parser.cleanup()
    return parser.result
if __name__=='__main__':
    text = """<HTML>
<HEAD><TITLE> New Document </TITLE>
<META NAME="Keywords" CONTENT=""></HEAD>
<BODY BGCOLOR="#FFFFFF">
<h1> Hello! </h1>
<a href="index.html" align="left" ONClick="window.open()">index.html</a>
<p>This is some <B><B><B name="my name">this is<I> a simple</I> text</B>
<a><a href="JAVascript:1/0">link</a>.
</BODY></HTML>"""
    print strip(text, 'text/html', ['a', 'h', 'p', 'b'])

# EOF
