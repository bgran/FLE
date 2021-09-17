# $Id: JamArtefact.py,v 1.31 2003/06/13 07:57:11 jmp Exp $

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

__version__ = '$Revision: 1.31 $'[11:-2]

from types import StringType
import time
try:
    from PIL import Image
    PIL_imported = 1
except ImportError:
    PIL_imported = 0
import cStringIO

import OFS
import Globals
from Globals import Persistent
from AccessControl import ClassSecurityInfo
from Products.ZCatalog.CatalogAwareness import CatalogAware

from Thread import EventManager
from TraversableWrapper import Traversable
from common import add_dtml, reload_dtml, intersect_bool, get_roles
from common import perm_view, perm_edit, perm_manage, perm_add_lo
from common import roles_admin
from common import roles_student, roles_tutor, roles_teacher
from input_checks import render, normal_entry_tags

class JamArtefact(
    CatalogAware,
    Traversable,
    Persistent,
    EventManager,
    OFS.Folder.Folder,
    OFS.SimpleItem.Item
    ):
    """JamArtefact"""
    meta_type = 'JamArtefact'

    security= ClassSecurityInfo()
    security.declareObjectPublic()

    dtml_files = (
        ('jam_artefact_index_html', 'Index page', 'ui/JamArtefact/index_html'),
        ('add_annotation_form', '', 'ui/JamArtefact/add_annotation_form'),
        )

    def __init__(self, id_, parent_ids, name, data, content_type, author=None):
        self.id = id_
        self.title = name

        EventManager.__init__(self)

        self.__name = name
        self.__data = data
        self.__censored = 0
        self.__content_type = content_type

        self.default_catalog = 'catalog_jam_artefacts'

        icon_type = self.icon_type_from_mime_type(content_type)
        
        if icon_type == 'image':
            if not PIL_imported:
                print "Can't create thumbnail image. PIL not installed."
            try:
                s = cStringIO.StringIO(data)
                im = Image.open(s)
                im.thumbnail((60, 60))
                if im.mode != 'RGB':
                    im = im.convert('RGB')

                s = cStringIO.StringIO()
                im.save(s, "JPEG")
                s.seek(0)
                self.__thumbnail = s.read()
            except:
                self.__icon = 'images/jam_type_img'

        else:
            self.__icon = {'audio'  : 'images/jam_type_sound',
                           'text'   : 'images/jam_type_text',
                           'html'   : 'images/jam_type_html',
                           'video'  : 'images/jam_type_video',
                           'archive': 'images/jam_type_arch',
                           'unknown': 'images/jam_type_no'}[icon_type]

        self.__annotations = []

        if type(parent_ids) == StringType:
            parent_ids = (parent_ids,)
        self.__parent_ids = parent_ids

        if author: self._author = author # pass to manage_afterAdd

        for tup in self.dtml_files:
            add_dtml(self, tup)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """Set default permissions for roles."""

        if hasattr(self, '_author'):
            try:
                self.manage_setLocalRoles(self._author, ('Owner',))
                self.changeOwnership(self.acl_users.getUser(
                    self._author).__of__(self.acl_users))
            except AttributeError:
                pass
            del self._author
            
        self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_teacher, 0)
        self.manage_permission(perm_add_lo, roles_student, 0)
        self.manage_permission(perm_view, roles_student, 0)

        self.index_object() # Add JamArtefact to ZCatalog

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

    security.declareProtected(perm_view, 'index_html')
    def index_html(self, REQUEST):
        """Update reader status before showing the page."""
        uname = str(REQUEST.AUTHENTICATED_USER)
        self.update_reader(uname)
        self.uncache_unread_artefacts(uname)
        return self.jam_artefact_index_html(self, REQUEST)


    security.declarePrivate('icon_type_from_mime_type')
    def icon_type_from_mime_type(self, mime_type):
        """Return type ('image', 'audio', 'text', 'html', 'video',
        'archive', or 'unknown')"""

        try:
            sub_type = mime_type[mime_type.find('/')+1:]
            main_type = mime_type[:mime_type.find('/')]

            if main_type == 'image': return 'image'
            elif main_type == 'audio': return 'audio'
            elif main_type == 'text':
                if sub_type == 'html': return 'html'
                else: return 'text'
            elif main_type == 'video': return 'video'
            elif main_type == 'application' and \
                 sub_type in ('gnutar', 'zip', 'x-compress', 'x-compressed',
                              'x-gtar', 'x-tar', 'x-zip', 'x-zip-compressed',
                              'x-shar', 'x-bzip', 'x-bzip2', 'x-cpio'):
                return 'archive'
            else: return 'unknown'
        except AttributeError:
            # mime_type is none, possibly importing old version
            return 'unknown'

    security.declareProtected(perm_view, 'get_children_artefacts')
    def get_children_artefacts(self):
        """Return a list of children artefacts."""
        children = []
        for ja in self.parent().get_children('JamArtefact'):
            if self.get_id() in ja.get_parent_ids():
                children.append(ja)

        return children

    security.declareProtected(perm_view, 'get_name')
    def get_name(self, REQUEST=None):
        """Return name of the artefact."""
        prefix = ''
        if self.__censored:
            if REQUEST:
                uname = str(REQUEST.AUTHENTICATED_USER)
                self.get_lang(('jam',),REQUEST)
                prefix = REQUEST['L_removed_name']
            else:
                prefix = 'REMOVED'
                uname=''

            # If the person is not the author and is not a teacher,
            # we only show the prefix (the censored notice)
            if uname!=self.get_author() and \
               not self.may_censor_jam_artefact(uname):
                return prefix

            prefix = prefix + ' / '

        return prefix + self.__name


    # Return real name of the artefact, even when the artefact is censored.
    security.declarePrivate('get_real_name')
    def get_real_name(self):
        """Return name of the artefact."""
        return self.__name

    security.declareProtected(perm_view, 'get_data')
    def get_data(self, REQUEST=None):
        """Return actual data."""

        if self.__censored:
            if not REQUEST or \
               not self.may_censor_jam_artefact(
                str(REQUEST.AUTHENTICATED_USER)): return None

        if REQUEST:
            self.update_reader(str(REQUEST.AUTHENTICATED_USER))

        if REQUEST and REQUEST.RESPONSE:
            REQUEST.RESPONSE.setHeader('Content-Type', self.__content_type)
        return self.__data

    security.declarePrivate('get_real_data')
    def get_real_data(self):
        """Return actual data."""
        return self.__data

    security.declareProtected(perm_view, 'get_content_type')
    def get_content_type(self):
        """Return content type."""
        return self.__content_type

    security.declareProtected(perm_view, 'get_artefact_type')
    def get_artefact_type(self):
        """Return type of the artefact."""
        return self.icon_type_from_mime_type(self.get_content_type())

    security.declareProtected(perm_view, 'get_icon')
    def get_icon(self, REQUEST, RESPONSE):
        """Return icon."""
        if self.__censored:
            return self.unrestrictedTraverse('images/jam_type_censored').data
        elif hasattr(self, '_' + self.__class__.__name__+ '__icon'):
            return self.unrestrictedTraverse(self.__icon).data
        else:
            RESPONSE.setHeader('Content-Type', 'image/jpeg')
            return self.__thumbnail

    security.declareProtected(perm_view, 'get_author')
    def get_author(self):
        """Return author (owner) of this item."""
        return self.getOwner().name

    security.declareProtected(perm_view, 'get_n_annotations')
    def get_n_annotations(self):
        """Return the number of annotations."""
        return len(self.__annotations)

    security.declareProtected(perm_view, 'get_n_censored_annotations')
    def get_n_censored_annotations(self):
        """Return the number of censored annotations."""
        n = 0
        for t in self.__annotations:
            if t[3]: n += 1
        return n

    security.declareProtected(perm_view, 'get_n_uncensored_annotations')
    def get_n_uncensored_annotations(self):
        """Return the number of uncensored annotations."""
        n = 0
        for t in self.__annotations:
            if not t[3]: n += 1
        return n

    security.declareProtected(perm_view, 'get_annotations')
    def get_annotations(self, REQUEST):
        """Return list of annotation tuples."""
        if self.__censored and \
           not self.may_censor_jam_artefact(str(REQUEST.AUTHENTICATED_USER)):
            return []

        # FIXME: This have to be changed when we have censoring
        # FIXME: on the annotation level.
        anns = []
        for (who, when, what, censored, censorer) in self.__annotations:
            if censored:
                self.get_lang(('common','webtop'), REQUEST)
                stamp = time.strftime(REQUEST['L_short_date_format'],
                                      time.localtime(censored))
                prefix = REQUEST['L_removed_annotation_body'] % (censorer, stamp)
                uname = str(REQUEST.AUTHENTICATED_USER)
                if uname != self.get_author() and \
                   not self.may_censor_jam_artefact(uname):
                    what = prefix
                else:
                    what = prefix + \
                           '<hr>' + render(what,
                                           legal_tags=normal_entry_tags,
                                           do_horizontal_space=1)
            else:
                what = render(what,
                              legal_tags=normal_entry_tags,
                              do_horizontal_space=1)

            anns.append((who, when, what, censored, censorer))

        return anns

    # For ZCatalog (catalog_jam_artefacts in CourseManager)
    security.declarePrivate('get_bodies_in_annotations')
    def get_bodies_in_annotations(self):
        """Return all text in all annotations of this JamArtefact."""
        annotations_texts = []
        for a in self.__annotations:
            annotations_texts.append(a[2])
        return ' '.join(annotations_texts)

    # For ZCatalog (catalog_jam_artefacts in CourseManager)
    security.declarePrivate('get_authors_in_annotations')
    def get_authors_in_annotations(self):
        """Return all text in all annotations of this JamArtefact."""
        annotations_authors = []
        for a in self.__annotations:
            annotations_authors.append(a[0])
        return annotations_authors

    # For ZCatalog (catalog_jam_artefacts in CourseManager)
    security.declareProtected(perm_view, 'get_jam_session_name')
    def get_jam_session_name(self):
        """Return name of the JamSession."""
        return self.parent().get_name()

    security.declarePrivate('get_real_annotations')
    def get_real_annotations(self):
        """Return list of annotation tuples."""
        return self.__annotations

    security.declarePrivate('add_annotation')
    def add_annotation(self, uname, annotation_time, annotation_text):
        """Add annotation to JamArtefact."""

        # annotation censorship
        censored = 0
        censorer = ''

        # uname and annotation_time can be used as a key attribute
        self.__annotations.append((uname, annotation_time, annotation_text,
                                   censored, censorer))
        self._p_changed = 1
        self.reindex_object()

    security.declarePrivate('do_censor_annotations')
    def do_censor_annotations(self, annotation_indexes, time, user):
        """Censor annotation."""
        for i in [int(x) for x in annotation_indexes]:
            t = self.__annotations[i]
            self.__annotations[i] = (t[0], t[1], t[2], time, user)
        self._p_changed = 1

    security.declarePrivate('do_uncensor_annotations')
    def do_uncensor_annotations(self, annotation_indexes):
        """Uncensor annotation."""
        for i in [int(x) for x in annotation_indexes]:
            t = self.__annotations[i]
            self.__annotations[i] = (t[0], t[1], t[2], 0, '')
        self._p_changed = 1

    security.declareProtected(perm_add_lo, 'add_annotation_form_handler')
    def add_annotation_form_handler(
        self,
        REQUEST,
        annotation_text,
        submit = '', # form buttons
        cancel = '', #
        ):
        """Add annotation form handler."""

        user = str(REQUEST.AUTHENTICATED_USER)

        if self.__censored and not self.may_censor_jam_artefact(user):
            raise 'FLE Error', "I don't want to anything."

        if submit:
            time_now = time.time()
            # FIXME: report that annotation_text doesn't work
            if annotation_text:
                self.add_annotation(user, time_now, annotation_text)
        elif cancel:
            pass
        else:
            raise 'FLE Error', 'Unknown button.' # Should never happen.

        REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))


    security.declareProtected(perm_view, 'get_parent_ids')
    def get_parent_ids(self):
        """Return a list of parent ids."""
        if type(self.__parent_ids) == StringType:
            return (self.__parent_ids,)
        else:
            return self.__parent_ids

    security.declarePrivate('set_parent_ids')
    def set_parent_ids(self, parent_ids):
        """Set parent ids."""
        self.__parent_ids = parent_ids

    security.declareProtected(perm_view, 'may_censor_jam_artefact')
    def may_censor_jam_artefact(self, person):
        """Return boolean depending on whether user may or may not
        censor jam artefacts."""
        from AccessControl.PermissionRole import rolesForPermissionOn
        return intersect_bool(
            get_roles(self, person),
            rolesForPermissionOn(perm_edit, self))

    security.declareProtected(perm_edit, 'censor_jam_artefact_handler')
    def censor_jam_artefact_handler(
        self, REQUEST,
        censor=None,               # buttons in jam artefact page
        uncensor=None,             #
        censor_annotations=None,   #
        uncensor_annotations=None, #
        verify=None,               # buttons in verify page
        verify_annotations=None,   #
        cancel=None,               #
        annotation_indexes=(),
        ):
        """Handles jam_artefact censorship."""
        if type(annotation_indexes) == StringType:
            annotation_indexes = (annotation_indexes,)

        if verify:
            import time
            self.do_censor(time.time(),str(REQUEST.AUTHENTICATED_USER))
            if REQUEST:
                self.get_lang(('common', 'jam'), REQUEST)
                return self.message_dialog(
                    self, REQUEST,
                    title=REQUEST['L_removed_msg'],
                    message=REQUEST['L_removed_msg'],
                    action='index_html')
        if verify_annotations:
            import time
            print '---'
            print annotation_indexes
            self.do_censor_annotations(annotation_indexes,
                                       time.time(),
                                       str(REQUEST.AUTHENTICATED_USER))
            if REQUEST:
                self.get_lang(('common', 'jam'), REQUEST)
                return self.message_dialog(
                    self, REQUEST,
                    title=REQUEST['L_removed_annotation_msg'],
                    message=REQUEST['L_removed_annotation_msg'],
                    action='index_html')
        elif cancel:
            if REQUEST:
                REQUEST.RESPONSE.redirect(
                    self.state_href(REQUEST, 'index_html'))
        elif uncensor:
            self.do_uncensor()
            if REQUEST:
                REQUEST.RESPONSE.redirect(
                    self.state_href(REQUEST, 'index_html'))
        elif uncensor_annotations:
            self.do_uncensor_annotations(annotation_indexes)
            if REQUEST:
                REQUEST.RESPONSE.redirect(
                    self.state_href(REQUEST, 'index_html'))
        elif censor:
            if REQUEST:
                self.get_lang(('common', 'jam'), REQUEST)
                return self.message_dialog2(
                    self, REQUEST,
                    title=REQUEST['L_warning'],
                    message=REQUEST['L_remove_verify'],
                    handler='censor_jam_artefact_handler',
                    extra_value_name='jam_artefact',
                    extra_values=(str(self.get_id()),),
                    option1_value = REQUEST['L_cancel'],
                    option1_name = 'cancel',
                    option2_value = REQUEST['L_ok'],
                    option2_name = 'verify')
        elif censor_annotations:
            if REQUEST:
                self.get_lang(('common', 'jam'), REQUEST)
                return self.message_dialog2(
                    self, REQUEST,
                    title=REQUEST['L_warning'],
                    message=REQUEST['L_remove_annotations_verify'],
                    handler='censor_jam_artefact_handler',
                    extra_value_name='annotation_indexes',
                    extra_values=annotation_indexes,
                    option1_value = REQUEST['L_cancel'],
                    option1_name = 'cancel',
                    option2_value = REQUEST['L_ok'],
                    option2_name = 'verify_annotations')
        else:
            raise 'FLE Error', 'Unknown button'

    def do_censor(self, time, user):
        self.__censored = time
        self.__censorer = user

    def do_uncensor(self):
        self.__censored = 0
        del self.__censorer

    security.declareProtected(perm_view, 'is_censored')
    def is_censored(self):
        """Return whether this jam artefact is censored."""
        return not not self.__censored

    security.declareProtected(perm_view, 'get_censor_time')
    def get_censor_time(self, REQUEST):
        """Return time when the artefact was censored."""
        self.get_lang(('common',), REQUEST)
        return time.strftime(REQUEST['L_short_date_format'],
                             time.localtime(self.__censored))

    security.declareProtected(perm_view, 'get_censorer')
    def get_censorer(self):
        """Return person who censored the artefact."""
        return self.__censorer

Globals.default__class_init__(JamArtefact)

# EOF
