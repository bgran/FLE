# $Id: Jamming.py,v 1.29 2003/06/13 07:57:11 jmp Exp $
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

"""Contains class Jamming, which has a number of JamSessions."""

__version__ = '$Revision: 1.29 $'[11:-2]

import time
import OFS, Globals
from Globals import Persistent
from AccessControl import ClassSecurityInfo

from Cruft import Cruft
from JamSessionLinear import JamSessionLinear
from JamSessionTree import JamSessionTree
from JamSessionGraph import JamSessionGraph
from TraversableWrapper import Traversable
from common import add_dtml, reload_dtml, intersect_bool, make_action
from common import perm_view, perm_edit, perm_manage, perm_add_lo
from input_checks import is_valid_title

"""A container for JamSessions. The only reason we really need this
class is for implementing Jamming tab by using own fle_html_header here."""
class Jamming(
    Traversable,
    Cruft, # for find_URL_of_fle_root()
    Persistent,
    OFS.Folder.Folder,
    ):
    """Jamming, contained within Course, represents jamming for
    one course."""
    meta_type = 'Jamming'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    dtml_files = (
        ('index_html', 'Index page', 'ui/Jamming/index_html'),
        ('add_jam_session_form', '', 'ui/Jamming/add_jam_session_form'),
        ('fle_html_header', 'Standard FLE Html Header (JM)',
         'ui/Jamming/fle_html_header'),
        ('fle_form_header', 'Standard FLE Form Header (JM)',
         'ui/Jamming/fle_form_header'),

        ('jam_search', '', 'ui/Jamming/jam_search'),
        ('jam_search_results', '', 'ui/Jamming/jam_search_results'),

        )

    def __init__(self, id_):
        """Constructor of the Jamming."""
        self.id = id_
        self.title = 'Jamming, container for JamSessions'

        # This is for group folder path listings - show path up to jamming.
        self.toplevel = 1

        for tup in self.dtml_files:
            add_dtml(self, tup)

    security.declareProtected(perm_manage, 'reload_dtml')
    # No additional comments.
    def reload_dtml(self, REQUEST=None):
        """Reload dtml files from the file system."""
        reload_dtml(self, self.dtml_files)

        if REQUEST:
            self.get_lang(('common',),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_dtml_reloaded'],
                message=REQUEST['L_dtml_files_reloaded'],
                action='index_html')

    security.declareProtected(perm_view, 'get_bg_colour_name')
    def get_bg_colour_name(self):
        """..."""
        return 'bl'

    def get_name(self):
        """Get course name."""
        return "jamming"

    security.declareProtected(perm_view, 'get_n_jam_sessions')
    def get_n_jam_sessions(self):
        """Return number of JamSessions in (the jamming of) this course."""
        return len(self.get_children('JamSession'))

    security.declareProtected(perm_add_lo, 'form_handler')
    def form_handler(
        self,
        my_name = '',
        type = None, # 'linear', 'tree', or 'graph'
        description = None,
        artefact_name = None,
        artefact_upload = None,
        annotation = '',
        submit = '', # submit buttons
        cancel = '', #
        called_from_import_code = 0,
        REQUEST = None,
        ):
        """Form handler for creating new JamSession."""
        if submit:
            if type == 'graph' and not self.has_PIL():
                # Users are not able to select graph type from UI if PIL is
                # not installed so this never happens unless input is hacked.
                raise 'FLE Error', 'PIL not installed'

            error_fields = []
            if REQUEST:
                self.get_lang(('common', 'jam'), REQUEST)

            my_name = my_name.strip()
            if not is_valid_title(my_name):
                error_fields.append(REQUEST['L_title_of_jam_session'])

            if not description:
                error_fields.append(REQUEST['L_description_of_jam_session'])

            if type not in ('linear', 'tree', 'graph'):
                error_fields.append(REQUEST['L_type_of_jam_session'])

            if not artefact_upload or len(artefact_upload.filename)==0:
                error_fields.append(REQUEST['L_upload_the_starting_artefact'])
            if not is_valid_title(artefact_name):
                error_fields.append(REQUEST['L_title_of_the_starting_artefact'])

            if len(error_fields) > 0:
                msg = REQUEST['L_invalid_fields'] + ": '" + \
                      "' , '".join(error_fields) + "'"
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_input'],
                    message=msg,
                    action=apply(
                    make_action,
                    ['add_jam_session_form'] +
                    [(x, eval(x)) for x in
                     ('my_name', 'description', 'type', 'artefact_name',
                      'annotation')]))

            data = artefact_upload.read()
            try:
                content_type = artefact_upload.headers['content-type']
            except KeyError:
                content_type = ''

            id_ = 'js' + self.parent().parent().generate_id()

            jam_session_class = {'linear': JamSessionLinear,
                                 'tree': JamSessionTree,
                                 'graph': JamSessionGraph}[type]

            if REQUEST: uname = str(REQUEST.AUTHENTICATED_USER)
            else: uname = None

            self._setObject(id_, jam_session_class(
                id_,
                my_name,
                description,
                artefact_name, # starting artefact
                data,          #
                content_type,  #
                author=uname,
                ))

            if REQUEST:
                ja = self._getOb(id_).get_children('JamArtefact')[0]
                ja.update_reader(uname)
                if annotation:
                    ja.add_annotation(uname, time.time(), annotation)
        elif cancel:
            pass
        else:
            raise 'FLE Error', 'Unknown button' # Should never happen.

        if not called_from_import_code and REQUEST:
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))
        else: # import code
            return self.get_child(id_)

    security.declareProtected(perm_view, 'search_form_handler')
    def search_form_handler(
        self,
        REQUEST,
        cancel=None, # submit buttons
        submit=None, #
        ):
        """Search form handler."""

        if submit:
            for s in 'get_name', 'get_bodies_in_annotations':
                REQUEST.set(s, REQUEST[s])

            if REQUEST['get_course_id'] == '___any___':
                REQUEST.set('get_course_id', [x.get_id() for x in \
                                              self.fle_users.get_user_info(
                    str(REQUEST.AUTHENTICATED_USER)).user_courses()])
            else:
                REQUEST.set('get_course_id', REQUEST['get_course_id'])

            if REQUEST['get_author'] == '___anyone___':
                REQUEST.set('get_author', self.get_all_users_id())
            else:
                REQUEST.set('get_author', REQUEST['get_author'])

            if REQUEST['get_artefact_type'] == '___any___':
                REQUEST.set('get_artefact_type', '')
            else:
                REQUEST.set('get_artefact_type', REQUEST['get_artefact_type'])

            if REQUEST['get_authors_in_annotations'] == '___anyone___':
                REQUEST.set('get_authors_in_annotations', '')
            else:
                REQUEST.set('get_authors_in_annotations',
                            REQUEST['get_authors_in_annotations'])

            return self.jam_search_results(self, REQUEST)

        elif cancel:
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))
        else:
            raise 'FLE Error', 'Unknown button'


Globals.default__class_init__(Jamming)

# EOF

