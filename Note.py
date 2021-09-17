# $Id: Note.py,v 1.137 2004/12/13 22:58:49 tarmo Exp $

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

"""Contains class Note, which represents a note in a knowledge building conversation."""

__version__ = "$Revision: 1.137 $"[11:-2]

import copy, time, re, string, urllib, types
from urllib import quote_plus

import OFS, Globals
from Globals import Persistent
from AccessControl import ClassSecurityInfo
from Products.ZCatalog.CatalogAwareness import CatalogAware

from common import reload_dtml, add_dtml, intersect_bool, get_roles
from input_checks import strip_all, strip_tags, \
     is_valid_url, is_valid_title
from Thread import Thread, EventManager
from TraversableWrapper import TraversableWrapper, Traversable
from Cruft import Cruft
from NoteDTML import NoteDTML
from TempObjectManager import TempObjectManager
from common import perm_view, perm_edit, perm_manage, perm_add_lo
from XmlRpcApi import NoteXMLRPC
import CourseContext

allowed_tags_in_notes = ('p','br','i','b','blockquote')

#All knowledge building entries are Notes.
#Each Course consists of one or more CourseContexts, of which each
#can contain discussion threads (or problems). A note object is used
#to start each thread and also for each successive reply to a thread.
class Note(
    CatalogAware,
    TraversableWrapper,
    Traversable,
    Cruft,
    EventManager,
    Thread,
    NoteDTML,
    TempObjectManager,
    NoteXMLRPC,
    ):
    """Note in Knowledge Building."""
    meta_type = 'Note'

    dtml_files = (
        #('repr', '', 'ui/Note/repr'),
        )
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    # Call courses/note_html (This way we avoid copying index_html
    # to each instance of Note class.)
    #
    # If index_html is handled normally through acquisition we could
    # probably just delete this method, which would move execution up the
    # acquisition tree to CourseContext or Course (or even CourseManager).
    # But they need their own index_htmls. Should we have a separate
    # subclass of Note for thread starters, which would contain all necessary
    # DTML methods and other UI related methods that notes need?
    security.declareProtected(perm_view, 'index_html')
    def index_html(self, REQUEST):
        """Default script - redirects to CourseManager's note_html script."""
        self.update_reader(repr(REQUEST.AUTHENTICATED_USER))
        self.uncache_unread_notes(repr(REQUEST.AUTHENTICATED_USER))
        return self.fle_root().courses.note_html(self, REQUEST)

    # @parent: the object under which the note will be created
    # @author: the author's user id
    # @subject: subject/topic
    # @body: the body of the note (string)
    # @tt_ref: the ThinkingType (object reference, not id)
    # @url: url to include in the note (optional)
    # @url_name: label for url (optional)
    # @image_data: image to include in the note (form upload) (optional)
    # @image_name: label for image (optional)
    def __init__(
        self, parent, author, subject, body, tt_ref,
        url='', url_name='', image_data=None, image_name='',
        creation_time=None):
        """Construct the note object."""

        # This is called when generating the Preview as well as when Publishing
        # the note. The constructor therefore cannot make any incremental
        # changes to the note's contents as the contents are reread several times
        # and fed into new Note objects.
        self.set_creation_time(creation_time)

        Thread.__init__(self, parent) # Takes care of id and title.
        EventManager.__init__(self)
        NoteDTML.__init__(self)

        self.default_catalog = 'catalog_notes'

        self.set_author(author)
        self.set_subject(subject)
        self.set_body(body)
        self.tt_ref = tt_ref
        self.tts_ref = tt_ref.parent()
        self.set_url(url)
        self.set_url_name(url_name)
        self.censored=0
        #self.image_data = copy.copy(image_data)
        if image_data and image_data.filename:
            self.set_image_data(image_data.read())
            try:
                self.set_image_content_type(image_data.headers['content-type'])
            except KeyError:
                self.set_image_content_type('')
            self.set_image_name(image_name)
        else:
            self.set_image_data(None)
            self.set_image_content_type('')
            self.set_image_name('')

        # Note objects are temporary by default.
        self.set_temporary(1)

        for tup in self.dtml_files:
            add_dtml(self, tup)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """Set default permissions for roles."""

        from common import roles_student, roles_tutor, roles_teacher
        from common import roles_admin

        self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_teacher, 0)
        self.manage_permission(perm_add_lo, roles_student, 0)
        self.manage_permission(perm_view, roles_student, 0)

        TempObjectManager.manage_afterAdd(self, item, container)
        if not self.is_temporary():
            self.index_object()

    # FIXME: This is not too beautiful... but seems to work OK.
    def manage_beforeDelete(self, item, container):
        pass

    security.declareProtected(perm_view, 'get_render_body')
    def get_render_body(self,REQUEST):
        """Return body with some modification so that
        in can be safely used in HTML pages."""

        prefix=""

        if self.censored:
            if REQUEST:
                uname = str(REQUEST.AUTHENTICATED_USER)
                self.get_lang(('common','kb'),REQUEST)
                stamp = time.strftime(REQUEST['L_short_date_format'],time.localtime(self.censored))
                prefix= REQUEST['L_removed_body'] % (self.censorer, stamp) + \
                        "<p>%s</p>" % self.censor_reason
            else:
                prefix = "CENSORED!"
                uname=''

            # If the person is not the author and is not a teacher, we only show
            # the prefix (the censored notice)
            if uname!=self.get_author() and \
               not self.may_censor_note(uname):
                return prefix

            # Add a horizontal rule between the prefix and the note body.
            prefix = prefix+"<hr>"

        # If the body isn't pre-rendered, we'll render it and store the result.
        if not hasattr(self,'__render_body'):
            from input_checks import render, normal_entry_tags
            self.__render_body = render(
                self.get_body(),
                legal_tags=normal_entry_tags,
                #ignore_whitespace_magic is default: <p> and <br>
                do_horizontal_space=1,
                )

        return prefix + self.__render_body

    security.declareProtected(perm_view, 'get_creation_time')
    def get_creation_time(self):
        """Returns the creation time."""
        return self.__creation_time

    security.declareProtected(perm_add_lo, 'set_creation_time')
    def set_creation_time(self, time_=0.0):
        """Set note creation time."""
        # This is metadata, and should be handled by zodb. Why do we bother
        # adding our own layer of bugs here? -granbo
        # 'cause we don't bother RTFM! --tarmo
        if not time_:
            self.__creation_time = time.time()
        else:
            if type(time_) is not types.FloatType:
                raise 'FLE Error', "Argument to Note.set_creation_time is not float type! (%s)" % (str(type(time_)))
            self.__creation_time = time_

    security.declareProtected(perm_view, 'get_printable_creation_day')
    def get_printable_creation_day(self,REQUEST):
        """Return the creation day in printable format."""
        return self.get_printable_day(self.get_creation_time(),REQUEST)

    security.declareProtected(perm_view, 'get_printable_creation_time')
    def get_printable_creation_time(self,REQUEST):
        """Return the creation time in printable format."""
        return self.get_printable_time(self.get_creation_time(),REQUEST)

    security.declareProtected(perm_view, 'get_printable_name')
    # No additional comments.
    def get_printable_name(self,REQUEST):
        """Return subject of the Note."""
        return self.get_subject(REQUEST)

    security.declareProtected(perm_view, 'get_body')
    # No additional comments.
    def get_body(self):
        """Return body."""
        return self.__body

    security.declareProtected(perm_manage, 'set_body')
    def set_body(self, body):
        """Set the note body."""
        self.__body = body

    def get_name(self):
        return self.get_subject()

    security.declareProtected(perm_view, 'get_subject')
    # No additional comments.
    def get_subject(self,REQUEST=None):
        """Return subject."""
        prefix = ""
        if self.censored:
            if REQUEST:
                uname = str(REQUEST.AUTHENTICATED_USER)
                self.get_lang(('kb',),REQUEST)
                prefix = REQUEST['L_removed_subject']
            else:
                prefix = "CENSORED"
                uname=''

            # If the person is not the author and is not a teacher,
            # we only show the prefix (the censored notice)
            if uname!=self.get_author() and \
               not self.may_censor_note(uname):
                return prefix

            prefix = prefix + " / "

        return prefix + self.__subject

    # Used when we want the real subject, not the possibly censored one.
    def get_real_subject(self):
        return self.__subject

    security.declareProtected(perm_add_lo, 'set_subject')
    def set_subject(self, subject):
        """Set the note subject."""
        self.__subject = strip_tags(subject, [])

    security.declareProtected(perm_view, 'get_author')
    # No additional comments.
    def get_author(self):
        """Return author."""
        return self.__author

    security.declareProtected(perm_view, 'get_author_with_rolename')
    def get_author_with_rolename(self):
        """Return author's role name (if exists) followed by nickname
        in parentheses"""
        uname = self.get_author()
        return self.get_nickname_with_role_name(uname) # acquisition

    security.declareProtected(perm_add_lo, 'set_author')
    def set_author(self, author):
        """Set the note author."""
        self.__author = author

    security.declareProtected(perm_view, 'get_author_ref')
    def get_author_ref(self):
        """Return reference to author UserInfo object."""
        return self.fle_users.get_user_info(self.get_author())

    security.declareProtected(perm_view, 'get_url')
    # No additional comments.
    def get_url(self,REQUEST=None):
        """Return URL."""
        if self.censored:
            if REQUEST:
                uname = str(REQUEST.AUTHENTICATED_USER)
            else:
                uname=''
            if uname!=self.get_author() and \
               not self.may_censor_note(uname):
                return ''

        if self.__url and self.__url != 'http://':
            return self.__url
        else:
            return ''

    security.declareProtected(perm_add_lo, 'set_url')
    def set_url(self, url):
        """Set url."""
        self.__url = strip_tags(url, [])

    security.declareProtected(perm_view, 'get_url_name')
    # No additional comments.
    def get_url_name(self):
        """Return name of the URL."""
        return self.__url_name

    security.declareProtected(perm_add_lo, 'set_url_name')
    def set_url_name(self, url_name):
        """Set the url name."""
        self.__url_name = strip_tags(url_name, [])

    security.declareProtected(perm_view, 'get_course_id')
    # For ZCatalog (catalog_notes defined in CourseManager)
    def get_course_id(self):
        """Return id of the course inside which this note is."""
        from Course import Course
        return self.find_class_obj(Course).get_id()

    security.declareProtected(perm_view, 'get_course_context_id')
    # For ZCatalog (catalog_notes defined in CourseManager)
    def get_course_context_id(self):
        """Return id of the course context inside which this note is."""
        from CourseContext import CourseContext
        return self.find_class_obj(CourseContext).get_id()

    security.declareProtected(perm_view, 'get_course_name')
    # For ZCatalog (catalog_notes defined in CourseManager)
    def get_course_name(self):
        """Return name of the course inside which this note is."""
        from Course import Course
        return self.find_class_obj(Course).get_name()

    security.declareProtected(perm_view, 'get_course_context_name')
    # For ZCatalog (catalog_notes defined in CourseManager)
    def get_course_context_name(self):
        """Return name of the course context inside which this note is."""
        from CourseContext import CourseContext
        return self.find_class_obj(CourseContext).get_name()

    security.declareProtected(perm_view, 'get_course_context_url')
    # No additional comments.
    def get_course_context_url(self, REQUEST):
        """Return the URL of the course context containing this note."""
        url = REQUEST.URL0

        # FIXME: we could use (un)restrictedTraverse to locate the context
        m = re.match("(.*?courses/.*?/.*?)/.*?", url)
        url = m.group(1) + "?" + REQUEST.QUERY_STRING
        return url

    security.declareProtected(perm_view, 'has_image')
    # No additional comments.
    def has_image(self,REQUEST=None):
        """Return whether the note has an image."""
        if self.censored:
            if REQUEST:
                uname = str(REQUEST.AUTHENTICATED_USER)
            else:
                uname=''
            if uname!=self.get_author() and \
               not self.may_censor_note(uname):
                return 0

        return not self.get_image_data() is None

    security.declareProtected(perm_view, 'is_starting_note')
    def is_starting_note(self):
        """Return whether this is node that starts a thread."""
        return isinstance(self.parent(), CourseContext.CourseContext)

    security.declareProtected(perm_view, 'get_image_data')
    # If the REQUEST parameter is specified (ie. this method is called
    # directly from an http request), we'll set the content-type of
    # the http response to match the image's content type.
    def get_image_data(self, REQUEST=None):
        """Return raw image data."""
        if REQUEST:
            REQUEST.RESPONSE.setHeader('content-type',
                self.get_image_content_type())
        return self.__image_data

    security.declareProtected(perm_add_lo, 'set_image_data')
    def set_image_data(self, image_data):
        """Set the note image data."""
        self.__image_data = image_data

    security.declareProtected(perm_view, 'get_image_content_type')
    def get_image_content_type(self):
        return self.__image_content_type

    security.declareProtected(perm_add_lo, 'set_image_content_type')
    def set_image_content_type(self, image_content_type):
        """Set note image content type."""
        self.__image_content_type = image_content_type

    security.declareProtected(perm_view, 'get_image_name')
    # No additional comments.
    def get_image_name(self):
        """Return image name."""
        return self.__image_name

    security.declareProtected(perm_add_lo, 'set_image_name')
    def set_image_name(self, image_name):
        """Set note image name."""
        self.__image_name = strip_tags(image_name, [])

    security.declareProtected(perm_view, 'get_tt_icon')
    # No additional comments.
    def get_tt_icon(self):
        """Return thinking type icon."""
        return self.tt_ref.get_icon()

    security.declarePrivate('set_tt')
    def set_tt(self,tt_ref):
        self.tt_ref=tt_ref

    security.declarePrivate('get_tt_icon_url_postfix')
    # For ZCatalog (catalog_notes defined in CourseManager)
    def get_tt_icon_url_postfix(self):
        c = self.find_course()
        cc = self.find_course_context()
        tts = cc.get_thinking_type_set()
        return '/'.join(['courses', c.get_id(), cc.get_id(), tts.get_id(),
                         self.get_tt_id(), 'type_icon'])


    def __get_tt_icon_url(self, REQUEST):
        """Return url for thinking type icon."""
        tts = self.get_thinking_type_set()
        return '/'.join((self.find_URL_of_course_context(REQUEST),
                        tts.get_id(),
                        self.get_tt_id(),
                        'type_icon'))

    security.declareProtected(perm_view, 'get_tt_icon_tag')
    # No additional comments.
    def get_tt_icon_tag(self, REQUEST):
        """Return html img tag that displays thinking type icon."""
        # So let's do the img tag ourselves, (yes we loose
        # width and height attributes...) --jmp 2001-10-10
        url = self.__get_tt_icon_url(REQUEST)
        return '<img src="%s" alt="" border="0" />' % url

    security.declareProtected(perm_view, 'get_tt_id')
    # No additional comments.
    def get_tt_id(self):
        """Return thinking type id."""
        return self.tt_ref.get_id()

    security.declareProtected(perm_view, 'get_tt_name')
    # No additional comments.
    def get_tt_name(self):
        """Return thingking type name."""
        return self.tt_ref.get_name()

    security.declareProtected(perm_view, 'get_possible_follow_ups')
    def get_possible_follow_ups(self):
        """Return thinking types that can follow Note's thinking type."""
        return self.get_thinking_type_set().get_possible_follow_ups(self.tt_ref)

    security.declareProtected(perm_view, 'get_tt_abbreviation')
    # This method is not used yet...
    def get_tt_abbreviation(self):
        """Return thinking type abbreviation."""
        return self.tt_ref.get_abbreviation()

    security.declareProtected(perm_view, 'get_tt_colour')
    def get_tt_colour(self):
        """Return thinking type colour."""
        return self.tt_ref.get_colour()

    security.declareProtected(perm_view, 'get_tt_ref')
    def get_tt_ref(self):
        """Return a reference to ThinkingType."""
        return self.tt_ref

    security.declarePrivate('uncache_notes')
    def uncache_notes(self):
        if not self.is_starting_note():
            self.parent().uncache_notes()
        else:
            if hasattr(self,'__cached_n_notes'):
                del self.__cached_n_notes
            if hasattr(self,'__cached_n_unread_notes'):
                del self.__cached_n_unread_notes

    security.declareProtected(perm_view, 'get_n_notes')
    # No additional comments.
    def get_n_notes(self):
        """Return number of children notes + 1 (=self)"""
        top = self.is_starting_note()
        if top:
            if hasattr(self,'__cached_n_notes'):
                return self.__cached_n_notes

        n = 1 # Note itself
        for note in self.get_children('Note'):
            n += note.get_n_notes()

        if top:
            self.__cached_n_notes = n

        return n

    security.declarePrivate('uncache_unread_notes')
    def uncache_unread_notes(self,uname):
        if not self.is_starting_note():
            self.parent().uncache_unread_notes(uname)
        else:
            if hasattr(self,'__cached_n_unread_notes'):
                if uname in self.__cached_n_unread_notes.keys():
                    del self.__cached_n_unread_notes[uname]

    security.declareProtected(perm_view, 'get_n_unread_notes')
    # Container-recursive method.
    def get_n_unread_notes(self, uname):
        """Return number of unread children notes + 1 (=self (if unread)))"""
        top = self.is_starting_note()
        if top:
            if hasattr(self,'__cached_n_unread_notes'):
                if uname in self.__cached_n_unread_notes.keys():
                    return self.__cached_n_unread_notes[uname]
            else:
                self.__cached_n_unread_notes={}

        n = 0
        if not self.is_reader(uname): n = 1
        for note in self.get_children('Note'):
            n += note.get_n_unread_notes(uname)

        if top:
            self.__cached_n_unread_notes[uname]=n
        return n

    security.declareProtected(perm_view, 'get_all_unread_children')
    # When you call this from the DTML, give course context but not
    # any path....
    # FIXME: Make a wrapper to make things more beautiful... --jmp 2001-10-16
    def get_all_unread_children(self, REQUEST, path=None, cc=None):
        """Return a list of all children that are unread."""
        if path is None:
            path = REQUEST.URL1 + '/' + cc.get_id() + '/' + self.get_id()

        reader = repr(REQUEST.AUTHENTICATED_USER)
        retval = []

        for note in self.get_children('Note'):
            if not note.is_reader(reader):
                retval.append([note,path + '/' + note.get_id()])
            retval += note.get_all_unread_children(REQUEST, path + '/' + note.get_id())
        return retval

    security.declareProtected(perm_view, 'mark_all_notes_read')
    def mark_all_notes_read(self, REQUEST):
        """Mark all notes as read in this thread (by current user)"""
        note = self
        while not note.is_starting_note():
            note = note.parent()
        note.__mark_all_children_read(str(REQUEST.AUTHENTICATED_USER))

        self.get_lang(('common', 'kb'), REQUEST)
        return self.message_dialog(
            self, REQUEST,
            title=REQUEST['L_unread_to_read_msg'],
            message=REQUEST['L_unread_to_read_msg'],
            action='index_html')

    def __mark_all_children_read(self, uname):
        if not self.is_reader(uname):
            self.update_reader(uname)
        for note in self.get_children('Note'):
            note.__mark_all_children_read(uname)

    security.declareProtected(perm_manage, 'reload_dtml')
    # Add new DTML-docs here
    def reload_dtml(self, REQUEST=None):
        """Reload dtml files from the file system."""
        NoteDTML.reload_dtml(self)
        reload_dtml(self, self.dtml_files)

    security.declareProtected(perm_add_lo, 'set_temporary')
    def set_temporary(self, bool):
        """Set this NOTE object as temporary."""
        self.__temporary = not not bool

    security.declareProtected(perm_view, 'is_temporary')
    def is_temporary(self):
        """Return boolean depending on if note is temporary, or not."""
        return self.__temporary

    security.declareProtected(perm_add_lo, 'preview_form_handler')
    def preview_form_handler(self, REQUEST,
        edit='',
        cancel='',
        post='',
        ):
        """Preview handler. If post, the note is just changed from
        temporary to current. If edit, we jump back a bit, etc.."""
        if edit:
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST,
                'edit_form'))
        elif cancel:
            # Delete self.
            try:
                self.do_cancel()
            except:
                pass
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST,
                '../../index_html'))
        elif post:
            self.do_publish()
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST,
                # Ugly hack.
                '../../%s/index_html'%self.get_id()))
        else:
            raise 'FLE Error', 'This should not happen.'

    security.declarePrivate('do_publish')
    def do_publish(self):
        self.set_temporary(0)
        self.uncache_notes()
        self.parent().move_from_tmp(self)

    security.declarePrivate('do_cancel')
    def do_cancel(self):
        self.parent().delete_from_tmp(self)

    security.declareProtected(perm_view, 'may_censor_note')
    def may_censor_note(self, person):
        """Return boolean depending on whether user may or may not
        censor notes."""
        from AccessControl.PermissionRole import rolesForPermissionOn
        if self.get_author()==person:
            return 0
        return intersect_bool(
            get_roles(self,person),
            rolesForPermissionOn(perm_edit,self))

    security.declareProtected(perm_edit, 'censor_note_handler')
    def censor_note_handler(
        self, REQUEST,
        uncensor=None, # This is received from note index page
        censor=None,      #
        explanation='',   # These are received from censor_form
        cancel=None,      #
        ):
        """Handles note censorship."""
        if censor:
            import time
            self.do_censor(time.time(),str(REQUEST.AUTHENTICATED_USER),strip_tags(explanation))
            if REQUEST:
                self.get_lang(('common','kb'),REQUEST)
                return self.message_dialog(
                    self, REQUEST,
                    title=REQUEST['L_removed_msg'],
                    message=REQUEST['L_removed_msg'],
                    action='index_html')
        elif cancel:
            if REQUEST:
                REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))
        elif uncensor:
            self.do_uncensor()
            if REQUEST:
                REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))
        else:
            raise 'FLE Error','Unknown button'

    def do_censor(self,time,user,explanation):
        self.censored=time
        self.censorer=user
        self.censor_reason=explanation

    def do_uncensor(self):
        self.censored=0
        del self.censorer
        del self.censor_reason

    # FIXME: remove most of the defaulted method arguments, because we
    # FIXME: take the form values anyways from REQUEST object.
    security.declareProtected(perm_add_lo, 'edit_note_form_handler')
    def edit_note_form_handler(
        self, REQUEST,
        subject='',
        body='',
        image=None,
        image_name='',
        url='',
        url_name='',
        tt_id_new='',
        # cancel, preview and change_tt are button actions
        cancel='',
        go_back='',
        preview='',
        change_tt='',
        ):
        """Handle note edits."""
        user = self.fle_users.get_user_info(str(REQUEST.AUTHENTICATED_USER))
        self.get_lang(('common', 'kb'), REQUEST)
        if cancel:
            # Delete self.
            try:
                self.do_cancel()
            except:
                pass
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST,
                '../../index_html'))
        elif go_back:
            user.register_edit(str(REQUEST.URL))
            self.store_edit(REQUEST)
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST,
               '../../index_html'))
        elif preview or change_tt:
            # Both buttons will need to commit all changes to the form,
            # so we start with both of them and diverge later on...
            errors = []

            errors = self.store_edit(REQUEST)

            if preview and len(errors) > 0:
                # Only display errors when trying to go to preview
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_input'],
                    message=REQUEST['L_invalid_fields'] + ": '" + \
                    "' , '".join(errors) + "'",
                    action='edit_form')
                    #action='edit_form?subject=%s&body=%s&my_url=%s&url_name=%s&image_name=%s' % tuple(
                    #[quote_plus(x) for x in (subject, body,
                    #                         url, url_name, image_name)]))
            if change_tt:
                a=self.get_body().replace('\n','').replace('\r','').replace(' ','')
                b=self.tt_ref.get_starting_phrase().replace('\n','').replace('\r','').replace(' ','')
                #raise 'foo',repr(a)+'/'+repr(b)+'/'+str(len(a))+'/'+str(len(b))
                self.set_tt(self.tts_ref.get_thinking_type(tt_id_new))
                if a==b:
                    self.set_body(self.tt_ref.get_starting_phrase())
                REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'edit_form'))
            else:
                REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'preview_form'))


        else:
            #raise 'FLE Error', 'This should not happen.'
            # Assume continued editing session ...
            #return self.edit_form(REQUEST)
            REQUEST.RESPONSE.redirect(self.state_href(
               REQUEST,
               'edit_form'))

    security.declarePrivate('store_edit')
    def store_edit(self, req):
        """Store note contents."""
        errors = []

        for s in ('subject', 'url', 'url_name', 'image_name'):
            e = req.get(s)
            req.set(s, e.strip())

        if not is_valid_title(req.get('subject')):
            errors.append(req['L_title_of_note'])

        original_body = req.get('body')
        body = strip_tags(original_body, allowed_tags_in_notes)
        req.set('body', body)
        if body != original_body:
            errors.append(req['L_message_body'])

        if req.get('url') and not is_valid_url(req.get('url')):
            errors.append(req['L_add_link'])

        if req.get('url_name') and \
           not is_valid_title(req.get('url_name')):
            errors.append(req['L_title_of_link'])

        if req.get('image_name') and not \
           is_valid_title(req.get('image_name')):
            errors.append(req['L_title_of_image'])

        # Set image before handling (possible) return of
        # error message dialog, so that image will not be lost.
        image = req.get('image')
        if image is not None and hasattr(image,'filename'):
            if len(image.filename) > 0:
                self.set_image_data(image.read())
                self.set_image_content_type(
                   image.headers['content-type'])

        self.set_subject(req.get('subject'))
        self.set_body(req.get('body'))
        if req.get('url') is not None:
            self.set_url(req.get('url'))
        if req.get('url_name') is not None:
            self.set_url_name(req.get('url_name'))
        if req.get('image_name'):
            self.set_image_name(req.get('image_name'))

        return errors


    def touchgraph_data(self):
        data=self.write_touchgraph_data(self,"NOTE","Note",self.get_tt_id())
        for note in self.objectValues("Note"):
            data=data+note.touchgraph_data()
        return data


Globals.InitializeClass(Note)
# EOF
