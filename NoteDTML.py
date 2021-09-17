# $Id: NoteDTML.py,v 1.35 2003/06/13 07:57:11 jmp Exp $
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

"""Contains class NoteDTML, which is a common superclass for Note and CourseContext, since they both need methods for creating subnotes and such."""

__version__ = "$Revision: 1.35 $"[11:-2]

import string
import re
from urllib import quote_plus

from AccessControl import ClassSecurityInfo
import Globals
from Globals import Persistent

from common import add_dtml, reload_dtml, \
     perm_view, perm_edit, perm_manage, perm_add_lo
from input_checks import is_valid_url, is_valid_title, strip_tags

# In CourseContext object we can create new thread.
# In Note object we can reply to Note.
# These two operations are really a same operation: create a new Note object.
# This class has dtml files and a form handler related to
# this operation (adding and previewing a Note).
#
# CourseContext and Note inherit this class, so these methods are
# used through them.
class NoteDTML(Persistent):
    """NoteDTML object."""

    __dtml_files = (
        )

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    def __init__(self):
        """Add dtml files."""

        for tup in self.__dtml_files:
            add_dtml(self, tup)

    security.declareProtected(perm_manage, 'reload_dtml')
    # No additional comments.
    def reload_dtml(self, REQUEST=None):
        """Reload dtml files from the file system."""

        reload_dtml(self, self.__dtml_files)

        if REQUEST:
            self.get_lang(('common','kb'),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_dtml_reloaded'],
                message=REQUEST['L_dtml_files_reloaded'],
                action='index_html')

    security.declareProtected(perm_add_lo, 'reply_button_handler')
    # When user wants to reply to a note, she select a thinking
    # type and then hits reply. Then this method is called.
    def reply_button_handler(self, tt_id, REQUEST, cont=''):
        """Creates temporary note object and redirects to edit_form."""
        if cont:
            user = self.fle_users.get_user_info(str(
               REQUEST.AUTHENTICATED_USER))
            #raise "moi", user.get_edit()
            REQUEST.RESPONSE.redirect(self.state_href(
               REQUEST,
               user.get_edit()))
            return

        if tt_id == "...":
            REQUEST.RESPONSE.redirect(self.state_href(
                REQUEST,
                'describe_thinking_types'))
        else:
            if tt_id in [o.get_id() for o in self.get_possible_follow_ups()]:
                # Create note object.
                author = str(REQUEST.AUTHENTICATED_USER)
                starting = self.get_thinking_type_set().get_thinking_type(tt_id).get_starting_phrase()
                (broken_id, note) = self.add_note(
                    tt_id, author, '', starting)
                #(broken_id, note) = self.add_note(
                #    tt_id, author, 'tmp', 'tmp',
                #    url, url_name, image, image_name)

                REQUEST.RESPONSE.redirect(self.state_href(
                    REQUEST,
                    'tmp_objects/%s/edit_form' % broken_id))
            else:
                raise 'FLE Error', 'Hacked input.'


    security.declarePrivate('add_note')
    # Returns a tuple containing the temporary id and object reference.
    def add_note(
        self,
        tt_id,
        author,
        subject,
        body,
        url='',
        url_name='',
        image=None,
        image_name='',
        creation_time = None,
        ):
        """Implementation of note adding."""
        note = self.add_reply(
            tt_id, author, subject, body,
            url, url_name, image, image_name,creation_time)
        note = note.__of__(self)
        broken_id = self.add_tmp_object(note)
        return (broken_id,note)

    security.declarePrivate('add_reply')
    # This is nothing but a utility function.
    def add_reply(
        self,
        tt_id,
        author,
        subject,
        body,
        url,
        url_name,
        image,
        image_name,
        creation_time = None,
        ):
        """Create a new child note."""
        # get_thinking_type_ref implemented in CourseContext (use acquisition)
        tt_ref = self.get_thinking_type_set().get_thinking_type(tt_id)

        from Note import Note
        obj = Note(
            self, author, subject, body, tt_ref,
            url, url_name, image, image_name,creation_time)
        return obj

Globals.default__class_init__(NoteDTML)

# EOF
