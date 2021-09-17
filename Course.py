# $Id: Course.py,v 1.176 2005/03/30 14:40:41 tarmo Exp $
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

"""Contains class Course, which represents one course, which has one or more CourseContexts, which in turn contain knowledge building conversations."""

__version__ = '$Revision: 1.176 $'[11:-2]

import time
import string, types
import OFS, Globals
from Globals import Persistent, Acquisition
import AccessControl
from AccessControl import ClassSecurityInfo
import copy

from Jamming import Jamming
from TraversableWrapper import Traversable, TraversableWrapper
from common import add_dtml, reload_dtml, intersect_bool, make_action, \
     get_roles, get_local_roles, course_level_roles, week_number
from input_checks import strip_all, is_valid_title, is_valid_url, wordwrap
from common import roles_student, roles_tutor, roles_teacher, roles_admin
from CourseContext import CourseContext
#from ThinkingTypeSetManager import ThinkingTypeSetManager as TTSM
from Thread import Thread
from Cruft import Cruft
from TempObjectManager import TempObjectManager
from input_checks import render, normal_entry_tags_and_link
from common import perm_view, perm_edit, perm_manage, perm_add_lo
from XmlRpcApi import CourseXMLRPC
from CourseStats import CourseStats

from COREBlog.COREBlog import manage_addCOREBlog
from common import FakeRequest
import re

# Each Course object contains (usually) one or more CourseContexts, which
# represent different aspects of the course.
# A Course contains information and services on one course implementation.
class Course(
    Persistent,
    TraversableWrapper,
    Traversable,
    Cruft,
    OFS.Folder.Folder,
    OFS.SimpleItem.Item,
    AccessControl.Role.RoleManager,
    Thread,
    CourseXMLRPC,
    CourseStats,
    ):
    """Course, contained within CourseManager, represents one course."""
    meta_type = 'Course'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    dtml_files = (
        ('add_course_context_form', 'Add Course Context Form',
         'ui/Course/add_course_context_form'),
        ('course_info', 'Course Information',
         'ui/Course/course_info'),
        ('graph', '', 'ui/Course/graph'),
        ('course_graph_tt', '', 'ui/Course/course_graph_tt'),
        ('course_graph_replies', '', 'ui/Course/course_graph_replies'),

        ('fle_form_header', 'Standard Html Header for forms (KB)',
         'ui/Course/fle_form_header'),

        ('fle_html_header', 'Standard FLE Html Header (KB)',
         'ui/Course/fle_html_header'),

        )


    # Call courses/course_html (This way we avoid copying index_html
    # to each instance of Course class.)
    # ATTENTION: We don't exactly know how this works (for example,
    # do we really need REQUEST ?)
    #
    #TODO: This could be done with a URL pointing to the course_html script.
    #But if we need this default implementation, we could use
    #restrictedTraverse('course_html') to activate Zope acquisition.
    security.declareProtected('View', 'index_html')
    def index_html(self, REQUEST=None):
        """Default script"""
        return self.fle_root().courses.course_html(self, REQUEST)

    # Parameters:
    #
    #- parent: should be a CourseManager
    #
    #- name: name of the Course
    #
    #- tts: list of ThinkingTypeSets (copies are made in manage_afterAdd)
    #
    #- teachers: list of users (of class UserInfo?) that are granted
    #Teacher privileges
    #
    #- etc: other textual information
    def __init__(
        self,
        parent,        # Whatever you do, dont bind this to self.
        name,
        teachers,
        description='',
        organisation='',
        methods='',
        starting_date='',
        ending_date=''):
        """Constructor of the course."""

        # Overriding all_meta_types is not not beautiful...but, hey!, it works!
        #self.all_meta_types = (
        #    {'name': 'ThinkingTypeSet',
        #     'action': 'get_id'},)

        # Cache active members.
        self.active_memb_cache = []

        # Remove all HTML tags from parameters
        name = strip_all(name)
        description = strip_all(description)
        methods = strip_all(methods)
        organisation = strip_all(organisation)

        Thread.__init__(self, parent) # Takes care of id and title.

        for teacher in teachers:
            if teacher: # Skip empty and None values
                self.set_roles(teacher, ('Teacher',))

        self.__name = name # name of the course
        self.__organisation = organisation
        self.__description = description
        self.__methods = methods
        self.__starting_date = starting_date
        self.__ending_date = ending_date

        self.__resources = []

        # This is for group folder path listings - show path up to course.
        self.toplevel = 1
              # Add dtml objects.
        for tup in self.dtml_files:
            add_dtml(self, tup)


    # This is to protect the method in CourseStats.
    # For some reason protecting the method in its own class is not effective.
    security.declareProtected(perm_manage, 'collect_stats')

    security.declarePrivate('manage_afterAdd')
    #Each course should have its own copy of the ThinkingTypeSets,
    #as the course administrator (teacher) should be able to edit them,
    #create new ones and so forth. These changes must not propagate to
    #other courses: hence the copying of the set.
    def manage_afterAdd(self, item, container):
        """foo"""

        self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_teacher, 0)
        self.manage_permission(perm_add_lo, roles_tutor, 0)
        #Staff role needs to see course information from course management
        self.manage_permission(perm_view, roles_student+('Staff',), 0)

        self._setObject('jamming', Jamming('jamming'))


#        TempObjectManager.manage_afterAdd(self, item, container)

    security.declareProtected(perm_view, 'get_printable_name')
    # No additional comments.
    def get_printable_name(self):
        """Return name of the course."""
        return self.__name

    def get_clean_name(self):
        """Return name of the course,
        without special characters and in lowercase."""
        return re.sub("[^-a-zA-Z0-9_]","",self.__name).lower()

    security.declareProtected(perm_manage, 'reload_dtml')
    # No additional comments.
    def reload_dtml(self, REQUEST=None):
        """Reload dtml files from the file system."""
        reload_dtml(self, self.dtml_files)

        if REQUEST:
            self.get_lang(('common','kb'),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_dtml_reloaded'],
                message=REQUEST['L_dtml_files_reloaded'],
                action='index_html')

    security.declarePublic('get_course_id')
    # For ZCatalog (catalog_notes defined in CourseManager)
    # This method is here so that Note and JamArtefact can acquire it.
    def get_course_id(self):
        """Return id of the course inside which this note is."""
        return self.get_id()

    security.declareProtected(perm_view, 'get_bg_colour_name')
    def get_bg_colour_name(self):
        """..."""
        return 'gr'

    #security.declareProtected(perm_view, 'get_name')
    # No additional comments.
    def get_name(self):
        """Get course name."""
        return self.__name

    def set_name(self,newname):
        self.__name=newname

    security.declareProtected(perm_view, 'get_organisation')
    # No additional comments.
    def get_organisation(self):
        """Get organisation name."""
        return self.__organisation

    security.declareProtected(perm_view, 'get_description')
    # No additional comments.
    def get_description(self):
        """Get description."""
        return self.__description

    security.declareProtected(perm_view,'render_description')
    def render_description(self):
        """Render description."""
        return render(
            self.get_description(),
            legal_tags=normal_entry_tags_and_link)

    security.declareProtected(perm_view, 'get_methods')
    # No additional comments.
    def get_methods(self):
        """Get info on methods."""
        return self.__methods

    security.declareProtected(perm_view,'render_methods')
    def render_methods(self):
        """Render methods."""
        return render(
            self.get_methods(),
            legal_tags=normal_entry_tags_and_link)

    security.declareProtected(perm_view, 'get_teachers')
    # No additional comments.
    def get_teachers(self):
        """Get teachers."""
        retval = []
        for (user, roles) in self.get_local_roles():
            if 'Teacher' in roles:
                retval.append(user)

        return retval

    security.declareProtected(perm_view, 'get_start_dd')
    # No additional comments.
    def get_start_dd(self):
        """Return starting day."""
        if self.__starting_date:
            return time.localtime(self.__starting_date)[2]
        else:
            return ''

    security.declareProtected(perm_view, 'get_start_mm')
    # No additional comments.
    def get_start_mm(self):
        """Return starting month."""
        if self.__starting_date:
            return time.localtime(self.__starting_date)[1]
        else:
            return ''

    security.declareProtected(perm_view, 'get_start_yyyy')
    # No additional comments.
    def get_start_yyyy(self):
        """Return starting year."""
        if self.__starting_date:
            return time.localtime(self.__starting_date)[0]
        else:
            return ''

    security.declareProtected(perm_view, 'get_end_dd')
    # No additional comments.
    def get_end_dd(self):
        """Return ending day."""
        if self.__ending_date:
            return time.localtime(self.__ending_date)[2]
        else:
            return ''

    security.declareProtected(perm_view, 'get_end_mm')
    # No additional comments.
    def get_end_mm(self):
        """Return ending month."""
        if self.__ending_date:
            return time.localtime(self.__ending_date)[1]
        else:
            return ''

    security.declareProtected(perm_view, 'get_end_yyyy')
    # No additional comments.
    def get_end_yyyy(self):
        """Return ending year."""
        if self.__ending_date:
            return time.localtime(self.__ending_date)[0]
        else:
            return ''

    security.declareProtected(perm_view, 'get_printable_starting_date')
    # No additional comments.
    def get_printable_starting_date(self, REQUEST):
        """Get starting date."""
        self.get_lang(('common',), REQUEST)
        return time.strftime(REQUEST['L_short_date_format'],
                             time.localtime(self.__starting_date))

    security.declareProtected(perm_view, 'get_printable_ending_date')
    # No additional comments.
    def get_printable_ending_date(self, REQUEST):
        """Get ending date."""
        if self.__ending_date == 0: return ''
        self.get_lang(('common',), REQUEST)
        return time.strftime(REQUEST['L_short_date_format'],
                             time.localtime(self.__ending_date))

    security.declarePrivate('get_start_date')
    def get_start_date(self):
        return self.__starting_date

    security.declarePrivate('get_end_date')
    def get_end_date(self):
        return self.__ending_date

    security.declareProtected(perm_view, 'get_users')
    def get_users(self, REQUEST):
        """Return dict with 2 members of attendees as UserInfo objects.
        'active_d' is the list of active members.
        'others_d' is the rest ..
        [[UIObj'active1'], [UIObj'other1', UIObj'other2', ..]]"""

        rv = {'active_d':[], 'others_d': []}
        au = str(REQUEST.AUTHENTICATED_USER)

        # User herself goes always to the first position.
        rv['active_d'].append(self.fle_users.get_user_info(au))

        for uname in filter((lambda x,au=au: x != au),
                            [(u[0]) for u in self.get_local_roles()]):
            o = self.fle_users.get_user_info(uname)
            if uname in self.active_memb_cache:
                rv['active_d'].append(o)
            else:
                rv['others_d'].append(o)
        return rv

    security.declareProtected(perm_view, 'get_all_users')
    def get_all_users(self):
        """Return a list of all users on course."""
        rv = []
        for uname in self.get_all_users_id():
            rv.append(self.fle_users.get_user_info(uname))
        return rv

    security.declareProtected(perm_view, 'get_all_users_id')
    def get_all_users_id(self):
        """Return a list of all users on this course. Same thing as
        get_all_users, but this one returns a list of id's of UserInfo
        objects, not the UserInfo object reference."""
        #return [u[0] for u in self.get_local_roles()]
        rv = []
        for user,roles in self.get_local_roles():
            if intersect_bool(course_level_roles,roles):
                rv.append(user)
        return rv

    security.declareProtected(perm_view, 'get_users_with_role')
    def get_users_with_role(self, role):
        """Return a list of participants who have a specified role."""
        rv = []
        for e in self.get_local_roles():
            if role in e[1]:
                rv.append(self.fle_users.get_user_info(e[0]))
        return rv

    security.declareProtected(perm_edit, 'add_student')
    #The person is added with Student role access.
    # NOTE: This method is no longer needed, except in the test cases!
    def add_student(self, name):
        """Add person to the course."""
        # Check that user exists... Raises exception if not.
        self.fle_users.get_user_info(name)
        self.set_roles(name, ('Student',))

    security.declareProtected(perm_view, 'get_valid_roles')
    # No additional comments.
    def get_valid_roles(self):
        """Get the roles valid for persons added to the course."""
        from CourseManager import course_level_roles
        valid_roles = list(course_level_roles)
        #valid_roles.append('Teacher')
        return valid_roles

    security.declareProtected(perm_manage, 'remove_person')
    def remove_person(self, person):
        """Remove person from the course."""
        # Check that user exists... Raises exception if not.
        self.fle_users.get_user_info(person)
        # We use the get_local_roles method, because we need to
        # see if the user has a role attached to this course object
        # specifically, and we don't want the roles in the acquisition
        # tree to interfere.
        if len(get_local_roles(self,person))==0:
            raise FleError, ("User "+person+" does not belong to this course.")
        self.__unset_roles((person,))

    # Note: person _must_ be a sequence!
    def __unset_roles(self, persons):
        """Unset roles of one user."""
        self.manage_delLocalRoles(persons)

    security.declareProtected(perm_view, 'has_role')
    # No additional comments.
    def has_role(self, person, role):
        """Return whether the user is in the specified role."""
        return role in get_roles(self,person)

    security.declareProtected(perm_view, 'get_teacher')
    def get_teacher(self):
        """Get the name of the teacher (creator of the course)."""
        for user,roles in self.get_local_roles():
            if 'Teacher' in roles:
                return user
        return None

    security.declareProtected(perm_edit, 'set_roles')
    # Note: roles _must_ be a sequence!
    # Called from CourseManager.add_users_form_handler
    def set_roles(self, person, roles):
        """Set roles of one person."""
        self.__unset_roles(person)
        self.manage_setLocalRoles(person, roles)

    # FIXME: input_checks: tt_set_name not checked
    # FIXME: input_checks: two course contexts can have identical name.
    security.declareProtected(perm_add_lo, 'add_course_context')
    # Handler for add_course_context_form
    def add_course_context(
        self, my_name, description, tt_set_name,
        description_long,
        REQUEST,

        use_roleplay='',
        # Submit buttons.
        publish='',
        cancel='',
        ):
        """Add CourseContext object."""

        if publish:
            error_fields = []
            errors = []
            self.get_lang(('common', 'kb'), REQUEST)

            my_name = my_name.strip()
            if not is_valid_title(my_name):
                error_fields.append(REQUEST['L_title_of_context'])
            if my_name in [x[1] for x in self.get_course_context_names()]:
                errors.append(REQUEST['L_name_taken'] % my_name)

            # Variables 'description' and 'description_long' are not checked
            # because render_description() and render_long_description()
            # methods in CourseContext filter out unwanted HTML tags.

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
                    ['add_course_context_form'] +
                    [(x, eval(x)) for x in
                     ('my_name', 'description', 'tt_set_name',
                      'description_long')]))

            uname=str(REQUEST.AUTHENTICATED_USER)
            obj = CourseContext(
                self, my_name, description, description_long, tt_set_name,
                uname,)
            id = obj.get_id()
            self._setObject(id, obj)
            obj.changeOwnership(self.acl_users.getUser(uname).__of__(self.acl_users))
            obj.manage_setLocalRoles(uname,('Owner',))

            if REQUEST:
                pagename=""
                if use_roleplay:
                    pagename="setup_roleplay_form"
                REQUEST.RESPONSE.redirect(self.state_href(
                    REQUEST,
                    '%s/%s' % (str(id),pagename)))
        elif cancel:
            return REQUEST.RESPONSE.redirect(self.state_href(REQUEST,REQUEST.URL1))
        else:
            raise "add_course_context called without 'publish' or 'cancel'"

    security.declareProtected(perm_view, 'get_course_context_names')
    # No additional comments.
    def get_course_context_names(self):
        """Return a list of CourseContext names."""
        retval = {}

        for e in self.get_children('CourseContext'):
            id = e.get_id()
            name = e.get_name()
            retval[id] = name
        return retval.items()

    security.declareProtected(perm_view, 'get_n_notes')
    def get_n_notes(self):
        """Returns a sum of all notes in all contexts."""
        count = 0
        for cc in self.get_course_contexts():
            count += cc.get_n_notes()
        return count

    security.declareProtected(perm_view, 'get_n_unread_notes')
    def get_n_unread_notes(self,uname):
        """Returns a sum of all unread notes in all contexts."""
        count = 0
        for cc in self.get_course_contexts():
            count += cc.get_n_unread_notes(uname)
        return count

    security.declareProtected(perm_view, 'get_n_unread_artefacts')
    def get_n_unread_artefacts(self, uname):
        """Return total number of unread JamArtefact in this course."""
        n = 0
        for js in self.jamming.get_children('JamSession'):
            n += js.get_n_unread_artefacts(uname)
        return n

    security.declareProtected(perm_view, 'get_n_artefacts')
    def get_n_artefacts(self):
        """Return total number of JamArtefact in this course."""
        n = 0
        for js in self.jamming.get_children('JamSession'):
            n += js.get_n_artefacts()
        return n

    security.declarePrivate('update')
    # Parameters are received from the form (apparently).
    def update(
        self,
        name,
        description,
        organisation,
        methods,
        starting_date,
        ending_date,
        ):
        """Edit course information."""

        self.__name = name
        self.__description = description
        if self.has_announcements():
            self.announcements._updateProperty("blog_long_description",description)
        self.__organisation = organisation
        self.__methods = methods
        self.__starting_date = starting_date
        self.__ending_date = ending_date

    security.declareProtected(perm_view, 'get_course_contexts')
    def get_course_contexts(self):
        """Return a list of all course contexts in this course."""
        return self.get_children('CourseContext')

    security.declareProtected(perm_view, 'get_course_context_ids_in_order')
    def get_course_context_ids_in_order(self, id_list):
        """Return a list of ids of all course contexts in this course."""
        return [o.get_id() for o in self.get_course_contexts_in_order(id_list)]

    # FIXME: See the random comment below, random is not
    # FIXME: probably the order that we really want.
    security.declareProtected(perm_view, 'get_course_contexts_in_order')
    def get_course_contexts_in_order(self, id_list):
        """Return a list of all course contexts in this course."""
        contexts = {}
        for c in self.get_children('CourseContext'):
            contexts[c.get_id()] = c

        retval = []
        if id_list and id_list != ['']:
            if type(id_list) == types.StringType:
                id_list = (id_list, )

            # Return courses contexts in a given order.
            for identifier in id_list:
                try:
                    retval.append(contexts[identifier])
                    del contexts[identifier]
                except KeyError: # invalid id_list
                    pass

        # If we still course contexts left (id_list is shorter
        # than the actual number of course_contexts), insert
        # them to the beginning of the list (in random order)
        for key in contexts.keys():
            retval.insert(0,contexts[key])

        return retval


    security.declareProtected(perm_view, 'get_thinking_types_on_course')
    # Return something like:
    #  [ [[tts_id1, tts1_name], [[tt1_id, tt1_name], [tt2_id, tt2_name], ...]],
    #    [[tts_id2, tts2_name], [[tt1_id, tt1_name], [tt2_id, tt2_name], ...]],
    #    ...
    #  ]
    def get_thinking_types_on_course(self):
        """..."""
        retval = []
        for cc in self.get_course_contexts():
            if cc.get_thinking_type_set_id() not in [x[0][0] for x in retval]:
                tts = cc.get_thinking_type_set()
                retval.append( [[tts.get_id(), tts.get_name()],
                                [[tt.get_id(), tt.get_name()] for tt \
                                 in tts.get_thinking_types()]
                                ])
        return retval

    security.declarePublic('may_view_course')
    def may_view_course(self, REQUEST):
        """Return boolean depending on wether user may or may not view
        the course."""
        from AccessControl.PermissionRole import rolesForPermissionOn
        return intersect_bool(
            get_roles(self,str(REQUEST.AUTHENTICATED_USER)),
            rolesForPermissionOn(perm_view,self))

    security.declareProtected(perm_view, 'may_add_course_context')
    def may_add_course_context(self, person):
        """Return boolean depending on wether user may or may not add
        a course context to the course."""
        from AccessControl.PermissionRole import rolesForPermissionOn
        return intersect_bool(
            get_roles(self,person),
            rolesForPermissionOn(perm_add_lo,self))

    security.declareProtected(perm_view, 'may_edit_course')
    def may_edit_course(self, person):
        """Return boolean depending on whether person can edit the course
        or not."""
        from AccessControl.PermissionRole import rolesForPermissionOn
        return intersect_bool(
            get_roles(self,person),
            rolesForPermissionOn(perm_edit,self))

    security.declareProtected(perm_view, 'active_members')
    #FIXME: Why not "get_active_members"
    def active_members(self):
        """Return a list of names of users who are active."""
        return self.active_memb_cache

    security.declareProtected(perm_view, 'search_form_handler')
    def search_form_handler(
        self,
        REQUEST,
        cancel=None, # submit buttons
        submit=None, #
        ):
        """Search form handler."""

        if submit:
            for s in 'get_subject', 'get_body':
                REQUEST.set(s, REQUEST[s])

            if hasattr(REQUEST, 'tt_id') and REQUEST['tt_id']:
                tts_ids = []
                tt_ids = []
                for s in REQUEST['tt_id']:
                    # FIXME: use of '\t!!!!\t as a separator fails if that
                    # FIXME: string is used as a part in tts_id.
                    tts_id, tt_id = s.split('\t!!!!\t')
                    tts_ids.append(tts_id)
                    tt_ids.append(tt_id)
                REQUEST['get_tt_id'] = tt_ids
                REQUEST['get_thinking_type_set_id'] = tts_ids
            else:
                # FIXME: Again, here we should use a string that is not id
                # FIXME: for any thinking type set.
                REQUEST['get_thinking_type_set_id'] = '__some_invalid_value__'

            if REQUEST['get_author'] == '___anyone___':
                REQUEST.set('get_author', self.get_all_users_id())
            else:
                REQUEST.set('get_author', REQUEST['get_author'])

            if REQUEST['get_course_id'] == '___any___':
                REQUEST.set('get_course_id', [x.get_id() for x in \
                                              self.fle_users.get_user_info(
                    str(REQUEST.AUTHENTICATED_USER)).user_courses()])
            else:
                REQUEST.set('get_course_id', REQUEST['get_course_id'])

            if REQUEST['get_course_context_id'] == '___any___':
                REQUEST.set('get_course_context_id',
                            [cc.get_id() for cc in self.get_course_contexts()])
            else:
                REQUEST.set('get_course_context_id',
                            REQUEST['get_course_context_id'])


            return self.kb_search_results(self, REQUEST)

        elif cancel:
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))
        else:
            raise 'FLE Error', 'Unknown button'

    security.declareProtected(perm_view, 'has_announcements')
    def has_announcements(self):
        """Return whether course has a announcements or not."""
        return hasattr(self,"announcements")

    def add_announcements(self):
        # Add COREBlog instance
        req=FakeRequest()
        req['id']='announcements'
        req['title']=self.get_name()
        req['management_page_charset']='UTF-8'
        req.form['createlexicon']='1'
        els = []
        class Record:
            pass
        el = Record()
        el.group='Case Normalizer'
        el.name="Case Normalizer"
        els.append(el)
        el = Record()
        el.group='Stop Words'
        el.name=" Don't remove stop words"
        els.append(el)
        el = Record()
        el.group="Word Splitter"
        el.name="Whitespace splitter"
        els.append(el)
        req.form['elements'] = els
        manage_addCOREBlog(parent=self,REQUEST=req)
        announcements=self.announcements

        # Set up permissions
        # Tutors can add comments and entries
        announcements.manage_permission('Add COREBlog Comments',roles_tutor,1)
        announcements.manage_permission('Add COREBlog Entries',roles_tutor,1)
        # Teachers can manage the announcements and moderate the entries (if applicable)
        announcements.manage_permission('Manage COREBlog',roles_teacher,1)
        announcements.manage_permission('Moderate COREBlog Entries',roles_teacher,1)
        # Anyone (even anonymous users!) can view the announcements
        announcements.manage_permission(perm_view,('Anonymous',),0)

        # Set up categories
        announcements.manage_addCategory("Announcement","")
        announcements.manage_addCategory("ToDo","")
        announcements.manage_addCategory("Event","")

        # Customize
        announcements._updateProperty("blog_long_description",self.get_description())
	announcements._updateProperty("author_profile",self.get_teachers()[0])
	announcements._updateProperty("color1","FFF")
	announcements._updateProperty("color2","CCCCCC")
	announcements._updateProperty("color3","393")
	announcements._updateProperty("color4","393")

    security.declareProtected(perm_add_lo, 'announcement_form_handler')
    def announcement_form_handler(self,title='',
                                  body='',
                                  main_category='',
                                  entry_id='',
                                  add='',
                                  cancel='',
                                  edit='',
                                  remove='',
                                  remove_confirm='',
                                  REQUEST=None):
        """Adds/removes an announcement."""
        if remove and not entry_id:
            pass
        elif add:
            uo = self.get_current_user_info_obj(REQUEST)
            name = uo.get_first_name() + ' ' + uo.get_last_name()
            if entry_id:
                self.announcements.get_entry(entry_id).manage_editEntry(author=name,
                                                                        body=body,
                                                                        extend="",
                                                                        excerpt="",
                                                                        main_category=main_category,
                                                                        moderated=1,
                                                                        title=title,
                                                                        format=1,
                                                                        subtitle='',
                                                                        sendping=0)
            else:
                self.announcements.manage_addEntry(author=name,
                                                   body=body,
                                                   extend="",
                                                   excerpt="",
                                                   main_category=main_category,
                                                   moderated=1,
                                                   title=title,
                                                   format=1,
                                                   subtitle='',
                                                   sendping=0)
            return REQUEST.RESPONSE.redirect(self.state_href(REQUEST,'announcements/'))
        elif cancel:
            pass
        elif edit:
            return REQUEST.RESPONSE.redirect(
                self.state_href(REQUEST, '../add_announcement_form?course_id=%s&entry_id=%s' % (self.get_id(),entry_id)))
        elif remove:
            self.get_lang(('common','coursemgmnt'),REQUEST)
            return self.message_dialog2(
                self, REQUEST,
                title=REQUEST['L_remove_q'],
                message=REQUEST['L_remove_announcement_verify'],
                handler='announcement_form_handler',
                extra_value_name = 'entry_id',
                extra_values = (entry_id,),
                option1_value = REQUEST['L_cancel'],
                option1_name = 'cancel',
                option2_value = REQUEST['L_remove'],
                option2_name = 'remove_confirm')
        elif remove_confirm:
#            raise 'Foo',entry_id
            self.announcements.manage_deleteEntries(ids=entry_id)
        else:
            raise 'FLE error','Unknown button'
        
        return REQUEST.RESPONSE.redirect(self.state_href(REQUEST,'../edit_announcements?course_id=%s' % self.get_id()))

    security.declareProtected(perm_view, 'has_group_folder')
    def has_group_folder(self):
        """Return whether course has a group folder or not."""
        return len(self.objectIds('GroupFolder'))>0

    def add_folder(self, my_name):
        from GroupFolder import GroupFolder
        from GroupFolderProxy import GroupFolderProxy
        new_id = 'gf'
        fol = GroupFolder(None,my_name)
        fol.id=new_id
        self._setObject(new_id,fol)
        fol=fol.__of__(self)
        self.make_group_folder_proxies(self.get_all_users())

        proxy = GroupFolderProxy(None, # any sense?
                                 self.get_name(),
                                 self.get_id())
        self.jamming._setObject(proxy.get_id(), proxy)

        return fol

    def make_group_folder_proxies(self, users):
        for user in users:
            # user.webtop.add_link(self.get_name()+" (Shared)",self.get_url_to_object(self.gf),1)
            user.webtop.add_group_folder_proxy(self.get_name(), self.get_id())

    security.declareProtected(perm_view, 'make_group_folder_proxy_handler')
    def make_group_folder_proxy_handler(self, REQUEST):
        """Make a group folder proxy on a webtop of a current user."""
        user = self.fle_users.get_child(str(REQUEST.AUTHENTICATED_USER))
        self.make_group_folder_proxies((user,))
        self.get_lang(('common','webtop'), REQUEST)
        return self.message_dialog(
            self, REQUEST,
            title=REQUEST['L_proxy_added'],
            message=REQUEST['L_added_proxy'] % self.get_name(),
            action='index_html')

    security.declareProtected(perm_view, 'does_group_folder_proxy_exist')
    def does_group_folder_proxy_exist(self, REQUEST):
        """Does current user already has a proxy on her webtop for group
        folder of this course?"""
        wt = self.fle_users.get_child(str(REQUEST.AUTHENTICATED_USER)).webtop
        return self.__proxy_finder(wt)

    def __proxy_finder(self, folder):
        for proxy in folder.get_children('GroupFolderProxy'):
            if proxy.get_course_this_belongs_to() == self:
                return 1
        for f in folder.get_children('WebtopFolder'):
            if self.__proxy_finder(f):
                return 1
        return 0

    def remove_folder_link(self,users):
        gf = self.get_child('gf')
        for user in users:
            fol = user.webtop
            self.__recurse_remove_folder_link(fol, gf)

    def __recurse_remove_folder_link(self, folder, gf):
        for (_id, proxy_fol) in folder.objectItems('GroupFolderProxy'):
            if proxy_fol.is_proxy_for(gf):
                folder._delObject(_id)

        for fol in folder.objectValues('WebtopFolder'):
            self.__recurse_remove_folder_link(fol, gf)


    security.declareProtected(perm_manage, 'eml_export')
    def eml_export(self,REQUEST):
        """Exports the course in zipped EML format."""
        from ImportExportEML import Exporter
        ex = Exporter()
        ex.exportCourse(self)
        import tempfile, os
        filename = tempfile.mktemp()
        ex.createZip(filename)
        file = open(filename,"rb")
        export_data=file.read()
        file.close()
        os.remove(filename)
        REQUEST.RESPONSE.setHeader('content-type','application/zip')
        return export_data

    security.declareProtected(perm_manage, 'text_export')
    def text_export(self, REQUEST):
        """Export the course in human (and only human) readable format."""
        retval=[]
        retval.append('Course name: ' + self.get_name())
        retval.append('')
        # Show note structure
        for cc in self.get_children('CourseContext'):
            retval.append('Course context: ' + cc.get_name())
            retval = self.__do_note_structure(cc,retval,1)

        # Show actual note bodies
        for cc in self.get_children('CourseContext'):
            retval.append('')
            retval.append('Course context name: ' + cc.get_name())
            for note in cc.get_children('Note'):
                retval = self.__do_note(note, retval)

        REQUEST.RESPONSE.setHeader('content-type','text/plain; charset=UTF-8')
        rv = '\n'.join(retval)
        #rv = unicode(rv, 'utf-8').encode('iso-8859-1')
        return rv

    def __do_note_structure(self, parent, retval, level):
        for note in parent.objectValues('Note'):
            retval.append('  '*level +  note.get_subject() + ' ('+note.get_author()+')')
            retval=self.__do_note_structure(note,retval,level+1)
        return retval

    def __do_note(self, note, retval):
        retval.append('')
        retval.append(note.get_author() + ' : ' + note.get_tt_name())
        retval.append(time.strftime("%Y-%m-%d %H:%M", time.localtime(
            note.get_creation_time())))
        body=note.get_body()
        retval.append("%s words " % len(body.split()))
        retval.append(note.get_subject())
        retval.append(wordwrap(body))
        for n in note.get_children('Note'):
            retval = self.__do_note(n, retval)
        return retval
    def write_touchgraph_data(self,obj,type,children_types=None,extra_links=None):
        links = ''
        if children_types:
            links = ' '.join(obj.objectIds(children_types))
        if extra_links:
            links = ' '.join((links,extra_links))
        if not links:
            links=' '
        return obj.get_id()+'\t'+\
              type+"\t"+\
              self.REQUEST.BASE0+self.get_url_to_object(obj)+'\t'+\
              obj.get_name()+'\t'\
              +links+'\t'

    # But should we protect it somehow?
    # The Java client would then need authentication
    def touchgraph_data(self):
        # Let's turn this method non-public while the client is not in use.
        #"""This is a public method."""
        data=self.write_touchgraph_data(self,"COURSE","CourseContext")
        for ctx in self.objectValues("CourseContext"):
            data=data+ctx.touchgraph_data()

        return data+"[END DATA]"

    # The week when the course start is labeled '1' and so on..
    def time_to_week(self, start_time, current_time):
        start_week = week_number(start_time)
        current_week = week_number(current_time)
        start_year = time.localtime(start_time)[0]
        current_year = time.localtime(current_time)[0]
        return str((current_year - start_year) * 52 +
                   current_week - start_week + 1)

    # The month when the course start is labeled '1' and so on..
    def time_to_month(self, start_time, current_time):
        start_year, start_month = time.localtime(start_time)[:2]
        current_year, current_month = time.localtime(current_time)[:2]

        return str((current_year - start_year) * 12 +
                   current_month - start_month + 1)

    def __get_data_for_x_graph_helper(self, REQUEST):

        # Display data by week or by month?
        method = self.time_to_week
        try:
            if REQUEST.graph_unit == 'month': method = self.time_to_month
        except (AttributeError, KeyError):
            pass
        
        uname = str(REQUEST.AUTHENTICATED_USER)

        tt_sets = []
        notes = []
        for cc in self.get_children('CourseContext'):
            tt_set = cc.get_thinking_type_set()
            if tt_set not in tt_sets: tt_sets.append(tt_set)
            
            notes += [(cc, x) for x in cc.walk('')[1:]]

        creation_times = []
        tuples = []
        for (cc, d) in notes:
            note = d['obj']
            if note.get_author() == uname:
                creation_time = note.get_creation_time()
                creation_times.append(creation_time)

                tuples.append((creation_time, cc.get_thinking_type_set(),
                               note.get_tt_abbreviation(), d))

        if len(creation_times) > 0:
            creation_times.sort()
            start_time = creation_times[0]
            
        for i in range(len(tuples)):
            tuples[i] = (method(start_time, tuples[i][0]),)+ tuples[i][1:]

        start_unit = 1
        if tuples:
            stop_unit = max([int(x[0]) for x in tuples])
        else:
            stop_unit = start_unit

        return (start_unit, stop_unit, tuples, tt_sets)

    def __retval_dict_to_array(self, dict_retval):
        keys = [int(x) for x in dict_retval.keys()]
        keys.sort()
        return [dict_retval[str(key)] for key in keys]
    
    security.declareProtected(perm_view, 'get_data_for_tt_graph')
    def get_data_for_tt_graph(self, REQUEST):
        """ Return something like:
        [[{'tt_set1': {'tt1': [{'path': '/6/7/'  , 'obj': <Note object>},
                               {'path': '/6/7/9/', 'obj': <Note object>},
                                '...'],
                       'tt2': [...],
                      },
           {'tt_set2': '...'}
             ...
           }
          {...}
          ...
         ], 6]
            |
            total number of notes
            """
        
        (start_unit, stop_unit, tuples, tt_sets) = \
                     self.__get_data_for_x_graph_helper(REQUEST)

        retval = {}
        for unit in [str(x) for x in range(start_unit, stop_unit+1)]:
            retval[unit] = {}
            for tt_set in tt_sets:
                retval[unit][tt_set.get_name()] = {}
                for tt in tt_set.get_thinking_types():
                    retval[unit][tt_set.get_name()][tt.get_abbreviation()] = []

        for t in tuples:
            unit     = t[0]
            tts_name = t[1].get_name()
            tt_id    = t[2]
            note     = t[3]
            retval[unit][tts_name][tt_id].append(note)

        return [self.__retval_dict_to_array(retval), len(tuples)]

    security.declareProtected(perm_view, 'get_data_for_replies_graph')
    def get_data_for_replies_graph(self, REQUEST):
        """Return something like:
        [[{'replies':
           {'user1': [{'path': '/2/3/5/9/', 'obj': <Note object>}],
            'user5': [{'path': '/2/3/',     'obj': <Note object>},
                      {'path': '/2/3/4/',   'obj': <Note object>}]
            }
           'empty': ['user2', 'user3']
           }
          {...},
          ...
         ], 6]
            |
            total number of notes
            """

        (start_unit, stop_unit, tuples, dummy) = \
                     self.__get_data_for_x_graph_helper(REQUEST)

        retval = {}
        for unit in [str(x) for x in range(start_unit, stop_unit+1)]:
            retval[unit] = {'replies': {}, 'empty': []}
            for nickname in [x.get_nickname() for x in self.get_all_users()]:
                retval[unit]['replies'][nickname] = []

        for t in tuples:
            unit = t[0]
            note_d = t[3]
            replied_to_person = note_d['obj'].parent().get_author()
            retval[unit]['replies'][replied_to_person].append(note_d)

        for unit in [str(x) for x in range(start_unit, stop_unit+1)]:
            for nickname in [x.get_nickname() for x in self.get_all_users()]:
                if len(retval[unit]['replies'][nickname]) == 0:
                    del retval[unit]['replies'][nickname]
                    retval[unit]['empty'].append(nickname)

        return [self.__retval_dict_to_array(retval), len(tuples)]

    # This is used for adding new resource and modifying existing
    # ones. Note that users can't modify the type of existing resource.
    security.declareProtected(perm_edit, 'resource_form_handler')
    def resource_form_handler(self, REQUEST,
                             resource_id=None,
                             title='',
                             author='',
                             description='',
                             type='', # 'url' or 'location'
                             url_or_location='',
                             edit='',   # submit buttons
                             cancel='', #
                             remove='', #
                             remove_confirm='', #
                             add=''     #
                             ):
        """Handler for resources."""
        if (remove or edit) and not resource_id:
            # 'Remove' or 'edit' button pressed without
            # any resources selected -> fail silently.
            pass
        elif add:

            # Input checks begin here.
            
            error_fields = []
            errors = []
            self.get_lang(('common', 'kb'), REQUEST)

            title = title.strip()
            author = author.strip()

            if not is_valid_title(title):
                error_fields.append(REQUEST['L_title_resource'])

            # Accept resource without any author.
            if not is_valid_title(author) and author:
                error_fields.append(REQUEST['L_author_resource'])

            description = strip_all(description)

            if resource_id:
                type=self.get_resource(resource_id).get_type()

            if type == CourseResource.types[1]:
                if not is_valid_url(url_or_location):
                    error_fields.append(REQUEST['L_url'])
            elif type== CourseResource.types[0]:
                pass
            else:
                raise 'FLE Error', \
                      'type should be url or location, but is ' + type
                
            if len(error_fields) > 0:
                msg = REQUEST['L_invalid_fields'] + \
                      ": '" + "' , '".join(error_fields) + "'"
                fields = ['title', 'author', 'description',
                          'type', 'url_or_location']
                if resource_id:
                    fields.append('resource_id')
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_input'],
                    message=msg,
                    action=apply(
                    make_action,
                    ['../add_resource_form'] +
                    [(x, eval(x)) for x in
                     fields] + [('course_id',self.get_id())]))

            # Input checks end here.

            if resource_id: # Edit existing resource
                self.modify_resource(resource_id,
                                     title, author, description,
                                     None, # Don't allow changing of type
                                     url_or_location)
            else: # Add new resource.
                self.add_resource(title, author, description, type,
                                  url_or_location)
        elif cancel:
            pass
        elif edit:
            return REQUEST.RESPONSE.redirect(
                self.state_href(REQUEST, '../add_resource_form?course_id=%s&resource_id=%s' % (self.get_id(),resource_id)))
        elif remove:
            self.get_lang(('common','coursemgmnt'),REQUEST)
            return self.message_dialog2(
                self, REQUEST,
                title=REQUEST['L_remove_q'],
                message=REQUEST['L_remove_resource_verify'],
                handler='resource_form_handler',
                extra_value_name = 'resource_id',
                extra_values = (resource_id,),
                option1_value = REQUEST['L_cancel'],
                option1_name = 'cancel',
                option2_value = REQUEST['L_remove'],
                option2_name = 'remove_confirm')
        elif remove_confirm:
            self.delete_resource(resource_id[0])
        else:
            raise 'FLE error', 'Unknown button'

        # Redirect to upper level so we stay in course management view.
        return REQUEST.RESPONSE.redirect(
            self.state_href(REQUEST, '../edit_course_resources?course_id=%s' % self.get_id()))

    security.declarePrivate('delete_resource')
    def delete_resource(self, resource_index):
        """Delete a resource in CourseContext."""
        self._delObject(resource_index)
        #del self.__resources[resource_index]
        #self._p_changed = 1

    security.declarePrivate('modify_resource')
    def modify_resource(self, resource_id,
                        title, author, description, type, url_or_location):
        """Modfify an existing resource in CourseContext."""
        self.get_child(resource_id).set_values(\
            title, author, description, type, url_or_location)
        #self._p_changed = 1
        
    security.declarePrivate('add_resource')
    def add_resource(self, title, author, description, type, url_or_location):
        """Add resource to CourseContext."""
        new_id='ref'+self.generate_id()
        res = CourseResource(new_id, title, author, \
                             description, type, url_or_location)
        self._setObject(new_id,res)
        #self._p_changed = 1

    security.declareProtected(perm_view, 'get_resources')
    def get_resources(self):
        """Return an array of resource objects."""
        return self.get_children('CourseResource')

    security.declareProtected(perm_view, 'get_resource')
    def get_resource(self, resource_index):
        """Return a resource object."""
        return self.get_child(resource_index)

    security.declareProtected(perm_view, 'get_resource_type')
    def get_resource_type(self, resource_index):
        """Return a resource tuple."""
        return self.get_resource(resource_index).get_type()

Globals.default__class_init__(Course)

class CourseResource(
    Traversable,
    Cruft,
    Persistent,
    OFS.SimpleItem.Item,
    AccessControl.Role.RoleManager,
    ):
    """Course resource."""
    meta_type = 'CourseResource'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    types = ('location', 'url')
    
    def __init__(self, id, title, author, description, type, location):
        """..."""
        self.id=id
        self.set_values(title, author, description, type, location)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        from common import roles_student, roles_tutor, roles_teacher
        from common import roles_admin

        #self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_teacher, 0)
        #self.manage_permission(perm_add_lo, roles_tutor, 0)
        #Staff role needs to see course information from course management
        self.manage_permission(perm_view, roles_student+('Staff',), 0)

    security.declareProtected(perm_view, 'get_id')
    def get_id(self):
        """Return id."""
        return self.id

    security.declareProtected(perm_view, 'get_title')
    def get_title(self):
        """Return title."""
        return self.title

    security.declareProtected(perm_view, 'get_author')
    def get_author(self):
        """Return author."""
        return self.author

    security.declareProtected(perm_view, 'get_description')
    def get_description(self):
        """Return description."""
        return self.description

    security.declareProtected(perm_view, 'get_type')
    def get_type(self):
        """Return type."""
        return self.type

    security.declareProtected(perm_view, 'get_location')
    def get_location(self):
        """Return location."""
        return self.location

    security.declareProtected(perm_view, 'is_url')
    def is_url(self):
        """Is type URL"""
        return self.get_type() == CourseResource.types[1]

    security.declareProtected(perm_edit, 'set_values')
    def set_values(self,
                   title=None,
                   author=None,
                   description=None,
                   type=None,
                   location=None
                   ):
        if type and  not type in CourseResource.types: raise 'FLE Error', \
           'Unknown resource type: %s' % type

        
        if title != None:  self.title = title
        if author != None: self.author = author
        if description != None:
            self.description = description
        if type != None: self.type = type
        if location != None: self.location = location
        
Globals.default__class_init__(CourseResource)
    

# EOF
