# $Id: CourseContext.py,v 1.101 2003/06/13 07:57:10 jmp Exp $

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

"""Contains class CourseContext, which represents one part of a Course."""

__version__ = "$Revision: 1.101 $"[11:-2]

import OFS, Globals
import AccessControl
import re, string, types

from Thread import Thread, EventManager
from common import reload_dtml, add_dtml, intersect_bool, make_action, get_roles
from input_checks import strip_all, render, is_valid_title, \
     normal_entry_tags_and_link, is_valid_url
from TraversableWrapper import TraversableWrapper, Traversable
from AccessControl import ClassSecurityInfo
from NoteDTML import NoteDTML
from Cruft import Cruft
from TempObjectManager import TempObjectManager
from common import perm_view, perm_edit, perm_manage, perm_add_lo
from XmlRpcApi import CourseContextXMLRPC
import Course

# CourseContexts exist inside Courses. Each course has at least one
# context, since contexts in turn can contain Notes that form
# knowledge building threads.
class CourseContext(
    EventManager,
    TraversableWrapper,
    Traversable,
    Cruft,
    Thread,
    NoteDTML,
    TempObjectManager,
    CourseContextXMLRPC,
    ):
    """Course Context."""
    meta_type = 'CourseContext'

    dtml_files = (
        #('repr_norm', '',
        # 'ui/CourseContext/repr_norm'),
        #('index_html', '',
        # 'ui/CourseContext/index_html'),
        # NB: this is here just because Thread.ThreadContainer.iterate_note
        # NB: needs a repr attribute to print for each Thread object it
        # NB: prints.
        #('repr', '',
        # 'ui/CourseContext/repr'),
        #('repr_in_course', '',
        # 'ui/CourseContext/repr_in_course'),
        )

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    # Call courses/context_html (This way we avoid copying index_html
    # to each instance of CourseContext class.)
    security.declareProtected(perm_view, 'index_html')
    def index_html(self, REQUEST):
        """index_html page."""
        self.update_reader(str(REQUEST.AUTHENTICATED_USER))
        return self.courses.context_html(self, REQUEST)

    # @tts_name: id of the global knowledge type set that should
    # be copied to this context. If set to '' or None, nothing is
    # copied.
    def __init__(
        self, parent, my_name, description, descr_long, tts_name, author):
        """Construct the course context object."""
        Thread.__init__(self, parent)
        EventManager.__init__(self)
        NoteDTML.__init__(self)

        self.__name = strip_all(my_name) # Get rid of possible HTML tags

        # Variables description and descr_long are not filtered because
        # render_description() and get_long_description() methods do the
        # filtering... (Why? To make it slower? At least this way it is
        # easier to change tags that are filtered afterwards.)
        self.__description = description
        self.__author = author
        self.__roleplay_in_use = 0
        self.__roleplay = {}

        # Adds long course context description.
        #
        # Why don't we just use self.descr_long ? Is it too simple solution? ;)
        # (ik/16.1.2002)
        if not descr_long:
            descr_long = ' '
        self.manage_addDTMLDocument('descr_long', '', descr_long)

        # Select the thinking type set to use for this course context.
        if tts_name:
            h = parent.fle_root().typesets
            if not h.is_valid_tts(tts_name):
                raise 'FLE Error', 'Non-existing thinking type set to use for Course Context.'
        # Store the name, even if it's None
        self._tt_set_id = tts_name

        for tup in self.dtml_files:
            add_dtml(self, tup)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """Set default permissions for different roles."""

        from common import roles_student, roles_tutor, roles_teacher
        from common import roles_admin

        self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_teacher+('Owner',), 0)
        self.manage_permission(perm_add_lo, roles_student, 0)
        self.manage_permission(perm_view, roles_student, 0)

        if self._tt_set_id:
            # Make a real copy of the global typeset.
            tt_set = getattr(self.typesets, self._tt_set_id)
            self._setObject(
                self._tt_set_id,
                tt_set.make_copy())

        TempObjectManager.manage_afterAdd(self, item, container)

    security.declareProtected(perm_view, 'get_author')
    def get_author(self):
        """Return author name."""
        return self.__author

    security.declareProtected(perm_view, 'may_edit_course_context')
    def may_edit_course_context(self, person):
        """Return boolean depending on whether person can edit the course
        context or not."""
        from AccessControl.PermissionRole import rolesForPermissionOn
        return intersect_bool(
            get_roles(self,person),
            rolesForPermissionOn(perm_edit,self))

    # No additional comments.
    security.declareProtected(perm_manage, 'reload_dtml')
    def reload_dtml(self, REQUEST=None):
        """Reload dtml files from the file system."""
        NoteDTML.reload_dtml(self)
        reload_dtml(self, self.dtml_files)

        if REQUEST:
            self.get_lang(('common','kb'),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_dtml_reloaded'],
                message=REQUEST['L_dtml_files_reloaded'],
                action='index_html')

    security.declareProtected(perm_view, 'get_n_notes')
    def get_n_notes(self):
        """Return number of notes in this CourseContext."""
        n = 0
        for note in self.get_children('Note'):
            n += note.get_n_notes()
        return n

    # This is a stub that is needed, because when a note is published, it
    # will call its parent's uncache_notes method. When a new thread is
    # started, the call ends up here.
    def uncache_notes(self):
        pass

    security.declareProtected(perm_view, 'get_n_unread_notes')
    def get_n_unread_notes(self, uname):
        """Return number of unread notes in this CourseContext for given user."""
        n = 0
        for note in self.get_children('Note'):
            n += note.get_n_unread_notes(uname)
        return n

    security.declareProtected(perm_view, 'get_printable_name')
    # No additional comments.
    def get_printable_name(self):
        """Return name of the CourseContext"""
        return self.__name

    security.declareProtected(perm_view, 'get_possible_follow_ups')
    def get_possible_follow_ups(self):
        return self.get_thinking_type_thread_start()

    security.declareProtected(perm_view, 'get_thinking_type_thread_start')
    def get_thinking_type_thread_start(self):
        """Gives list of thinking types that can start a thread."""
        tts = self.get_thinking_type_set()
        return tts.get_thinking_type_thread_start()

    security.declareProtected(perm_view, 'get_thinking_type_set')
    def get_thinking_type_set(self):
        """Return ThinkingTypeSet object."""
        return self.get_child(self._tt_set_id)

    security.declareProtected(perm_view, 'get_thinking_type_set_id')
    def get_thinking_type_set_id(self):
        """Return ThinkingTypeSet id."""
        return self._tt_set_id

    security.declareProtected(perm_view, 'get_name')
    # No additional comments.
    def get_name(self):
        """Return name."""
        return self.__name

    security.declareProtected(perm_view, 'get_description')
    # No additional comments.
    def get_description(self):
        """Return description."""
        return self.__description

    security.declareProtected(perm_view,'render_description')
    def render_description(self):
        """Render description."""
        return render(
            self.get_description(),
            legal_tags=normal_entry_tags_and_link)

    security.declareProtected(perm_view, 'get_long_description')
    # No additional comments.
    def get_long_description(self):
        """Return description."""
        return self._getOb('descr_long')()

    security.declareProtected(perm_view, 'is_long_description_empty')
    def is_long_description_empty(self):
        """Does long description contain only white space?"""
        return self.get_long_description().strip() == ''

    security.declareProtected(perm_view,'render_long_description')
    def render_long_description(self):
        """Render long description."""
        return render(
            self.get_long_description(),
            legal_tags=normal_entry_tags_and_link)

##    security.declareProtected(perm_view, 'get_title')
##    # No additional comments.
##    def get_title(self):
##        """Return title."""
##        return self.title

    security.declareProtected(perm_view, 'get_course_ref')
    def get_course_ref(self):
        """Return reference to the course of this CourseContext."""
        return self.find_class_obj(Course.Course)

    security.declarePublic('is_temporary')
    def is_temporary(self):
        """This is here to diguise CourseContext objects as Note objects. ;)"""
        return 0

    security.declareProtected(perm_edit, 'edit_course_context')
    def edit_course_context(self,
                            REQUEST,
                            my_name = '',
                            description = '',
                            description_long = '',
                            use_roleplay = '',
                            delete = '',
                            cancel = '',  # submit buttons
                            publish = '', #
                            ):
        """Handler for ui/CourseContext/edit_course_context_form.dtml."""

        if delete:
            self.get_lang(('common', 'coursemgmnt'),REQUEST)
            return self.message_dialog2(
                self, REQUEST,
                title = REQUEST['L_confirmation'],
                message = REQUEST['L_are_you_sure_ctx'] + ' ' + \
                   self.get_name(),
                handler = 'delete_form_handler',
                extra_value_name = 'ctx_id',
                extra_values = (self.get_id(),),
                option1_value = REQUEST['L_cancel'],
                option1_name = 'cancel',
                option2_value = REQUEST['L_ok'],
                option2_name = 'delete'
                )

        elif publish:
            error_fields = []
            errors = []
            self.get_lang(('common', 'kb'), REQUEST)

            my_name = my_name.strip()
            if not is_valid_title(my_name):
                error_fields.append(REQUEST['L_title_of_context'])
            if my_name != self.get_name() and \
               my_name in [x[1] for x in self.get_course_context_names()]:
                errors.append(REQUEST['L_name_taken'] % my_name)

            # Variables 'description' and 'description_long' are not checked
            # because render_description() and render_long_description()
            # methods filter out unwanted HTML tags.

            if len(error_fields) > 0 or len(errors) > 0:
                msg = ", ".join(errors)
                if len(error_fields) > 0:
                    msg = msg + "<br>" + REQUEST['L_invalid_fields'] + \
                          ": '" + "' , '".join(error_fields) + "'"
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_input'],
                    message=msg,
                    action=apply(
                    make_action,
                    ['edit_course_context_form'] +
                    [(x, eval(x)) for x in
                     ('my_name', 'description', 'description_long')]))


            self.__name = my_name
            self.__description = description

            # Edit long course context description.
            description_long_ob = self._getOb('descr_long')
            description_long_ob.manage_edit(description_long,
                                            'description_long')
            # Set roles for users.
            self.set_roleplay(publish=1, REQUEST=REQUEST)

            # Use roleplay?
            self.__roleplay_in_use = use_roleplay

            return REQUEST.RESPONSE.redirect(
                self.state_href(REQUEST, 'index_html'))

        elif cancel:
            return REQUEST.RESPONSE.redirect(
                self.state_href(REQUEST, 'index_html'))
        else:
            raise 'FLE error', 'Unknown button'

    security.declareProtected(perm_edit, 'delete_form_handler')
    def delete_form_handler(
        self,
        REQUEST,
        delete='',
        cancel='',
        ):
        """Form handler that is called from message_dialog2."""
        if delete:
            id_ = self.get_id()
            self.parent()._delObject(id_)
            return REQUEST.RESPONSE.redirect(self.state_href_remove_from_list(REQUEST, "../index_html", 'cc_order' + self.parent().get_id(), id_))
        else:
            return REQUEST.RESPONSE.redirect(self.state_href(REQUEST, "index_html"))

    security.declarePrivate('set_roleplay_use')
    def set_roleplay_use(self, in_use):
        """Set whether or not this context uses roleplaying."""
        self.__roleplay_in_use = in_use

    security.declareProtected(perm_view, 'uses_roleplay')
    def uses_roleplay(self):
        """Returns whether or not this context uses roleplaying."""
        return self.__roleplay_in_use

    security.declarePrivate('set_user_role_name')
    def set_user_role_name(self, uname, role_name):
        """Set playrole for user given by user's uname."""
        self.__roleplay[uname] = role_name
        self._p_changed = 1

    security.declareProtected(perm_edit, 'set_roleplay')
    def set_roleplay(self,cancel='',publish='',REQUEST=None):
        """Sets up roleplaying for this context."""
        if publish and REQUEST:
            self.__roleplay={}
            self.__roleplay_in_use = 1
            for (key,val) in REQUEST.items():
                if key.startswith('roleplay_'):
                    self.__roleplay[key[9:]]=val
            self._p_changed=1
        REQUEST.RESPONSE.redirect(self.state_href(REQUEST,'index_html'))

    security.declareProtected(perm_view, 'get_nickname_with_role_name')
    def get_nickname_with_role_name(self, uname):
        """Return role name (if exists) followed by nickname in parentheses.
        If roleplay is not used in this CourseContext returns only nickname."""
        
        nickname = self.fle_users.get_user_info(uname).get_nickname()
        if self.uses_roleplay():
            role = self.get_role_played_by_user(uname)
            return role + ' (' + nickname + ')'
        else:
            return nickname

    security.declareProtected(perm_view, 'get_role_played_by_user')
    def get_role_played_by_user(self,uname):
        """Returns the role of the specified user in
        this context's roleplay."""
        try:
            return self.__roleplay[uname]
        except AttributeError:
            return ""
        except KeyError:
            return ""

    def touchgraph_data(self):
        data=self.write_touchgraph_data(self,"CONTEXT","Note")
        set = self.get_thinking_type_set()
        for tt in set.get_thinking_types():
            data=data+tt.touchgraph_data()
        for note in self.objectValues("Note"):
            data=data+note.touchgraph_data()
        return data


Globals.InitializeClass(CourseContext)

# EOF

