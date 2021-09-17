# $Id: WebtopItem.py,v 1.38 2003/06/13 07:57:12 jmp Exp $
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

"""Contains class WebtopItem, which contains common methods that are inherited to all specific webtop items."""

__version__ = "$Revision: 1.38 $"[11:-2]

#from Globals import Persistent, HTMLFile
import AccessControl
import Globals
import OFS
from AccessControl import ClassSecurityInfo
from Products.ZCatalog.CatalogAwareness import CatalogAware

import time

from common import reload_dtml, add_dtml
import TraversableWrapper
#from UserInfo import UserInf
from common import perm_view, perm_edit, perm_manage, perm_add_lo, \
     get_local_roles, get_roles

class WebtopItem(
    CatalogAware,
    TraversableWrapper.Traversable,
    AccessControl.Role.RoleManager,
    Globals.Persistent,
    #OFS.SimpleItem.Item,
    #OFS.Folder.Folder
    ):
    """A generic Webtop item. This is an 'abstract' class and should not
    be used directly. Instantiate a WebtopFile, WebtopFolder,
    WebtopLink or WebtopMemo instead."""
    meta_type = "WebtopItem"
    security = ClassSecurityInfo()

    def __init__(self, parent, name):
        """Construct the webtop item object.
        NOTE: This constructor must be called from the subclass's constructor."""
        self.default_catalog = 'catalog_webtop_items'

        if parent:
            self.id = parent.generate_id()
        else:
            self.id = 'wt0'
        self.set_name(name)
        self.set_icon('images/doc_small')
        self.do_stamp()

##     security.declarePrivate('manage_afterAdd')
##     def manage_afterAdd(self,item,container):
##         from common import roles_admin, roles_teacher, roles_student

##         self.manage_permission(perm_manage, roles_admin, 0)
##         self.manage_permission(perm_edit, roles_teacher+('Owner',), 0)
##         self.manage_permission(perm_view, roles_student, 0)

##     security.declarePrivate('manage_afterAdd')
##     def manage_afterAdd(self,item,container):
##         """FIXME: It may be that this is not
##         needed anymore when WebtopItem is CatalogAware"""
##         if not hasattr(self,'REQUEST'):
##             from common import FakeRequest
##             self.REQUEST=FakeRequest()
##         CatalogAware.manage_afterAdd(self, item, container)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self,item,container):
        """..."""
        # Check if we're being added inside a Webtop (not inside a GroupFolder)
        # and if our owner differs from the webtop owner, change ownership
        import Webtop
        import GroupFolderProxy
        ob=self.parent()
        while 1:
            if isinstance(ob,Webtop.Webtop):
                #raise 'foo',"YES, it's a webtop!"
                if self.get_author_name() != ob.parent().get_uname():
                    self.set_author(ob.parent().get_uname())
            elif isinstance(ob,GroupFolderProxy.GroupFolderProxy):
                break
            try:
                ob=ob.parent()
            except:
                break

        # Index into ZCatalog (unless object is inside WebtopTrash)
        if not isinstance(container, TraversableWrapper.TWFolder):
            self.index_object()


##    def manage_beforeDelete(self, item, container):
##        """Remove WebtopItem from ZCatalog's index."""
##        self.unindex_object()

    security.declareProtected(perm_view, 'get_view_url')
    def get_view_url(self):
        """Return URL that shows the object."""
        # This is OK in most cases, but you have override this sometimes...
        return self.absolute_url()

    security.declareProtected(perm_view, 'get_context_url')
    def get_context_url(self):
        """Return URL that shoes the object in a context (currently it
        is always the URL of parent folder..."""
        return self.absolute_url()[:self.absolute_url().rindex('/')] + '/'

    security.declareProtected(perm_view,'get_timestamp')
    def get_timestamp(self):
        """Return timestamp in time.time() format."""
        return self.__timestamp

    security.declarePrivate('set_timestamp')
    def set_timestamp(self,time):
        """Set timestamp to new value."""
        self.__timestamp=time

    security.declarePrivate('do_stamp')
    def do_stamp(self):
        """Set timestamp to current time."""
        self.__timestamp = time.time()

    security.declarePrivate('set_icon')
    def set_icon(self, img):
        """Sets the icon path for this webtop item."""
        self.iconpath=img

    security.declareProtected(perm_view,'get_icon')
    def get_icon(self):
        """Returns the icon object for the path stored in this item."""
        try:
            return self.unrestrictedTraverse(self.iconpath)
        except KeyError:
            return None

    # For ZCatalog
    security.declarePrivate(perm_view, 'get_icon_path')
    def get_icon_path(self):
        """Return icon path."""
        return self.iconpath

    security.declareProtected(perm_view,'get_list_item_name')
    def get_list_item_name(self, REQUEST=None):
        """Returns the displayable string to be used when
        the item is shown in a folder contents list."""
        return self.get_name()

    security.declareProtected(perm_view,'get_name')
    def get_name(self):
        """Returns the name of this item."""
        return self.title

    security.declarePrivate('set_name')
    def set_name(self,newname):
        """Changes the name of this item."""
        self.title=newname

    security.declareProtected(perm_view, 'get_author')
    def get_author(self):
        """Return author (owner) of this item."""
        return self.getOwner()

    security.declareProtected(perm_view, 'get_author_name')
    def get_author_name(self):
        """Return name of the author (owner) of this item."""
        owner = self.getOwner()
        if not owner:
            return ''
        return owner.name

    security.declarePrivate('set_author')
    def set_author(self,author):
        """Set the author (owner) of this item."""
        self.manage_setLocalRoles(author,('Owner',))
        self.changeOwnership(self.acl_users.getUser(author).__of__(self.acl_users))

    security.declarePrivate('get_content')
    def get_content(self):
        """This must be overridden in inherited class"""
        raise 'FLE Error', 'method get_content() not implemented.'

    security.declareProtected(perm_view,'get_size')
    def get_size(self):
        """Return size (in bytes) of the WebTop item.
        this must be overridden in inherited class."""

        raise 'FLE Error', 'method get_size() not implemented.'

    security.declareProtected(perm_view,'get_printable_size')
    def get_printable_size(self, REQUEST):
        """Return pritable size: scaled size + unit."""

        self.get_lang(('common',),REQUEST)
        size = self.get_size()

        if size >= 1024*1024:
            size = size / (1024.0 * 1024)
            retval = str(round(size, 1)) + ' ' + REQUEST['L_megabyte']
        elif size >= 1024:
            size = size / 1024.0
            retval = str(round(size, 1)) + ' ' + REQUEST['L_kilobyte']
        else:
            # Why don't we return the real size of small objects?
            retval = '1 ' + REQUEST['L_kilobyte']

        return retval

    def may_edit(self,uname):
        """Returns whether user may edit this object or not."""
##         raise 'foo',str(self.get_local_roles()) + " vs. " + str(get_local_roles(self,uname)) + " with " + uname
##         raise 'foo',self.get_name() + str(get_local_roles(self,uname))
        if 'Owner' in get_local_roles(self,uname):
            return 1
        if 'Teacher' in get_roles(self,uname):
            return 1
        return 0
##         from AccessControl.PermissionRole import rolesForPermissionOn
##         return intersect_bool(
##             get_roles(obj,uname),
##             rolesForPermissionOn(perm_edit,obj))

Globals.InitializeClass(WebtopItem)
# EOF
