##############################################################################
#
# jmimetool.py
# class imprementation to handle Japanese Mail Message
#
# Copyright (c) 2002-2004 Atsushi Shibata. All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and its 
# documentation for any purpose and without fee is hereby granted, provided that
# the above copyright notice appear in all copies and that both that copyright 
# notice and this permission notice appear in supporting documentation, and that
# the name of Atsushi Shibata not be used in advertising or publicity pertaining 
# to distribution of the software without specific, written prior permission. 
# 
# ATSUSHI SHIBAT DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, 
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO
# EVENT SHALL SHIBAT ATSUSHI BE LIABLE FOR ANY SPECIAL, INDIRECT OR 
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF
# USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE. 
#
##############################################################################

import string
import re
import StringIO
import base64
import mimetools
import multifile

from utility import convert_charcode,code_jis

def decode_header(hdr):
    pat = re.compile("=\?iso-2022-jp\?B\?[^\?]+\?=",re.I | re.M)
    l = pat.findall(hdr)

    for i in l:
        b = i[16:len(i)-2]
        r = base64.decodestring(b)
        hdr = string.replace(hdr,i,r)

    return hdr

class Message(mimetools.Message):
    #class imprementation to handle Japanese Mail Message
    #Decode headers,convert Kanji Code if need....

    def __init__(self,fp,codestr):
        #read lines and decode header if need
        inbody = 0
        self.bodypos = 0
        lines = []
        for line in string.split(fp.getvalue(),"\n"):
            if len(line) == 0 and inbody == 0:
                inbody = 1
                self.bodypos = self.bodypos + 2
            elif inbody == 0:
                #line is in header...
                self.bodypos = self.bodypos + len(line) + 2
                try:
                    line = convert_charcode(decode_header(line),codestr,code_jis)
                except:
                    pass
            else:
                #line is in body...
                try:
                    line = convert_charcode(line,codestr,code_jis)
                except:
                    pass
            lines.append(line)

        self.buffer = StringIO.StringIO(string.join(lines,"\n"))
        mimetools.Message.__init__(self,self.buffer,1)

    def get_parts(self):
        #Dividing multipart and return tupple of dictionaries.
        #"type" for type,"data" for data

        #Get message type of mail
        messagetype = self.gettype()

        rett = []

        if messagetype[:10] == "multipart/":
            #The message is multipart

            file = multifile.MultiFile(self.buffer)
            file.push(self.getparam("boundary"))
            while file.next():
                submsg = mimetools.Message(file)
                data = StringIO.StringIO()
                try:
                    mimetools.decode(file, data, submsg.getencoding())
                except ValueError:
                    pass
                rett.append({"type":submsg.gettype(),"data":data})
            file.pop()
        else:
            d = {}
            d["type"] = messagetype

            inbody = 0
            lines = []
            self.buffer.seek(0)
            for line in string.split(self.buffer.getvalue(),"\n"):
                if len(line) == 0:
                    inbody = 1
                elif inbody == 1:
                    lines.append(line+"\n")
            d["data"] = StringIO.StringIO(string.join(lines))
            rett.append(d)

        return rett


