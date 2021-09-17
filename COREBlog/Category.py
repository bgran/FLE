##############################################################################
#
# Category.py
# Classes for Categories
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
from string import join,find,lower
from time import time

from Globals import Persistent,HTMLFile
import Globals
from Acquisition import Implicit

from permissions import View,ManageCOREBlog,AddCOREBlogEntries,AddCOREBlogComments,ModerateCOREBlogEntries
from OFS.Traversable import Traversable
from AccessControl import ClassSecurityInfo
from DateTime import DateTime
from utility import remove_html

__doc__="""Zope Blog Product 'COREBlog:Category'
$Id: Category.py,v 1.1 2004/09/02 09:54:39 tarmo Exp $"""

__version__='$Revision: 1.1 $'[11:-2]

class Category(Persistent,Implicit):
    """Class for COREBlog Category"""

    security = ClassSecurityInfo()

    security.setDefaultAccess("allow")

    meta_type='COREBlog Category'
    #icon   =''


    security.declarePrivate('__init__')
    def __init__(self,id,name,description,icon_path="",created = -1):
        self.id = str(id)
        self.name = name
        self.description = description
        self.icon_path = icon_path
        self.count = 0
        if created != -1:
            self.created = created
        else:
            self.created = time()


    #Datetime information
    security.declareProtected(View, 'created_date')
    def created_date(self):
        """Return DateTime object for Object creation time"""
        return DateTime(self.created)


    security.declareProtected(ManageCOREBlog, 'get_count')
    def get_count(self):
        return self.count


    security.declareProtected(ManageCOREBlog, 'set_count')
    def set_count(self,count):
        self.count = count
        return self.count


    security.declareProtected(ManageCOREBlog, 'edit')
    def edit(self,name,description,icon_path):
        self.name = remove_html(name)
        self.description = description
        self.icon_path = remove_html(icon_path)

Globals.InitializeClass(Category)

