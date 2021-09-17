# $Id: GroupFolder.py,v 1.12 2003/06/13 07:57:11 jmp Exp $
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

"""Contains class GroupFolder, which is the root object for group folders
in Knowledge Building."""

__version__ = "$Revision: 1.12 $"[11:-2]

import Globals
#from Globals import Persistent, HTMLFile
import AccessControl

from common import reload_dtml, add_dtml
#import TraversableWrapper
import WebtopFolder
import WebtopTrash
from WebtopItem import WebtopItem
from TraversableWrapper import TWFolder
from TempObjectManager import TempObjectManager
from common import perm_view, perm_edit, perm_manage, perm_add_lo

# This object is the root of a group folder inside a Course or
# a CourseContext.
#
# A group folder contains a trash folder and any
# WebtopItems the users have created. WebtopItem is a superclass, and
# actually the group folder will contain specific subclass instances, like
# WebtopFolder, WebtopFile, WebtopLink and WebtopMemo.
#
class GroupFolder(
    WebtopFolder.WebtopFolder,
    ):
    """Group folder."""
    meta_type = "GroupFolder"

    list_of_types=('WebtopFolder', 'WebtopLink', 'WebtopMemo', 'WebtopFile')

    dtml_files = (
        ('index_html'   , 'Index page'   , 'ui/GroupFolder/index_html'),

        #('fle_html_header', '', 'ui/GroupFolder/fle_html_header'),
        #('fle_form_header', '', 'ui/GroupFolder/fle_form_header'),
        )

    security = AccessControl.ClassSecurityInfo()
    def __init__(self,parent,name):
        """Construct the group folder root object."""
        WebtopItem.__init__(self,parent,name)
        TempObjectManager.__init__(self)
        self.id = 'gf' + self.id[2:]
        self.__id_counter = long(self.id[2:])
        self.set_icon('images/group_folder')
        for tup in self.dtml_files:
            add_dtml(self, tup)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """Create trash and clipboard and call superclass
        initialization code."""
        WebtopFolder.WebtopFolder.manage_afterAdd(self, item, container)

        if hasattr(self.parent().aq_base,'toplevel'):
            self._setObject('trash', WebtopTrash.WebtopTrash())

        from common import roles_admin, roles_staff, roles_user
        from common import roles_student, roles_tutor, roles_teacher

        self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_student, 0)
        self.manage_permission(perm_view, roles_student, 0)

        # We don't want to index GroupFolder objects.
        self.unindex_object()

    security.declareProtected(perm_manage, 'reload_dtml')
    # No additional comments.
    def reload_dtml(self, REQUEST=None):
        """Reload dtml file from the file system."""
        reload_dtml(self, self.dtml_files)
        if REQUEST:
            self.get_lang(('common',),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_dtml_reloaded'],
                message=REQUEST['L_dtml_files_reloaded'],
                action='index_html')

    security.declarePrivate('generate_id')
    def generate_id(self):
        """Return a unique (within this webtop) id.
        These ids are used for any and all WebtopItems created
        instead of their visible names so we avoid any problems with
        visible name conflicts and can use more complex visible names
        for items."""

        self.__id_counter += 1L
        return "gf"+str(self.__id_counter)

    security.declareProtected(perm_view, 'get_list_item_name')
    def get_list_item_name(self, REQUEST=None):
        """Return the name of Groupfolder."""
        return self.get_name()

    def get_name(self):
        """Return the name of the course."""
        try:
            if hasattr(self.parent().aq_base, 'toplevel'):
                return self.parent().get_name()
        except AttributeError:
            pass
        return WebtopFolder.WebtopFolder.get_name(self)

##     security.declarePrivate('add_folder')
##     def add_folder(self,name):
##         """Implementation of add_folder_handler without http code."""
##         f = GroupFolder(self,name)
##         self._setObject(f.id,f)
##         return f

    security.declarePrivate('get_clipboard')
    def get_clipboard(self):
        uname=str(self.REQUEST.AUTHENTICATED_USER)
        return self.fle_users.get_user_info(uname).webtop.clipboard

    security.declareProtected(perm_view, 'get_trash')
    def get_trash(self):
        """Return trash (an instance of WebtopTrash)"""
        #raise 'foo',str(self.aq_chain)
        if hasattr(self.parent().aq_base, 'toplevel'):
            return self.get_child('trash')
        else:
            return self.parent().get_trash()

Globals.InitializeClass(GroupFolder)

# EOF
