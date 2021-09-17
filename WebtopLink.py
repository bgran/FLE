# $Id: WebtopLink.py,v 1.30 2003/06/17 12:37:49 tarmo Exp $
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

"""Contains class WebtopLink, which represents a URL stored in a user's webtop."""

__version__ = "$Revision: 1.30 $"[11:-2]

from urllib import quote
from common import reload_dtml, add_dtml, intersect_bool
from WebtopItem import WebtopItem
from Cruft import Cruft # for find_URL_of_fle_root()
from AccessControl import ClassSecurityInfo
from AccessControl.PermissionRole import rolesForPermissionOn
import OFS
#from Globals import Persistent, HTMLFile
import Globals
from common import perm_view, perm_edit, perm_manage, perm_add_lo, \
     get_roles, course_level_roles

class WebtopLink(
    WebtopItem,OFS.SimpleItem.Item,
    Globals.Persistent,
    Cruft):
    """A link in a Webtop."""
    meta_type = "WebtopLink"

    security = ClassSecurityInfo()

    def __init__(self, parent, name, url_or_obj, internal=0):
        """Construct the webtop link object, either to a URL or
        to another ZObject."""
        WebtopItem.__init__(self,parent,name)
        self.__is_internal=internal
        if internal:
            if type(url_or_obj)!=type(''):
                url_or_obj = self.get_url_to_object(url_or_obj)
            if url_or_obj.find('jamming') >= 0:
                self.set_icon('images/type_link_jm')
            # FIXME: This won't work if there can be links to Course Management
            # FIXME: We should really move KB down to same level as Jamming.
            elif url_or_obj.find('courses') >= 0:
                self.set_icon('images/type_link_kb')
            else:
                self.set_icon('images/type_link')
        else:
            try:
                # Encode special chars in url.
                #a, b = url_or_obj.split('://')
                #b = quote(b,'/')
                #b = b.replace(' ', '%20')
                #url_or_obj = a + '://' + b
                url_or_obj=url_or_obj.replace(' ','%20')
            except ValueError:
                pass

            self.set_icon('images/type_external')

        self.__url=url_or_obj

    security.declareProtected(perm_view,'get_list_item_name')
    def get_list_item_name(self, REQUEST=None):
        """Overrides WebtopItem method to notify of an inaccessible object."""
        name = WebtopItem.get_name(self)
        if self.is_internal_link():
            object = self.get_obj_ref()
            if not object:
                if REQUEST:
                    self.get_lang(('common','webtop'),REQUEST)
                    name = name+" %s" % REQUEST['L_obj_removed']
        return name

    security.declarePrivate('get_obj')
    def get_obj_ref(self):
        if not self.__is_internal:
            return None
        try:
            return self.get_object_of_url(self.__url, self)
        except:
            # This will cause all failures in locating the link object
            # to finish quietly.
            return None

    security.declareProtected(perm_view, 'get_url')
    def get_url(self):
        """Returns the url contained in the link."""
        return self.__url

    # for ZCatalog
    security.declarePrivate('get_content')
    def get_content(self):
        """Return content (url)of the link."""
        return self.get_url()

    security.declareProtected(perm_view, 'get_view_url')
    def get_view_url(self):
        """Return URL that shows the object."""
        return self.get_url()

    security.declareProtected(perm_view, 'is_internal_link')
    def is_internal_link(self, REQUEST=None):
        """Return whether URL points inside FLE"""
        return self.__is_internal

    security.declareProtected(perm_view, 'may_follow_link')
    def may_follow_link(self, REQUEST):
        """Return whether current user has view access
        to place pointed by link."""
        if not self.is_internal_link(): return 1

        object = self.get_obj_ref()
        if not object:
            return 0
        # Figure out which roles user has on a course
        person = str(REQUEST.AUTHENTICATED_USER)
        actual_roles = get_roles(object,person)
        valid_roles = course_level_roles
        return intersect_bool(actual_roles, valid_roles)

    security.declareProtected(perm_view, 'get_size')
    def get_size(self):
        """Return size of the object."""
        return len(self.__url)

Globals.InitializeClass(WebtopLink)
# EOF

