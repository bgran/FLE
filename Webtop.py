# $Id: Webtop.py,v 1.40 2003/06/13 07:57:11 jmp Exp $
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

"""Contains class Webtop, which is the root object for users' webtops."""

__version__ = "$Revision: 1.40 $"[11:-2]

import Globals
#from Globals import Persistent, HTMLFile
import AccessControl
import re

from common import reload_dtml, add_dtml
#import TraversableWrapper
import WebtopFolder
import WebtopTrash
from TraversableWrapper import TWFolder
from common import perm_view, perm_edit, perm_manage, perm_add_lo

# This object is the root of a user's webtop and should reside inside
# the UserInfo object of the user.
#
# A webtop contains a clipboard folder, a trash folder and any
# WebtopItems the user has created. WebtopItem is a superclass, and
# actually the webtop will contain specific subclass instances, like
# WebtopFolder, WebtopFile, WebtopLink and WebtopMemo.
#
class Webtop(
    WebtopFolder.WebtopFolder,
    ):
    """User's Webtop."""
    meta_type = "Webtop"

    dtml_files = (
        ('index_html'       , 'Index page'    , 'ui/Webtop/index_html'),
        ('wt_add_folder'    , 'Webtop folder' , 'ui/Webtop/wt_add_folder'),
        ('wt_upload'        , 'Upload file'   , 'ui/Webtop/wt_upload'),
        ('wt_add_link'      , 'Add link'      , 'ui/Webtop/wt_add_link'),
        ('wt_add_memo'      , 'Add memo'      , 'ui/Webtop/wt_add_memo'),
        ('wt_view_memo'     , 'View memo'     , 'ui/Webtop/wt_view_memo'),
        ('wt_rename'        , 'Rename'        , 'ui/Webtop/wt_rename'),
        ('wt_preferences'   , 'Preferences'   , 'ui/Webtop/wt_preferences'),
        ('wt_search'        , 'Search'        , 'ui/Webtop/wt_search'),
        ('wt_search_results', 'Search Results', 'ui/Webtop/wt_search_results'),

        ('fle_html_header', '', 'ui/Webtop/fle_html_header'),
        ('fle_form_header', '', 'ui/Webtop/fle_form_header'),
        )

    security = AccessControl.ClassSecurityInfo()
    def __init__(self):
        """Construct the webtop root object."""
        self.__id_counter = 0L
        self.toplevel=1
        for tup in self.dtml_files:
            add_dtml(self, tup)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """Create trash and clipboard and call superclass
        initialization code."""
        WebtopFolder.WebtopFolder.__init__(self, None, 'webtop')
        self.id = 'webtop'
        WebtopFolder.WebtopFolder.manage_afterAdd(self, item, container)
        self._setObject('trash', WebtopTrash.WebtopTrash())
        self._setObject('clipboard', TWFolder())

        from common import roles_admin, roles_staff, roles_user

        self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_admin+('Owner',), 0)
        self.manage_permission(perm_view, roles_user, 0)

        # We don't want to Webtops to show in search results, just
        # objects inside them...
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
        return "wt"+str(self.__id_counter)

    security.declarePrivate('get_clipboard')
    def get_clipboard(self):
        """Returns a reference to the clipboard."""
        return self.clipboard

    security.declareProtected(perm_view, 'is_quota_limit_reached')
    def is_quota_limit_reached(self):
        """Is quota limit reached?"""
        limit = self.get_quota()
        if limit < 0:
            return 0 # no quota
        else:
            return self.get_size() >= limit

    # Note: unlike get_size() of WebtopFolder, this includes WebtopTrash too.
    security.declareProtected(perm_view, 'get_size')
    def get_size(self):
        """Return size of the object."""
        size = 0

        for o in self.objectValues(
            ('WebtopTrash', 'WebtopFolder',
             'WebtopLink', 'WebtopMemo', 'WebtopFile')):
            size += o.get_size()

        return size

    security.declareProtected(perm_view, 'search_form_handler')
    def search_form_handler(
        self,
        REQUEST,
        cancel=None, # submit buttons
        submit=None, #
        ):
        """Search form handler."""

        if submit:
            for s in 'get_name', 'get_content':
                REQUEST.set(s, REQUEST[s])

            if REQUEST['get_author_name'] == '___anyone___':
                uname = str(self.REQUEST.AUTHENTICATED_USER)
                if len(self.fle_users.get_user_info(uname).user_courses()) > 0:
                    REQUEST.set('get_author_name',
                                self.courses.get_unames_on_my_courses(REQUEST))
                else:
                    REQUEST.set('get_author_name', uname)
            else:
                REQUEST.set('get_author_name', REQUEST['get_author_name'])
            return self.wt_search_results(self, REQUEST)
        elif cancel:
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))
        else:
            raise 'FLE Error', 'Unknown button'

    # We don't want to display GroupFolderProxy objects that are
    # located on other users' webtops.
    def ok_to_display_search_result(self, REQUEST, fixed_url, meta_type):
        """Return whether to display search result (specified by
        fixed_url and meta_type)."""
        if (fixed_url == ''): return 0

        uname = str(self.REQUEST.AUTHENTICATED_USER)
        if uname == re.search('fle_users/(.*?)/', fixed_url).group(1):
            return 1

        if meta_type == 'GroupFolderProxy': return 0

        obj = self.get_object_of_url(fixed_url, self)
        while obj.meta_type != 'FLE':
            if obj.meta_type == 'GroupFolderProxy':
                return 0
            obj = obj.parent()
        return 1

    # Objects are really in the GroupFolder, but we want to return
    # URLs to objects inside GroupFolderProxy in the user's webtop.
    # So we do the mapping here...
    security.declareProtected(perm_view, 'get_fixed_urls')
    def get_fixed_urls(self, REQUEST,
                       url,
                       view_url,
                       context_url,
                       meta_type,
                       ):
        """Return a tuple (fixed_view_url, fixed_context_url)"""
        if url.find('/courses') == -1:
            # We are not inside course folder, nothing to fix!
            return view_url, context_url

        course_id = re.search("/courses/([^/]*)", url).group(1)
        uname = str(self.REQUEST.AUTHENTICATED_USER)

        # Find proxy for course's group folder.
        proxy_url = self.__url_to_proxy(self.fle_users.get_user_info(uname).get_webtop(), course_id)
        if not proxy_url:
            # Object is in the GroupFolder but the user's Webtop does not have
            # a GroupFolderProxy for that GroupFolder: return empty strings
            # to signal that we don't want to display this search result.
            return '', ''

        if meta_type == 'WebtopLink':
            return view_url, proxy_url
        if meta_type == 'GroupFolder':
            return proxy_url, proxy_url[:proxy_url.rfind('/')]
        else:
            return proxy_url + '/' + view_url[view_url.find('/gf/')+4:], \
                   proxy_url

    def __url_to_proxy(self, ob, course_id):
        # Is right GroupFolderProxy in this folder?
        for proxy in ob.get_children('GroupFolderProxy'):
            if proxy.get_course_this_belongs_to().get_id() == course_id:
                return proxy.absolute_url()

        # If not, search recursively in subfolders.
        for folder in ob.get_children('WebtopFolder'):
            url = self.__url_to_proxy(folder, course_id)
            if url: return url

        return None

Globals.InitializeClass(Webtop)

# EOF
