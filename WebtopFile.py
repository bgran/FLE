# $Id: WebtopFile.py,v 1.14 2003/06/13 07:57:12 jmp Exp $
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

"""Contains class WebtopFile, which represents an uploaded (binary)
file in a user's webtop."""

__version__ = "$Revision: 1.14 $"[11:-2]

import Globals
from WebtopItem import WebtopItem
import OFS
from AccessControl import ClassSecurityInfo
from common import perm_view

class WebtopFile(WebtopItem, OFS.Image.File):
    """A file in a Webtop."""
    meta_type = "WebtopFile"

    security = ClassSecurityInfo()

    def __init__(self, parent, name, file):
        """Construct the webtop folder object."""
        WebtopItem.__init__(self,parent,name)
        OFS.Image.File.__init__(self, self.id, self.title, file)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self,item,container):
        content_type = self.getContentType()
        content_type_major = content_type[:content_type.find('/')]

        if content_type == 'text/html':
            self.set_icon('images/type_html')
        elif content_type_major == 'text':
            self.set_icon('images/type_doc')
        elif content_type_major == 'audio':
            self.set_icon('images/type_audio')
        elif content_type_major == 'image':
            self.set_icon('images/type_image')
        elif content_type_major == 'video':
            self.set_icon('images/type_video')
        else:
            self.set_icon('images/type_no')

        self.__content_type = content_type

        WebtopItem.manage_afterAdd(self, item, container)

    security.declarePrivate('get_content_type')
    def get_content_type(self):
        """Return content type of the file."""
        return self.__content_type

    # FIXME: As this function returns some content for catalog
    # FIXME: to index, we should do all possible conversions here
    # FIXME: (RTF -> ascii, PDF -> ascii, and so on ...)
    security.declarePrivate('get_content')
    def get_content(self):
        """Return content of the file."""
        return self.data

    security.declareProtected(perm_view, 'get_size')
    def get_size(self):
        """Return size of the object."""
        return self.getSize()

Globals.InitializeClass(WebtopFile)
# EOF
