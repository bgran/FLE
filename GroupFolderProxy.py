# $Id: GroupFolderProxy.py,v 1.19 2003/06/13 07:57:11 jmp Exp $
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

"""Contains class WebTopGroupFolderProxy."""

import Globals
import AccessControl
from common import course_level_roles
from common import reload_dtml, add_dtml
import Webtop
import WebtopFolder
from WebtopItem import WebtopItem
from common import perm_view, perm_edit, perm_manage, perm_add_lo

class GroupFolderProxy(
    WebtopFolder.WebtopFolder,
    ):
    """GroupFolderProxy"""
    meta_type = "GroupFolderProxy"

    dtml_files = (
        ('index_html'   , 'Index page'   , 'ui/GroupFolder/index_html'),
	('maptool', 'Maptool launcher', 'ui/Course/maptool'),

        # ('fle_html_header', '', 'ui/Webtop/fle_html_header'),
        # ('fle_form_header', '', 'ui/Webtop/fle_form_header'),
        )

    security = AccessControl.ClassSecurityInfo()

    def __init__(self, parent, name, course_id):
        """Construct GroupFolderProxy"""
        self.__course_id = course_id

        WebtopItem.__init__(self, parent, name)
        self.set_icon('images/group_folder')
        for tup in self.dtml_files:
            add_dtml(self, tup)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self,item,container):
        """..."""
        WebtopFolder.WebtopFolder.manage_afterAdd(self, item, container)

        for role in course_level_roles:
            self._addRole(role)

        from common import roles_admin, roles_staff, roles_user
        from common import roles_student, roles_tutor, roles_teacher

        self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_student, 0)
        self.manage_permission(perm_view, roles_student, 0)

        # We want to index only those GroupFolderProxy objects
        # that are in Webtops.
        if not (isinstance(container, Webtop.Webtop) or
                isinstance(container, WebtopFolder.WebtopFolder)):
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
        return self.__get_group_folder().generate_id()

    security.declareProtected(perm_view, 'get_list_item_name')
    def get_list_item_name(self, REQUEST=None):
        """Return the name of Groupfolder."""
        if REQUEST:
            uname = str(REQUEST.AUTHENTICATED_USER)
            language = self.fle_users.get_child(uname).get_language()
        else:
            language = 'en'

        d = {}
        self.get_lang_given(('webtop',), d, language)
        return self.get_name() + ' (' + d['L_shared_course_folder'] + ')'

    security.declareProtected(perm_view, 'get_trash')
    def get_trash(self):
        """Return trash (an instance of WebtopTrash)"""
        return self.__get_group_folder().get_trash()

    security.declarePrivate('get_clipboard')
    def get_clipboard(self):
        return self.__get_group_folder().get_clipboard()


    security.declareProtected(perm_view, 'has_content')
    def has_content(self):
        """Any WebtopItems in this folder?"""
        return self.__get_group_folder().has_content()

    security.declareProtected(perm_view, 'list_contents')
    def list_contents(self, criteria=''):
        """Returns a list of all different WebtopItems in this folder."""
        return self.__get_group_folder().list_contents(criteria)

    security.declareProtected(perm_edit, 'add_folder_handler')
    def add_folder_handler(
        self, REQUEST, my_name,
        submit = '', # form buttons
        cancel = '', #
        ):
        """Handles the input from folder add form."""
        return self.__get_group_folder().add_folder_handler(
            REQUEST, my_name, submit, cancel)

    security.declareProtected(perm_edit, 'add_link_handler')
    def add_link_handler(
        self, REQUEST, my_name, url,
        type = '',
        submit = '', # form buttons
        cancel = '', #
        back_link = '', # 'add link to webtop' feature outside webtop
        ):
        """Handles the input from link add form."""

        return self.__get_group_folder().add_link_handler(
            REQUEST, my_name, url, type, submit, cancel, back_link)

    security.declareProtected(perm_edit, 'add_file_handler')
    def add_file_handler(
        self, REQUEST, my_name, file=None,
        key = '',
        submit = '', # form buttons
        cancel = '', #
        ):
        """Handles the input from upload form."""

        return self.__get_group_folder().add_file_handler(
            REQUEST, my_name, file, key, submit, cancel)

    security.declareProtected(perm_edit, 'add_memo_handler')
    def add_memo_handler(
        self,
        REQUEST,
        my_name,
        contents,
        submit='',
        cancel=''):
        """Handles the input from memo add form."""

        return self.__get_group_folder().add_memo_handler(
            REQUEST, my_name, contents, submit, cancel)

    security.declareProtected(perm_edit, 'form_handler')
    def form_handler(
        self,
        item_ids=None,
        copy='', cut='', paste='',           # submit buttons
        remove='', rename='', select_all='', #
        REQUEST=None):
        """Handles the input from folder default form:
        item copy/cut/paste, remove and rename operations."""

        return self.__get_group_folder().form_handler(
            item_ids, copy, cut, paste, remove, rename, select_all, REQUEST)

    security.declareProtected(perm_edit, 'rename_helper')
    def rename_helper(self, expr1, expr2=None):
        """Helper function for DTML method wt_rename.dtml"""
        return self.__get_group_folder().rename_helper(expr1, expr2)

    security.declareProtected(perm_view, 'is_clipboard_empty')
    def is_clipboard_empty(self):
        """Is clipboard empty?"""
        return self.__get_group_folder().is_clipboard_empty()

    security.declareProtected(perm_edit, 'rename_handler')
    def rename_handler(
        self, REQUEST,
        item_id_list,
        new_name_list,
        submit = '', # form buttons
        cancel = '', #
        ):
        """Handles rename_form submission."""

        return self.__get_group_folder().rename_handler(
            REQUEST, item_id_list, new_name_list, submit, cancel)

    security.declareProtected(perm_view, 'get_size')
    def get_size(self):
        """Return size of the object."""
        return self.__get_group_folder().get_size()

    security.declarePublic('get_child')
    def get_child(self, _id):
        """Override get_child() of TraversableWrapper."""
        return self.__get_group_folder().get_child(_id)

    def is_proxy_for(self, group_folder):
        return self.__get_group_folder() == group_folder

    security.declarePublic('get_course_this_belongs_to')
    def get_course_this_belongs_to(self):
        """Return the course to which the actual group folder belongs to."""
        return self.courses.get_child(self.__course_id)

    def __get_group_folder(self):
        return self.courses.get_child(self.__course_id).gf

    def __bobo_traverse__(self, REQUEST, entry_name=None):
        if entry_name[:2] == 'gf' or entry_name == 'trash':
            ob = getattr(self.__get_group_folder(), entry_name).aq_base
            return ob.__of__(self)
        else:
            return getattr(self, entry_name)

    # Called from get_object_of_url (defined in Cruft.py)
    security.declarePrivate('lame_getattr_emulation')
    def lame_getattr_emulation(self, entry_name):
        if entry_name[:2] == 'gf' or entry_name == 'trash':
            return getattr(self.__get_group_folder(), entry_name).aq_base
        else:
            return getattr(self, entry_name)


Globals.InitializeClass(GroupFolderProxy)


#EOF
