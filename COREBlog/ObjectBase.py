##############################################################################
#
# ObjectBase.py
# Classes for ObjectBase,Comments,Trackbacks
#
# Copyright (c) 2003-2004 Atsushi Shibata. All Rights Reserved.
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

#Import modules from python lib.
from time import time,gmtime,strftime

from Globals import Persistent
import Globals
from Acquisition import Implicit

from permissions import View,ManageCOREBlog,AddCOREBlogEntries,AddCOREBlogComments,ModerateCOREBlogEntries
from OFS.Traversable import Traversable
from AccessControl import ClassSecurityInfo
from DateTime import DateTime
from BTrees.IIBTree import IISet

from utility import convert_charcode,code_utf8
from trackback_tools import post_trackback

__doc__="""Zope Blog Product 'COREBlog:ObjectBase'
$Id: ObjectBase.py,v 1.1 2004/09/02 09:54:39 tarmo Exp $"""

__version__='$Revision: 1.1 $'[11:-2]

class ObjectBase(Persistent,Implicit,Traversable):
    """Baseclass for COREBlog Entry/Comment"""

    security = ClassSecurityInfo()

    security.setDefaultAccess("allow")

    meta_type='COREBlog ObjectBase'
    #icon   =''


    security.declarePrivate('__init__')
    def __init__(self,id,moderated,created = -1):
        self.id = str(id)
        self.moderated = moderated
        if created != -1:
            self.created = created
        else:
            self.created = time()


    #Datetime information
    security.declareProtected(View, 'date_created')
    def date_created(self):
        """Return DateTime object for Object creation time"""
        return DateTime(self.created)


    security.declareProtected(View,'year_created')
    def year_created(self):
        """Return year for Object creation time"""
        return DateTime(self.created).year()


    security.declareProtected(View,'month_created')
    def month_created(self):
        """Return month for Object creation time"""
        return DateTime(self.created).month()


    security.declareProtected(View,'day_created')
    def day_created(self):
        """Return day for Object creation time"""
        return DateTime(self.created).day()


    security.declareProtected(View,'weekday_created')
    def weekday_created(self):
        """Return day of the week for Object creation time"""
        setfirstweekday(SUNDAY)
        dt = DateTime(self.created)
        return weekday(dt.year(),dt.month(),dt.day())


    #moderation
    security.declareProtected(ModerateCOREBlogEntries, 'setModeration')
    def setModeration(self,moderated):
        pre_moderation = self.moderated
        self.moderated = moderated
        if pre_moderation:
            if not moderated:
                #moderation turnd into "closed"
                self.goClose()
        elif not pre_moderation:
            if moderated:
                #moderation turnd into "closed"
                self.goOpen()


    security.declarePrivate('goClose')
    def goClose(self):
        # This is hook method called when change moderation
        # This is base class,so that do nothing. Subclass shoudl override this method
        pass


    security.declarePrivate('goOpen')
    def goOpen(self):
        # This is hook method called when change moderation
        # This is base class,so that do nothing. Subclass shoudl override this method
        pass


Globals.InitializeClass(ObjectBase)

class Comment(ObjectBase):
    """Class for COREBlog Comments"""

    security = ClassSecurityInfo()
    
    meta_type='COREBlog Comment'
    description = 'COREBlog Comment class'

    icon = 'misc_/COREBlog/comment_img'


    security.declarePrivate('__init__')
    def __init__(self,id,parent_id,title,author,email,url,body,moderated,sec = -1):
        ObjectBase.__init__(self,id,moderated,sec)
        self.parent_id = parent_id
        self.title = title
        self.author = author
        self.email = email
        self.url = url
        self.body = body


    security.declareProtected(View, 'index_html')
    def index_html(self,REQUEST):
        """ Comment presentation """
        return self.comment_html(self,REQUEST)

Globals.InitializeClass(Comment)

class Trackback(ObjectBase):
    """Class for COREBlog Trackback item"""

    security = ClassSecurityInfo()
    
    meta_type='COREBlog Trackback'
    icon = 'misc_/COREBlog/trackback_img'


    security.declarePrivate('__init__')
    def __init__(self,id,parent_id,title,excerpt,url,blog_name,moderated,sec=-1):
        #Initialize instance
        ObjectBase.__init__(self,id,moderated,sec)
        self.parent_id = parent_id
        self.title = title
        self.excerpt = excerpt
        self.url = url
        self.blog_name = blog_name
        self.created = time()


Globals.InitializeClass(Trackback)


class SendingTrackback(ObjectBase):
    """Class for COREBlog Trackback/sending to another blog"""

    security = ClassSecurityInfo()
    
    meta_type='COREBlog SendingTrackback'
    icon = 'misc_/COREBlog/trackback_img'


    security.declarePrivate('__init__')
    def __init__(self,id,parent_id,url,sent = 0):
        #Initialize instance
        ObjectBase.__init__(self,id,1)
        self.parent_id = parent_id
        self.url = url
        self.sent = sent
        self.created = time()

    security.declareProtected(ManageCOREBlog, 'post_trackback')
    def post_trackback(self,src_url,blog_name,title,excerpt,charcode="",fromcode=""):
        #Post a trackback and return result code
        if charcode:
            #convert title,excerpt to charcode
            title = convert_charcode(title,charcode,fromcode)
            excerpt = convert_charcode(excerpt,charcode,fromcode)
        errcode,message = post_trackback(self.url,title,src_url, \
                                         blog_name,excerpt)
        if errcode == 0:
            #Sent!
            self.sent = 1

        return errcode,message

Globals.InitializeClass(Trackback)

