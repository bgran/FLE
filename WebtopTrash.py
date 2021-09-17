# $Id: WebtopTrash.py,v 1.29 2003/06/13 07:57:12 jmp Exp $
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

"""Contains class WebtopTrash, which is used to access all trashed
objects in a user's webtop and to manipulate them."""

__version__ = "$Revision: 1.29 $"[11:-2]

import Globals
from common import reload_dtml, add_dtml
from WebtopItem import WebtopItem
from WebtopLink import WebtopLink
from Cruft import Cruft
import TraversableWrapper
import OFS
import types
from common import perm_view, perm_edit, perm_manage, perm_add_lo
from AccessControl import ClassSecurityInfo

# Trashed objects are not stored in WebtopTrash, but inside
# their respective folders, inside a TWFolder named "tmp_objects".
# WebtopTrash uses recursive calls to access these trashed objects.
class WebtopTrash(
    Globals.Persistent,
    OFS.SimpleItem.Item,
    TraversableWrapper.Traversable,
    Cruft
    ):
    """A trash folder in a  Webtop. Each Webtop contains exactly
    one WebtopTrash folder."""
    meta_type = "WebtopTrash"

    security = ClassSecurityInfo()

    def __init__(self, id_='trash'):
        """Construct the webtop trash object."""
        self.id=id_

    security.declareProtected(perm_view, 'has_content')
    def has_content(self):
        """Any WebtopItems inside trash?"""
        return len(self.list_contents()) > 0

    # NB. criteria added to make WebtopTrash.list_contents work like
    # NB. WebtopFolder.list_contents.
    security.declareProtected(perm_view,'list_contents')
    def list_contents(self, criteria=None):
        """List contents."""

        if self.parent().meta_type == 'GroupFolderProxy':
            return self.parent().get_trash().list_contents()
        else:
            return self._list_contents(self.parent())

    def _list_contents(self, item):
        retval = []

        if hasattr(item, 'get_tmp_object_real_ids'):
            retval += item.get_tmp_objects()

        for e in item.objectValues(('WebtopFolder', 'GroupFolder',
                                    'GroupFolderProxy')):
            retval += self._list_contents(e)

        return retval

    security.declareProtected(perm_edit,'form_handler')
    def form_handler(self, item_ids=None, empty_trash='', restore='',
                     REQUEST=None):
        """Handle the trashcan form: removal and restoration of items."""
        if type(item_ids) is types.StringType:
            item_ids=(item_ids,)

        if not empty_trash and not item_ids:
            self.get_lang(('common','webtop'),REQUEST)
            return self.message_dialog_error(
                self, REQUEST,
                title=REQUEST['L_no_item_selected'],
                message=REQUEST['L_select_item_first_common'],
                action='index_html')

        if self.parent().meta_type == 'GroupFolderProxy':
            trash = self.parent().get_trash()
        else:
            trash = self

        if empty_trash:
            item_ids = \
                     [o.get_id() for o in \
                      filter(lambda o, user = str(REQUEST.AUTHENTICATED_USER):
                             o.may_edit(user), trash.list_contents())]
        objs = []
        for item_id in item_ids:
            obj = trash.aq_parent.find_object_by_id(item_id)
            if not obj:
                raise 'Object with id '+item_id+' not found in subtree!'
            objs.append(obj)

        if restore:
            self.restore(objs)
        elif empty_trash:
            self.remove(objs)
        else:
            raise 'FLE Error', 'Unknown button'

        if REQUEST:
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))

    security.declarePrivate('remove')
    def remove(self,items):
        """Permanently remove selected item(s) from trash."""
        for item in items:
            item.delete_me()

    security.declareProtected(perm_view,'get_name')
    def get_name(self):
        """Returns the name of the trash."""
        return self.id

    security.declarePrivate('restore')
    def restore(self,items):
        """Recover the selected items."""
        for obj in items:
            # Move from selected object to its parent's parent.
            # (containment: folder, tmp_objects, obj)
            # So we move to 'folder' that is (hopefully)
            # a TempObjectManager.
            obj.aq_parent.aq_parent.move_from_tmp(obj)

    # This method added only for quota functionality of Webtops.
    # I have not even thought how this would behave if called
    # for WebTrash objects inside GroupFolders.
    security.declarePrivate('get_size')
    def get_size(self):
        """Return size of the object."""
        size = 0
        for o in self._list_contents(self):
            size += o.get_size()
        return size

Globals.InitializeClass(WebtopTrash)
# EOF
