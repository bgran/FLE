# $Id: JamSession.py,v 1.33 2003/06/13 07:57:11 jmp Exp $

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

"""Contains class JamSession, which is abstract base class for different
JamSession types."""

__version__ = '$Revision: 1.33 $'[11:-2]

from types import StringType
from urllib import quote_plus

import OFS, Globals, AccessControl
from Globals import Persistent
from AccessControl import ClassSecurityInfo

from JamArtefact import JamArtefact
from TraversableWrapper import TraversableWrapper

from input_checks import is_valid_title, strip_all, render, \
     normal_entry_tags_and_link
from common import reload_dtml, add_dtml, intersect_bool, make_action
from common import perm_view, perm_edit, perm_manage, perm_add_lo, \
     roles_admin, roles_staff, roles_user


class JamSession(
    TraversableWrapper,
    OFS.Folder.Folder,
    Persistent,
    AccessControl.Role.RoleManager,
    ):
    """JamSession"""

    meta_type = 'JamSession'

    security= ClassSecurityInfo()
    security.declareObjectPublic()

    dtml_files = (
        ('index_html', 'Index page', 'ui/JamSession/index_html'),
        ('add_artefact_form', '', 'ui/JamSession/add_artefact_form'),
        ('edit_jam_session_form' ,'Edit existing JamSession',
         'ui/JamSession/edit_jam_session_form'),
    )

    def __init__(self,
                 id_,
                 name,
                 description,
                 start_artefact_name,
                 start_artefact_data,
                 start_artefact_content_type,
                 author=None):
        """Construct JamSession."""
        self.id = id_
        self.title = ''
        self.__name = strip_all(name)
        self.__description = description

        # pass to manage_afterAdd
        self._t_name = start_artefact_name
        self._t_data = start_artefact_data
        self._t_ct = start_artefact_content_type
        self._t_author = author

        for tup in self.dtml_files:
            add_dtml(self, tup)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """Set default permissions for roles."""

        self.add_artefact(self._t_name, self._t_data, self._t_ct,
                          self._t_author)
        del self._t_name
        del self._t_data
        del self._t_ct
        del self._t_author

        self.update_drawing()

        from common import roles_student, roles_tutor, roles_teacher
        from common import roles_admin

        self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_teacher, 0)
        self.manage_permission(perm_add_lo, roles_student, 0)
        self.manage_permission(perm_view, roles_student, 0)

    security.declareProtected(perm_manage, 'reload_dtml')
    def reload_dtml(self, REQUEST=None):
        """Reload dtml files from the file system."""
        reload_dtml(self, self.dtml_files)
        if REQUEST:
            self.get_lang(('common',), REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_dtml_reloaded'],
                message=REQUEST['L_dtml_files_reloaded'],
                action='index_html')

    security.declareProtected(perm_view, 'get_name')
    def get_name(self):
        """Return name of the JamSession."""
        return self.__name

    security.declareProtected(perm_view, 'get_description')
    def get_description(self):
        """Return desctiption of the JamSession."""
        return self.__description

    security.declareProtected(perm_view, 'render_description')
    def render_description(self):
        """Render description."""
        return render(
            self.get_description(),
            do_vertical_space=0,
            legal_tags=normal_entry_tags_and_link)

    security.declarePrivate('uncache_artefacts')
    def uncache_artefacts(self):
        if hasattr(self,'__cached_n_artefacts'):
            del self.__cached_n_artefacts
        if hasattr(self,'__cached_n_unread_artefacts'):
            del self.__cached_n_unread_artefacts

    security.declareProtected(perm_view, 'get_n_artefacts')
    def get_n_artefacts(self):
        """Return number of artefacts in this JamSession"""
        if hasattr(self, '__cached_n_artefacts'):
            return self.__cached_n_artefacts
        else:
            n = len(self.get_children('JamArtefact'))
            self.__cached_n_artefacts = n
            return n

    security.declarePrivate('uncache_unread_artefacts')
    def uncache_unread_artefacts(self, uname):
        if hasattr(self, '__cached_n_unread_artefacts'):
            if uname in self.__cached_n_unread_artefacts.keys():
                del self.__cached_n_unread_artefacts.keys[uname]

    security.declareProtected(perm_view, 'get_n_unread_artefacts')
    def get_n_unread_artefacts(self, uname):
        """Return number of unread artefacts in this JamSession"""

        if hasattr(self, '__cached_n_unread_artefacts'):
            if uname in self.__cached_n_unread_artefacts.keys():
                return
        else:
            self.__cached_n_unread_artefacts = {}

        n = 0
        for a in self.get_children('JamArtefact'):
            if not a.is_reader(uname):
                n += 1

        self.__cached_n_unread_artefacts[uname] = n
        return n

    security.declareProtected(perm_view, 'get_starting_artefact_id')
    def get_starting_artefact_id(self):
        """Return ID of the starting artefact."""
        return self.__starting_artefact_id

    security.declareProtected(perm_view, 'render')
    # This is called from DTML, return a list of lists (DTML
    # constructs a table using that information.)
    def render(self):
        """Render JamSession."""
        return self.drawing

    security.declareProtected(perm_add_lo, 'add_artefact')
    def add_artefact(self, name, data, content_type, author, parent_ids=(),
                     REQUEST=None):
        """Add new artefact to JamSession."""
        #                 Jamming  Course   CourseManager
        #                   |       |        |
        id_ = 'ja' + self.parent().parent().parent().generate_id()

        if len(parent_ids) == 0:
            self.__starting_artefact_id = id_

        self._setObject(id_, JamArtefact(id_, parent_ids, name,
                                         data, content_type, author))
        ja = self.get_child(id_)
        if REQUEST: ja.update_reader(str(REQUEST.AUTHENTICATED_USER))
        return ja

    security.declareProtected(perm_add_lo, 'index_html_form_handler')
    def index_html_form_handler(
        self, REQUEST,
        parent_ids='invalid_id',
        ):
        """Redirect to add_artefact_form."""

        if parent_ids == 'invalid_id':
            self.get_lang(('common', ), REQUEST)
            return self.message_dialog_error(
                self, REQUEST,
                title=REQUEST['L_invalid_input'],
                message=REQUEST['L_select_item_first_common'],
                action='index_html')

        from types import StringType
        if type(parent_ids) == StringType:
            parent_ids = (parent_ids,)

        REQUEST.RESPONSE.redirect(
            self.state_href(REQUEST,
                            'add_artefact_form?parent_ids=%s' %
                            ','.join(parent_ids)
                            )
            )

    security.declareProtected(perm_edit, 'edit_form_handler')
    def edit_form_handler(
        self, REQUEST,
        my_name = '',
        description = None,
        cancel = '', # submit buttons
        save = '',   #
        remove = '', #
        ):
        """Edit form handler"""
        if cancel:
            pass
        elif save:
            self.get_lang(('common', 'jam'), REQUEST)

            error_fields = []

            my_name = my_name.strip()
            if not is_valid_title(my_name):
                error_fields.append(REQUEST['L_title_of_jam_session'])

            if not description:
                error_fields.append(REQUEST['L_description_of_jam_session'])

            if len(error_fields) > 0:
                msg = REQUEST['L_invalid_fields'] + ": '" + \
                      "' , '".join(error_fields) + "'"
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_input'],
                    message=msg,
                    action=apply(
                    make_action,
                    ['edit_jam_session_form'] +
                    [(x, eval(x)) for x in ('my_name', 'description')]))

            self.__name = my_name
            self.__description = description
        elif remove:
            self.get_lang(('common', 'jam'),REQUEST)
            return self.message_dialog2(
                self, REQUEST,
                title = REQUEST['L_confirmation'],
                message = REQUEST['L_are_you_sure_jam_session'] % \
                self.get_n_artefacts(),
                handler = 'delete_confirmation_form_handler',
                option1_value = REQUEST['L_cancel'],
                option1_name = 'cancel',
                option2_value = REQUEST['L_ok'],
                option2_name = 'delete'
                )
        else:
            raise 'FLE Error', 'Unknown button' # Should never happen.


        REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))

    security.declareProtected(perm_edit, 'delete_confirmation_form_handler')
    def delete_confirmation_form_handler(
        self,
        REQUEST,
        cancel='', # submit buttons
        delete='',
        ):
        """Delete this JamSession."""

        if delete:
            self.parent()._delObject(self.get_id())
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST,'../index_html'))
            return
        elif cancel:
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))
            return
        else:
            raise 'FLE Error', 'Unknown button'


    security.declareProtected(perm_add_lo, 'add_artefact_form_handler')
    def add_artefact_form_handler(
        self, REQUEST,
        artefact_name = '',
        artefact_upload = None,
        parent_ids = (),
        submit = '', # submit buttons
        cancel = '',
        ):
        """Form handler for add_artefact_form."""

        if submit:
            errors = []
            self.get_lang(('common', 'jam'), REQUEST)

            artefact_name = artefact_name.strip()
            if not is_valid_title(artefact_name):
                errors.append(REQUEST['L_name_of_the_artefact'])

            if not artefact_upload or len(artefact_upload.filename) == 0:
                errors.append(REQUEST['L_upload_file'])

            if type(parent_ids) == StringType:
                parent_ids = (parent_ids,)

            # Some sanity checks to make sure that
            # a) there aren't errors in our code
            # b) some evil cracker is not modifying input

            if len(parent_ids) == 0:
                raise 'FLE Error', 'no parent_ids given'
            if self.get_type() in ('linear', 'tree'):
                if len(parent_ids) != 1:
                    raise 'FLE Error', 'Only one parent should be given'

            existing_ids = [a.get_id() for a in
                            self.get_children('JamArtefact')]
            for pid in parent_ids:
                if pid not in existing_ids:
                    raise 'FLE Error', \
                          'Trying to add artefact to non_existing artefact'

            if self.get_type() == 'linear':
                parent_id_list = []
                for a in self.get_children('JamArtefact'):
                    for pid in a.get_parent_ids():
                        parent_id_list.append(pid)

                if intersect_bool(parent_ids, parent_id_list):
                    raise 'FLE Error', \
                          'Trying to add artefact to non-last artefact.'

            # FIXME: Add checks for 'tree' and 'graph' types

            if len(errors) > 0:
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_input'],
                    message=REQUEST['L_invalid_fields'] + ": '" + \
                    "' , '".join(errors) + "'",
                    action='add_artefact_form?artefact_name=%s&parent_ids=%s' %
                    (quote_plus(artefact_name), ','.join(parent_ids)))

            data = artefact_upload.read()
            try:
                content_type = artefact_upload.headers['content-type']
            except KeyError:
                content_type = ''

            self.add_artefact(artefact_name, data, content_type,
                              str(REQUEST.AUTHENTICATED_USER),
                              parent_ids,
                              REQUEST)
            self.update_drawing()
            self.uncache_artefacts()
        elif cancel:
            pass
        else:
            raise 'FLE Error', 'Unknown button' # Should never happen

        REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))


Globals.default__class_init__(JamSession)

# EOF
