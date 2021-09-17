# $Id: ThinkingTypeSet.py,v 1.74 2004/09/20 12:32:39 tarmo Exp $
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

"""Contains class ThinkingTypeSet, which represents a set of knowledge types."""

__version__ = "$Revision: 1.74 $"[11:-2]

import string, types

import OFS, Globals, AccessControl
from Globals import Persistent, Acquisition

from input_checks import is_valid_id
from common import reload_dtml, add_dtml
import common
from AccessControl import ClassSecurityInfo
from common import perm_view, perm_edit, perm_manage, perm_add_lo

from TraversableWrapper import TraversableWrapper
from Cruft import Cruft
from ThinkingType import ThinkingType

#A ThinkingTypeSet is a collection of ThinkingTypes. A collection (or set)
#contains types that together form a usable and meaningful combination.
#Each Course can utilize one or more sets and each CourseContext uses
#one of the Course's sets. The Course administrator can customize the
#course's sets independently from the globally available sets.
class ThinkingTypeSet(
    OFS.Folder.Folder,
    TraversableWrapper,
    Cruft,
    Persistent,
    AccessControl.Role.RoleManager,
    OFS.SimpleItem.Item):
    """Thinking type set."""
    meta_type = 'ThinkingTypeSet'
    security = ClassSecurityInfo()

    dtml_files = (
        ('index_html', 'Index page',
         'ui/ThinkingTypeSet/index_html'),

        ('fle_html_header', '',
         'ui/ThinkingTypeSet/fle_html_header'),
        ('fle_form_header', '',
         'ui/ThinkingTypeSet/fle_form_header'),

        ('edit_form_1_3', '',
         'ui/ThinkingTypeSet/edit_form_1_3'),
        ('edit_form_2_3', '',
         'ui/ThinkingTypeSet/edit_form_2_3'),
        ('edit_form_3_3', '',
         'ui/ThinkingTypeSet/edit_form_3_3'),
        )

    security.declarePrivate('make_copy')
    def make_copy(self):
        """Make a deep copy of the typeset."""
        types=[]
        thread_start=[]
        relations={}
        for type in self.get_thinking_types():
            if type.has_icon():
                data = type.get_icon().data
            else:
                data = None
            info={
                'id': type.get_id(),
                'name': type.get_name(),
                'starting_phrase': type.get_starting_phrase(),
                'description': type.get_description(),
                'colour': type.get_colour(),
                'icon': None,
                'icondata': data,
                'abbr': type.get_abbreviation(),
                'checklist': type.get_checklist(),
                }
            types.append(info)
            if type.is_start_node():
                thread_start.append(type.get_id())
            relations[type.get_id()]=type.get_possible_follow_up_ids()

        tts = ThinkingTypeSet(
            id_=self.id,
            name=self.get_name(),
            orig_name=self.get_original_name(),
            language=self.get_language(),
            description=self.get_description(),
            types=types,
            thread_start=thread_start,
            relations=relations)
        return tts

    # @id: id for the thinking type set
    # @name: name for the set
    # @types: List of ThinkingTypes that will belong to the set
    # @thread_start: List of TTs that can start a thread
    # @relations: List of tuples (pairs) of allowed reply relations
    #             (which TT can be used to reply to which TT).
    def __init__(self, id_, name, orig_name, language, description, types, thread_start, relations):
        """Construct ThinkingTypeSet."""
        self.id = id_
        self.title = ''
        self.original_name=orig_name
        self.language=language
        self.set_name(name)
        self.set_description(description)

        self._t_types=types
        self._t_thread_start=thread_start
        self._t_relations=relations
        self.__dtml_loaded = 0

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """Set default permissions for roles."""
        from common import roles_admin, roles_staff, roles_user

        self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_staff, 0)
        self.manage_permission(perm_add_lo, roles_staff, 0)
        self.manage_permission(perm_view, roles_user, 0)

        # This needed, because manage_afterAdd may be called multipled times
        # for objects inside a TempObjectManager.
        if self.__dtml_loaded:
            return

        for tup in self.dtml_files:
            add_dtml(self, tup)
        self.__dtml_loaded=1

        types=self._t_types
        thread_start=self._t_thread_start
        relations=self._t_relations
        del self._t_types
        del self._t_thread_start
        del self._t_relations

        self.sort_order = []
        for type_info in types:
            self.add_type(type_info)
            if type_info['id'] in thread_start:
                getattr(self, type_info['id']).set_starting_type()

        for (r, d) in relations.items():
            getattr(self, r).set_possible_follow_ups(d)

    # @type_name: name of the TT to add
    # @type_dict: Dictionary of data for the TT
    #             (name, explanation, instructions, abbreviation, colour, icon).
    security.declarePrivate('add_type')
    def add_type(self, type_dict):
        """Adds new thinking type to the set."""
        t = type_dict

        if t.has_key('icondata'):
            icondata=t['icondata']
        else:
            icondata=None

        if t.has_key('checklist'):
            checklist=t['checklist']
        else:
            checklist=''

        if t.has_key('abbr'):
            abbr = t['abbr']
        else:
            abbr = ''

        tt = ThinkingType(
            t['id'],
            t['name'],
            t['starting_phrase'],
            t['description'],
            t['colour'],
            t['icon'],
            icondata,
            abbr,
            checklist)
        self.add_thinking_type(tt)

    # No additional comments.
    security.declareProtected(perm_manage,'reload_dtml')
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

    # No additional comments.
    security.declareProtected(perm_view,'get_name')
    def get_name(self):
        """Return the thinking type set name."""
        return self.__name

    security.declareProtected(perm_view,'get_original_name')
    def get_original_name(self):
        """Return the original (untranslated) thinking type set name."""
        if hasattr(self,'original_name'):
            return self.original_name
        return self.get_name()

    security.declarePrivate('set_name')
    def set_name(self, name):
        """Set the thinking type set name."""
        self.__name = name

    security.declareProtected(perm_view, 'get_id')
    def get_id(self):
        """Get id."""
        return self.id

    security.declareProtected(perm_view, 'get_language')
    def get_language(self):
        """Get language."""
        if hasattr(self,'language'):
            return self.language
        else:
            return '??'

    def set_language(self,lang):
       self.language=lang

    security.declarePrivate('set_id')
    def set_id(self, id_):
        """Set id."""
        self.id = id_

    def __sort(self,types):
        """Sort entries according to defined sort_order."""
        sorted = []
        for id in self.sort_order:
            for obj in types:
                if obj.get_id()==id:
                    sorted.append(obj)
        return sorted

    security.declareProtected(perm_view,'get_thinking_types')
    def get_thinking_types(self):
        """Return a list of ThinkingType objects in this set."""
        types = self.get_children('ThinkingType')
        return self.__sort(types)

    security.declareProtected(perm_view,'get_tt_icon_url')
    def get_tt_icon_url(self, cc, tt_id, REQUEST):
        """Return the url for the icon of the given thinking type."""
        retval = []
        retval.append(cc.find_URL_of_course(REQUEST))
        retval.append('/' + self.get_id())
        retval.append('/' + tt_id)
        retval.append('/type_icon')
        return string.join(retval, '')

    security.declareProtected(perm_view,'get_possible_follow_ups')
    def get_possible_follow_ups(self,tt_ref):
        """Return thinking types that can follow another thinking type."""
        types = [self.get_child(x)
                 for x in tt_ref.get_possible_follow_up_ids()]
        return self.__sort(types)

    security.declareProtected(perm_view, 'is_possible_follow_up')
    def is_possible_follow_up(self, x, y):
        """Can ThinkingType y follow ThinkingType x? (x and y are ids.)"""
        return y in self.get_child(x).get_possible_follow_up_ids()

    # No additional comments.
    security.declareProtected(perm_view,'get_thinking_type_thread_start')
    def get_thinking_type_thread_start(self):
        """Return list of thinking types that can start a thread."""
        return filter(
            lambda x:x.is_start_node(),
            self.get_children('ThinkingType'))

    # No additional comments.
    security.declareProtected(perm_view,'get_thinking_type')
    def get_thinking_type(self, tt_id):
        """Return reference to a contained ThinkingType by tt_id."""
        return self.get_child(tt_id)

    # NOTE: tt will be owned by this set - do not pass a reference to
    # another set's TT to this method or reference problems will emerge.
    security.declareProtected(perm_add_lo,'add_thinking_type')
    def add_thinking_type(self, tt):
        """Add ThinkingType."""
        self._setObject(tt.get_id(), tt)
        self.sort_order.append(tt.get_id())

    # No additional comments.
##     def publish(self, REQUEST=None):
##         """Copy ThinkingTypeSet to the global thinking types."""
##         if self.name in self.typesets.objectIds():
##             raise 'FLE Error', 'Global thinking type names"' + self.name + '" already exists.'
##         self.typesets.add_thinking_type_set(self)

##         if REQUEST:
##             self.get_lang(('common','coursemgmnt'),REQUEST)
##             return self.message_dialog(
##                 self, REQUEST,
##                 title=REQUEST['L_set_published'],
##                 message=REQUEST['L_set_published'],
##                 action='index_html')

    security.declareProtected(perm_edit,'set_description')
    def set_description(self, desc):
        """Set the thinking type set description."""
        self.__description = desc
        if hasattr(self,'__rendered_description'):
            del self.__rendered_description

    security.declareProtected(perm_view,'get_description')
    def get_description(self):
        """Return the thinking type set description."""
        return self.__description

    security.declareProtected(perm_view,'render_description')
    def render_description(self):
        """Return set description in html rendered format"""
        if not hasattr(self,'__rendered_description'):
            from input_checks import render
            self.__rendered_description = render(
                self.get_description(),
                #legal_tags=['<p>', '</p>', '<i>', '</i>','<b>', '</b>'],
                #do_horizontal_space is default (0),
                #ignore_whitespace_magic is default: <p> and <br>
                )
        return self.__rendered_description

    security.declareProtected(perm_view,'get_colours')
    def get_colours(self):
        """Return a list of dictionaries with colours."""
        colours = common.colours
        # All your colour are belong common.colours!
        t = colours.items()

        return [(n, v) for (n, v) in colours.items()]

    security.declareProtected(perm_edit,'thinking_type_entries')
    def thinking_type_entries(self, dont_return_empty_entries=0):
        """Return 10 entries to be used in edit_form_1_3.
        It would be hard to determine what color goes where, which are
        already in use, etc., so we do things here."""
        rv = []
        # First figure out current thinking types:
        for o in self.get_thinking_types():
            rv.append({'e':1, 'o':o})
        if dont_return_empty_entries:
            return rv
        # Then fill in the rest with cruft.
        num_entries = 10 - len(rv)
        for o in (0,)*num_entries:
            rv.append({'e':0, 'o':None})
        return rv

    # FIXME: input_checks
    security.declareProtected(perm_edit,'edit_form_1_3_handler')
    def edit_form_1_3_handler(
        self,
        tts_name,
        tts_desc,
        tts_lang,
        tts_orig_name,
        tt_0_name='',tt_0_abbr='',tt_0_colour='',tt_0_icon=None,
        tt_1_name='',tt_1_abbr='',tt_1_colour='',tt_1_icon=None,
        tt_2_name='',tt_2_abbr='',tt_2_colour='',tt_2_icon=None,
        tt_3_name='',tt_3_abbr='',tt_3_colour='',tt_3_icon=None,
        tt_4_name='',tt_4_abbr='',tt_4_colour='',tt_4_icon=None,
        tt_5_name='',tt_5_abbr='',tt_5_colour='',tt_5_icon=None,
        tt_6_name='',tt_6_abbr='',tt_6_colour='',tt_6_icon=None,
        tt_7_name='',tt_7_abbr='',tt_7_colour='',tt_7_icon=None,
        tt_8_name='',tt_8_abbr='',tt_8_colour='',tt_8_icon=None,
        tt_9_name='',tt_9_abbr='',tt_9_colour='',tt_9_icon=None,
        cancel='',
        submit='',
        next_form='',
        REQUEST=None
        ):
        """Handle requests for edit_form_1_3.dtml."""
        if cancel:
            if REQUEST.get('is_new'):
                self.delete_sets((self.get_id(),))
                return REQUEST.RESPONSE.redirect(
                    self.state_href(REQUEST,'../../index_html'))
            return REQUEST.RESPONSE.redirect(
                self.state_href(REQUEST,'index_html'))

        for num in range(10):
            ct_name = REQUEST.get("tt_%s_name" % num)
            if ct_name:
                break
        else:
            # We end up here if no new types are named.
            for tt in self.get_children('ThinkingType'):
                # Look for entries about these.
                cid = tt.get_id()
                ct_name = REQUEST.get("%s_name" % cid)
                if ct_name:
                    break
            else:
                self.get_lang(('common','coursemgmnt'),REQUEST)
                return self.message_dialog(
                    self, REQUEST,
                    title=REQUEST['L_invalid_input'],
                    message=REQUEST['L_no_types_entered'],
                    action='edit_form_1_3')

        att = []
        self.set_name(tts_name)
        self.set_language(tts_lang)
        if tts_orig_name:
            self.original_name=tts_orig_name
        else:
            self.original_name=tts_name
        self.set_description(tts_desc)
        # First get rid of old thinking types.
        #for o in self.get_thinking_types():
        #    self._delObject(o.get_id())
        # First find existing thinking type objects.
        for tt in self.get_children('ThinkingType'):
            # Look for entries about these.
            cid = tt.get_id()
            # First figure out if this thinking type has record in the
            # form.
            ct_name = REQUEST.get("%s_name" % cid)
            ct_abbr = REQUEST.get("%s_abbr" % cid)
            ct_colour = REQUEST.get("%s_colour" % cid)
            ct_icon = REQUEST.get("%s_icon" % cid)
            # First figure out if this thinking type has record in the
            # form.
            if ct_abbr:
                # This thinking type can be säädetty, damn.
                tt.set_abbreviation(ct_abbr)
                tt.set_name(ct_name)
                tt.set_colour(ct_colour)
                if ct_icon:
                    if len(ct_icon.filename) > 0:
                        # We got picture
                        icon_data = ct_icon.read()
                        tt.add_image_from_data(icon_data)
                att.append(tt)
            else:
                # We don't have an entry, so it's bye bye tt
                self._delObject(tt.get_id())
                self.sort_order.remove(tt.get_id())
        # Duhuh ..
        for num in range(10):
            ct_name = REQUEST.get("tt_%s_name" % num)
            ct_abbr = REQUEST.get("tt_%s_abbr" % num)
            ct_colour = REQUEST.get("tt_%s_colour" % num)
            ct_icon = REQUEST.get("tt_%s_icon" % num)
            icon_data = None
            icon_name = ''

            # First determine if this thinking type can be added.
            if ct_name or ct_abbr:
                if not ct_abbr:
                    #ct_abbr = "%s" % num
                    ct_abbr=ct_name[:3]

                ct_abbr=ct_abbr.strip()
                if not is_valid_id(ct_abbr):
                    params=""
                    if REQUEST.get("is_new"):
                        params="?is_new=1"
                    self.get_lang(('common','coursemgmnt'),REQUEST)
                    return self.message_dialog(
                        self, REQUEST,
                        title=REQUEST['L_invalid_name'] + \
                        ': "' + ct_abbr + '"',
                        message=REQUEST['L_give_valid_name'],
                        action='edit_form_1_3'+params)

                if ct_icon:
                    if len(ct_icon.filename) > 0:
                        # We got picture.
                        icon_data = ct_icon.read()
                if not icon_data:
                    # We'll use a default icon for any type that
                    # isn't supplied with one.
                    icon_name="ui/images/types/coi/comment.gif"

                # We are about ready to create the thinking type thing.
                tt_obj = ThinkingType(
                   ct_abbr,
                   ct_name,
                   "", # We don't have an starting_phrase
                   "", # nor a description
                   ct_colour,
                   icon_name,
                   icon_data)
                self._setObject(tt_obj.get_id(), tt_obj)
                self.sort_order.append(tt_obj.get_id())
                att.append(tt_obj)

        if submit:
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST,
                "index_html"))
        elif next_form:
            params=""
            if REQUEST.get("is_new"):
                params="?is_new=1"
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST,
                "edit_form_2_3"+params))
        else:
            self.set_undefined_page("Unknown button pressed.", REQUEST)

    # FIXME: input_checks
    security.declareProtected(perm_edit,'edit_form_2_3_handler')
    def edit_form_2_3_handler(
        self,
        REQUEST,
        cancel='',
        submit='',
        previous_form='',
        next_form='',
        ):
        """Form handler for edit_form_2_3.dtml."""
        if cancel:
            if REQUEST.get('is_new'):
                self.delete_sets((self.get_id(),))
                return REQUEST.RESPONSE.redirect(
                    self.state_href(REQUEST,'../../index_html'))
            return REQUEST.RESPONSE.redirect(
                self.state_href(REQUEST,'index_html'))

        for tt in self.get_children('ThinkingType'):
            ct_start = REQUEST.get("%s_start" % tt.get_id())
            ct_desc = REQUEST.get("%s_desc" % tt.get_id())
            ct_checklist = REQUEST.get("%s_checklist" % tt.get_id())
            if ct_start:
                tt.set_starting_phrase(ct_start)
            if ct_desc:
                tt.set_description(ct_desc)
            if ct_checklist:
                tt.set_checklist(ct_checklist)
        if submit:
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST,
                'index_html'))
        elif next_form:
            params=""
            if REQUEST.get('is_new'):
                params="?is_new=1"
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST,
                'edit_form_3_3'+params))
        elif previous_form:
            params=""
            if REQUEST.get('is_new'):
                params="?is_new=1"
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST,
                'edit_form_1_3'+params))
        else:
            self.set_undefined_page("Unknown button pressed.", REQUEST)

    # FIXME: input_checks
    security.declareProtected(perm_edit,'edit_form_3_3_handler')
    def edit_form_3_3_handler(
        self,
        REQUEST,
        cancel='',        # form submit buttons
        previous_form='', #
        submit='',        #
        thread_start=[],
        followup=[],
        ):
        """Form handler for edit_form_3_3.dtml."""
        if cancel:
            if REQUEST.get('is_new'):
                self.delete_sets((self.get_id(),))
                return REQUEST.RESPONSE.redirect(
                    self.state_href(REQUEST,'../../index_html'))
            else:
                return REQUEST.RESPONSE.redirect(
                    self.state_href(REQUEST,'index_html'))

        # not cancel button -> previous or submit button pressed -> update
        # start and follow up information.


        if type(followup) is types.StringType: followup = (followup,)
        if type(thread_start) is types.StringType:
            thread_start = (thread_start,)

        id_list = [x.get_id() for x in self.get_children('ThinkingType')]

        # Store here for all types a list of follow-ups, and the same list in reverse
        d = {}
        dd = {}
        for tt_id in id_list:
            d[tt_id] = []
            dd[tt_id] = []

        for key, value in [x.split('___') for x in followup]:
            d[key].append(value)
            dd[value].append(key)

        # Input checks

        errors = []
        for tt_id in id_list:
            if not dd[tt_id] and not tt_id in thread_start:
                errors.append(tt_id)

        if not thread_start:
            # TODO: This doesn't give a very good error
            errors.append('start')

        if errors:
            self.get_lang(('common','coursemgmnt'),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_error'],
                message=REQUEST['L_use_each_type'],
                action="edit_form_3_3")

        # Store information
        
        for tt_id in id_list:
            child = self.get_child(tt_id)
            child.set_starting_type(tt_id in thread_start)
            child.set_possible_follow_ups(d[tt_id])

        if previous_form:
            params=""
            if REQUEST.get('is_new'):
                params="?is_new=1"
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST,
                'edit_form_2_3'+params))
            return

        elif submit:
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST,'index_html'))
        else:
            raise 'FLE Error', 'Unknown button'

    security.declareProtected(perm_edit,'finalize_set')
    def finalize_set(self,REQUEST):
        """Finalize and publicize the set. Editing is no longer
        possible."""
        id_list = [x.get_id() for x in self.get_children('ThinkingType')]

        d = {}
        for tt_id in id_list:
            d[tt_id] = []

        thread_start=[]
        for tt in self.get_thinking_types():
            if tt.is_start_node():
                thread_start.append(tt.get_id())
            d[tt.get_id()].append(tt.get_possible_follow_up_ids())

        # Input checks

        errors = []
        for tt_id in id_list:
            if not d[tt_id] and not tt_id in thread_start:
                errors.append(tt_id)

        if not thread_start:
            # TODO: This doesn't give a very good error
            errors.append('start')

        if errors:
            self.get_lang(('common','coursemgmnt'),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_error'],
                message=REQUEST['L_use_each_type'],
                action="edit_form_3_3")

        self.move_from_tmp(self)
        REQUEST.RESPONSE.redirect(self.state_href(REQUEST,"../.."))

Globals.InitializeClass(ThinkingTypeSet)
# EOF

