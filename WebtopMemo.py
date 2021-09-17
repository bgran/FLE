# $Id: WebtopMemo.py,v 1.24 2003/06/13 07:57:12 jmp Exp $
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

"""Contains class WebtopMemo, which represents an editable memo or note in a user's webtop."""

__version__ = "$Revision: 1.24 $"[11:-2]

from common import reload_dtml, add_dtml
from WebtopItem import WebtopItem
import OFS
#from Globals import Persistent, HTMLFile
import Globals
from AccessControl import ClassSecurityInfo
import re
from common import perm_view, perm_edit, perm_manage, perm_add_lo

class WebtopMemo(WebtopItem,
                 OFS.SimpleItem.Item,
                 ):
    """An editable memo in a Webtop."""
    meta_type = "WebtopMemo"

    security = ClassSecurityInfo()

    def __init__(self, parent, name, contents):
        """Construct the webtop memo object."""
        WebtopItem.__init__(self,parent,name)
        self.set_icon('images/type_memo')
        self.__contents=contents

    security.declareProtected(perm_view, 'get_body')
    def get_body(self, REQUEST=None):
        """Returns the contents of the memo as a string."""
        if REQUEST:
            REQUEST.RESPONSE.setHeader('content-type',
                                       'text/plain; charset=utf-8')
        return self.__contents

    security.declarePrivate('set_body')
    def set_body(self,contents):
        if contents != self.__contents:
            self.__contents = contents
            self.do_stamp()

    # for ZCatalog
    security.declarePrivate('get_content')
    def get_content(self):
        """Return content of the memo"""
        return self.__contents

    security.declareProtected(perm_view, 'get_view_url')
    def get_view_url(self):
        """Return URL that shows the object."""
        return self.absolute_url() + '/wt_view_memo'

    security.declareProtected(perm_edit, 'add_memo_handler')
    def add_memo_handler(self,REQUEST, contents, submit='', cancel=''):
        """Handles the input from memo editing."""
        if submit:
            from common import get_local_roles
            roles = get_local_roles(self,str(REQUEST.AUTHENTICATED_USER))
            if 'Owner' in roles or 'Teacher' in roles:
                self.set_body(contents)
        REQUEST.RESPONSE.redirect(self.state_href(REQUEST,'../index_html'))

    security.declareProtected(perm_view, 'render_contents')
    def render_contents(self):
        """Memo can contain arbitrary html tags and is rendered with
        both vertical and horizontal space respect on, unless a tag
        of P or BR is used."""
        from input_checks import render

        return render(
            self.__contents,
            do_strip=0,
            do_horizontal_space=1)


    security.declareProtected(perm_view, 'get_size')
    def get_size(self):
        """Return size of the object."""
        return len(self.__contents)

Globals.InitializeClass(WebtopMemo)
# EOF

