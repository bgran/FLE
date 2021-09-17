##############################################################################
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
# SHIBAT ATSUSHI DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, 
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO
# EVENT SHALL SHIBAT ATSUSHI BE LIABLE FOR ANY SPECIAL, INDIRECT OR 
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF
# USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE. 
#
##############################################################################

import COREBlog
from ImageFile import ImageFile
from COREBlog import COREBlog,manage_addCOREBlogForm,manage_addCOREBlog

__doc__="""Zope Blog Product 'COREBlog'
$Id: __init__.py,v 1.1 2004/09/02 09:54:39 tarmo Exp $"""

__version__='$Revision: 1.1 $'[11:-2]

#import ZCTextIndex constructors...
try:
    from Products.ZCTextIndex.PipelineFactory import element_factory

    def getElementGroups(self):
        return element_factory.getFactoryGroups()

    def getElementNames(self, group):
        return element_factory.getFactoryNames(group)

except:
    pass


# Register the COREBlog class
def initialize(context):
    try:
        context.registerClass(  COREBlog,
                                meta_type="COREBlog",
                                constructors = (
                                    manage_addCOREBlogForm,
                                    manage_addCOREBlog,
                                    getElementGroups, getElementNames
                                )
                             )
    except:
        context.registerClass(  COREBlog,
                                meta_type="COREBlog",
                                constructors = (
                                    manage_addCOREBlogForm,
                                    manage_addCOREBlog
                                )
                             )

misc_={'coreblog_img':ImageFile('www/coreblog-icon.gif',globals()),
       'entry_img':ImageFile('www/entry.gif',globals()),
       'comment_img':ImageFile('www/comment.gif',globals()),
       'trackback_img':ImageFile('www/trackback.gif',globals()),
       }

