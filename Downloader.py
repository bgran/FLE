# $Id: Downloader.py,v 1.3 2004/09/15 18:05:08 tarmo Exp $
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

"""
This class enable the use of clean urls, with convenient
file names at the end, with the actual downloadable resource
as a parameter. Makes downloading files to stupid browsers
easier.
"""

__version__ = "$Revision: 1.3 $"[11:-2]

import os.path, string, time

import Globals
import AccessControl
import OFS
from OFS.Folder import Folder
from Cruft import Cruft

# This is the class for the FLE installation root object.
class Downloader(
    Folder,
    Cruft,
    OFS.SimpleItem.Item,
    ):
    """Download assistant."""
    security = AccessControl.ClassSecurityInfo()
    security.declareObjectPublic()

    def __bobo_traverse__(self, REQUEST, entry_name=None):
        return self

    def __call__(self,client=None,REQUEST={},RESPONSE=None, **kw):
        #raise 'foo2','CALL CALLED: ' + str(REQUEST)
        srcurl=REQUEST.get('src')
        #raise 'foo',srcurl
        obj=self.get_object_of_url(srcurl,self)
        path=srcurl.split('/')
        fname=path.pop()
        if fname=='':
            return obj.index_html(REQUEST,RESPONSE)
        else:
            try:
                return apply(getattr(obj,fname),(REQUEST,))
            except TypeError:
                return apply(getattr(obj,fname),(REQUEST,RESPONSE))

Globals.InitializeClass(Downloader)

# EOF
