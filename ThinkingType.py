# $Id: ThinkingType.py,v 1.47 2003/06/13 07:57:11 jmp Exp $
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

"""Contains class ThinkingType that represents a knowledge type."""

__version__ = "$Revision: 1.47 $"[11:-2]

import types, os

import OFS, Globals, AccessControl
from Globals import Persistent, Acquisition

from TraversableWrapper import TraversableWrapper
from Cruft import Cruft
from common import reload_dtml, add_dtml, file_path
from common import perm_view, perm_edit, perm_manage, perm_add_lo

#Represents a thinking type (knowledge type, whatever). Each Note
#in knowledge building is associated with one thinking type, which
#should classify the intent of the note.
#
#ThinkingType contains information like icon, name, explanation and
#such for one thinking type.
class ThinkingType(
    OFS.Folder.Folder,
    TraversableWrapper,
    Cruft,
    Persistent,
    AccessControl.Role.RoleManager,
    OFS.SimpleItem.Item):
    """Thinking type."""
    meta_type = 'ThinkingType'
    security = AccessControl.ClassSecurityInfo()

    dtml_files = (
        )

    # @id: id of the object
    # @name: name for the TT
    # @starting_phrase: A phrase describing the thinking type.
    # @description: a long description of the thinking type.
    # @colour: Colour (for background)
    # @icon: Path for the icon (relative path in file system) (optional)
    # @icondata: Image object for icon (optional)
    def __init__(
        self,
        id_,
        name,
        starting_phrase,
        description,
        colour,
        icon,
        icondata,
        abbr='',
        checklist='',
        ):
        """Construct ThinkingType."""
        self.id = id_
        self.title = ''

        if abbr:
            self.set_abbreviation(abbr)
        else:
            self.set_abbreviation(id_) # FIXME: Temporary hack

        self.set_name(name)
        self.set_starting_phrase(starting_phrase)
        self.set_description(description)
        self.set_checklist(checklist)

        self.set_colour(colour)
        self.__is_start_node = 0
        self.__possible_follow_ups = []

        # Set icon.
        if icon:
            self.add_image(os.path.join(file_path, icon))
        elif icondata:
            self.manage_addImage('type_icon', icondata, '')

        for tup in self.dtml_files:
            add_dtml(self, tup)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self,item,container):
        from common import roles_admin, roles_staff, roles_user

        self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_staff, 0)
        self.manage_permission(perm_add_lo, roles_staff, 0)
        self.manage_permission(perm_view, roles_user, 0)

    security.declareProtected(perm_edit,'add_image')
    # The icon is copied into the TT, so global changes won't affect it.
    # Parameter is a relative path in the file system.
    def add_image(self, fs_path):
        """Add Thinking type icon."""
        from common import add_image_obj
        add_image_obj(self, 'type_icon', '', fs_path)

    security.declareProtected(perm_edit,'add_image_from_data')
    def add_image_from_data(self, data):
        """Add thinking type icon from raw data. Are you ready for this?
        We don't care."""
        # Remove old image if it exists:
        try:
            self.type_icon
            self._delObject('type_icon')
        except AttributeError: pass
        self.manage_addImage('type_icon', data, '')

    security.declareProtected(perm_edit,'set_starting_type')
    # No additional comments.
    def set_starting_type(self, bool=1):
        """Set starting type. If this is true, this type can start a new
        discussion thread."""
        self.__is_start_node = bool

    security.declareProtected(perm_view,'is_start_node')
    # No additional comments.
    def is_start_node(self):
        """Returns whether this TT can be used to start a new thread."""
        return not not self.__is_start_node

    security.declareProtected(perm_edit,'set_possible_follow_ups')
    def set_possible_follow_ups(self, follow_ups):
        """Sets this TT's follow-up table to the supplied list"""
        self.__possible_follow_ups = []
        for f in follow_ups:
            if not f in self.__possible_follow_ups:
                self.__possible_follow_ups.append(f)
        self._p_changed = 1

    security.declareProtected(perm_view,'get_possible_follow_up_ids')
    # No additional comments.
    def get_possible_follow_up_ids(self):
        """Returns the list of possible follow-up TTs' ids."""
        return self.__possible_follow_ups

    security.declareProtected(perm_manage,'reload_dtml')
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

    security.declareProtected(perm_view,'get_name')
    def get_name(self):
        """Return name."""
        return self.__name
    security.declareProtected(perm_edit,'set_name')
    def set_name(self, name):
        """Set name."""
        self.__name = name

    security.declareProtected(perm_view,'get_starting_phrase')
    def get_starting_phrase(self):
        """Return starting phrase."""
        return self.__start_phrase
    security.declareProtected(perm_edit,'set_starting_phrase')
    def set_starting_phrase(self, phrase):
        """Set thinking types starting phrase."""
        self.__start_phrase = phrase
        self._p_changed = 1

    security.declareProtected(perm_view,'get_description')
    def get_description(self):
        """Return note description."""
        return self.__description

    security.declareProtected(perm_view,'render_description')
    def render_description(self):
        """Return type description in html rendered format"""
        if not hasattr(self,'__rendered_description'):
            from input_checks import render, normal_entry_tags
            self.__rendered_description = render(
                self.get_description(),
                legal_tags=normal_entry_tags,
                #legal_tags=['<p>', '</p>', '<i>', '</i>','<b>', '</b>'],
                #do_horizontal_space is default (0),
                #ignore_whitespace_magic is default: <p> and <br>
                )
        return self.__rendered_description

    security.declareProtected(perm_edit,'set_description')
    def set_description(self, desc):
        """Set thinking type description."""
        self.__description = desc
        if hasattr(self,'__rendered_description'):
            del self.__rendered_description

    security.declareProtected(perm_edit,'set_checklist')
    def set_checklist(self, checklist):
        """Set the thinking type set check list."""
        self.__checklist = checklist
        if hasattr(self,'__rendered_checklist'):
            del self.__rendered_checklist

    security.declareProtected(perm_view,'get_checklist')
    def get_checklist(self):
        """Return the thinking type set checklist."""
        try:
            return self.__checklist
        except AttributeError:
            return ''

    security.declareProtected(perm_view,'has_checklist')
    def has_checklist(self):
        try:
            return not not self.__checklist
        except AttributeError:
            return 0

    security.declareProtected(perm_view,'render_checklist')
    def render_checklist(self):
        """Return set checklist in html rendered format"""
        if not hasattr(self,'__rendered_checklist'):
            from input_checks import render, normal_entry_tags
            self.__rendered_checklist = render(
                self.get_checklist(),
                legal_tags=normal_entry_tags,
                #legal_tags=['<p>', '</p>', '<i>', '</i>','<b>', '</b>'],
                #do_horizontal_space is default (0),
                #ignore_whitespace_magic is default: <p> and <br>
                )
        return self.__rendered_checklist

    security.declareProtected(perm_view,'get_abbreviation')
    def get_abbreviation(self):
        """Return thinking type abbreviation."""
        return self.__abbreviation

    security.declareProtected(perm_edit,'set_abbreviation')
    def set_abbreviation(self, abbr):
        """Return thinking type abbrevation."""
        self.__abbreviation = abbr

    security.declareProtected(perm_view,'has_icon')
    def has_icon(self):
        return hasattr(self, 'type_icon')

    security.declareProtected(perm_view,'get_icon')
    # No additional comments.
    def get_icon(self):
        """Return icon (image data)."""
        return self.type_icon

    security.declareProtected(perm_view,'get_colour')
    # No additional comments.
    def get_colour(self):
        """Return colour."""
        return self.__colour
    security.declareProtected(perm_edit,'set_colour')
    def set_colour(self, colour):
        """Set thinking type colour."""
        self.__colour = colour

    def touchgraph_data(self):
        data=self.write_touchgraph_data(self,"TYPE")
        return data

Globals.InitializeClass(ThinkingType)
# EOF
