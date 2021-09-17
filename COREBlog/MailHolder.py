##############################################################################
#
# MailHolder.py
# class imprementation for hold index information of mail
#
# Copyright (c) 2002-2004 Atsushi Shibata(shibata@webcore.co.jp)
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
import time
import StringIO

import poplib
import jmimetool


class MailHolder:
    # class imprementation for holding index information of mail

    date_fmt = "%Y/%m/%d %H:%M:%S"

    def __init__(self,message):
        #create MailHolder object from incomming jmailtool.Message object

        #get mail information
        if message.getheader("Subject"):
            self.subject = string.replace(message.getheader("Subject"),"\n","")
        else:
            self.subject = ""
        self.datet = message.getdate("Date")
        self.sender = message.getaddrlist("From")
        self.receiver = message.getaddrlist("To")

        self.size = len(message.buffer.getvalue())

        self.recievingdatet = time.localtime(time.time())

        self.attachments = 0

    #Methods for getting mail information
    def getSubject(self):
        """ get subject"""
        #get mail subject
        return self.subject

    def getSender(self):
        #get sender string
        retsender = ""
        for addrl in self.sender:
           retsender = retsender + string.join(addrl," ")
        return retsender

    def getSenderList(self):
        #get sender in tupple(list)
        rett = []
        for addrl in self.sender:
            rett.append(string.join(addrl," "))
        return rett

    def getReceiver(self):
        #get sender string
        retreceiver = ""
        for addrl in self.receiver:
            retreceiver = retreceiver + string.join(addrl," ")
        return retreceiver

    def getReceiverList(self):
        #get sender in tupple(list)
        rett = []
        for addrl in self.receiver:
            rett.append(string.join(addrl," "))
        return rett

    def getSize(self):
        return self.size

    def getDate(self,fmt = date_fmt):
        return time.strftime(fmt,self.datet)

    def getRecievingDate(self,fmt = date_fmt):
        return time.strftime(fmt,self.recievingdatet)

    def getSize(self):
        return self.size

