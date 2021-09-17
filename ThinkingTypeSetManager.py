# $Id: ThinkingTypeSetManager.py,v 1.55 2005/01/25 20:20:39 tarmo Exp $
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

"""Contains class ThinkingTypeSetManager, which is a holder and factory object for ThinkingTypeSets."""

__version__ = '$Revision: 1.55 $'[11:-2]

import OFS, Globals, AccessControl
from Globals import Persistent

from TraversableWrapper import TraversableWrapper as TW
from Cruft import Cruft
from CourseManager import IDManager

from common import reload_dtml, add_dtml, iterate_fle_path
from common import perm_view, perm_edit, perm_manage, perm_add_lo
from TempObjectManager import TempObjectManager

# This is located in FLE/global_thinking_types and contains globally
# available ThinkingTypeSets. Each course can select one or more
# of these sets, which are then _copied_ into the course, where
# they can be edited independently of the global sets.
#
# Edited sets can be recopied back to global types so they can be
# used in other courses.
class ThinkingTypeSetManager(
    OFS.Folder.Folder,
    TW,
    Cruft,
    Persistent,
    AccessControl.Role.RoleManager,
    IDManager,
    TempObjectManager,
    OFS.SimpleItem.Item):
    """ThinkingTypeSetManager, contains globally available ThinkingTypeSets"""
    meta_type = 'ThinkingTypeSetManager'
    security = AccessControl.ClassSecurityInfo()

    dtml_files = (
        ('index_html', 'Index page',
         'ui/ThinkingTypeSetManager/index_html'),
        ('fle_html_header', '',
         'ui/ThinkingTypeSetManager/fle_html_header'),
        ('fle_form_header', '',
         'ui/ThinkingTypeSet/fle_form_header'),
        ('import_form', '',
         'ui/ThinkingTypeSetManager/import_form'),
        )

    def __init__(self, id, title):
        """Construct ThinkingTypeSetManager."""
        self.id = id
        self.title = title
        IDManager.__init__(self)


    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """Set default permissions for roles."""
        from common import roles_admin, roles_staff, roles_user

        self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_staff, 0)
        self.manage_permission(perm_add_lo, roles_staff, 0)
        self.manage_permission(perm_view, roles_staff, 0)

        for tup in self.dtml_files:
            add_dtml(self, tup)

        TempObjectManager.manage_afterAdd(self,item,container)

    security.declarePrivate('get_new_valid_tts_id')
    def get_new_valid_tts_id(self):
        """Tries to locate a free id of the format "ttsNN"."""
        while 1:
            tid = "tts" + self.generate_id()
            if not self.is_valid_tts(tid):
                return tid

    security.declarePrivate('load_default_sets')
    def load_default_sets(self):
        """Add default default thinking types."""
        iterate_fle_path('types', '.py', self.__add_ttset)

    def __add_ttset(self, file):
        """Add thinking type set to this very nice manager-a."""
        import sys, os
        from common import file_path
        sys.path.insert(0, os.path.join(file_path, 'types'))
        try:
            file = file[:-len('.py')]
            try:
                obj = __import__(file)
                reload(obj)
            except ImportError, err:
                raise Exception, (sys.path, file)
        finally:
            del sys.path[0]

        from ThinkingTypeSet import ThinkingTypeSet as TTS
        if hasattr(obj,'description'):
            descr=obj.description
        else:
            descr=''
        if hasattr(obj,'translated_from'):
            frm=obj.translated_from
        else:
            frm=obj.name
        tts = TTS(
            file, obj.name, frm, obj.language, descr, obj.types, obj.thread_start, obj.relations)
        # Remove possibly previously existing set
        if hasattr(self,file):
            self.manage_delObjects(file)
        self._setObject(file, tts)

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
    security.declareProtected(perm_view, 'get_thinking_type_sets')
    def get_thinking_type_sets(self):
        """Return a list of usable ThinkingTypeSet objects
        in this manager."""
        return self.get_children('ThinkingTypeSet')

    # This is called from ui/Course/add_course_context_form.dtml and
    # as an user adding a course context is not necessary staff we
    # have to make this public.
    security.declarePublic('get_thinking_type_sets_sorted')
    def get_thinking_type_sets_sorted(self):
        """Same as get_thinking_type_sets, but the first entry in list is
        always the coi thinkingtypeset."""
        rv = self.get_thinking_type_sets()
        def sorter(x, y):
            if x.get_id() == "coi":
                return -1
            else:
                return 0
        rv.sort(sorter)
        return rv

    security.declareProtected(perm_view,'get_thinking_type_sets')
    def get_all_thinking_type_sets(self,REQUEST):
        """Return a list of ThinkingTypeSet objects in this manager."""
        tmps = self.get_tmp_objects()
        user = self.acl_users.getUser(self.get_current_user(REQUEST))
        visible = []
        for set in tmps:
            if 'FLEAdmin' in user.roles \
                   or 'Owner' in user.getRolesInContext(set.aq_base):
                visible += [set,]
        return self.get_thinking_type_sets() + visible

    security.declarePrivate('is_valid_tts')
    def is_valid_tts(self, tts):
        """Test whether tts is a valid Thinking Type Set id."""
        return tts in self.objectIds('ThinkingTypeSet')

    # FIXME: input_checks
    security.declareProtected(perm_edit, 'start_edit_from_existing')
    def start_edit_from_existing(self, REQUEST, tts_id=None):
        """..."""
        if tts_id:
            tts = self.get_object_even_if_tmp(tts_id).make_copy()
        else:
            from ThinkingTypeSet import ThinkingTypeSet
            tts = ThinkingTypeSet(
                id_='foo', # This should disappear after the next two commands!
                orig_name='',
                language='en',
                name='',
                description='',
##                 types=({'id':'T1','name':'T1','starting_phrase':'','description':'','colour':'','icon': "ui/images/types/coi/comment.gif",'icondata':None},),
##                 thread_start=('T1',),
                types=(),
                thread_start=(),
                relations={},
                )
        tid = self.get_new_valid_tts_id()
        tts.set_id(tid)
        self._setObject(tid, tts)
        old_name=tts.get_name()
        if not old_name:
            old_name = 'New'
        tts.set_name(tts.get_name() + ' (' + \
                     self.fle_users.get_user_info(
            self.get_current_user(REQUEST)).get_nickname() + ')')
        tempid = self.move_to_tmp(tts)
        tts = self.get_tmp_object(tempid)
        REQUEST.RESPONSE.redirect(
            self.state_href(REQUEST,
                            self.get_path_to(tts) + '/edit_form_1_3?is_new=1'))


    # FIXME: input_checks
    security.declareProtected(perm_edit, 'form_handler')
    def form_handler(
        self,
        REQUEST,
        sets=None,
        delete='',
        tts_export='',
        ):
        """Handle the typeset front page form input."""
        if sets:
            from types import StringType
            if type(sets) == StringType:
                sets = (sets,)
        else:
            self.get_lang(('common','kb','coursemgmnt'),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_error'],
                message=REQUEST['L_you_didnt_select_type'],
                action='index_html')

        if delete:
            self.get_lang(('common', 'coursemgmnt'),REQUEST)
            return self.message_dialog2(
                self, REQUEST,
                title = REQUEST['L_confirmation'],
                message = REQUEST['L_are_you_sure_tts'] + '<br>' + \
                '<br>'.join(
                [self.get_object_even_if_tmp(si).get_name() for si in sets]),
                handler = 'delete_form_handler',
                extra_value_name = 'sets',
                extra_values = sets,
                option1_value = REQUEST['L_cancel'],
                option1_name = 'cancel',
                option2_value = REQUEST['L_ok'],
                option2_name = 'delete'
                )
        elif tts_export:
            from ImportExport import Exporter
            ex = Exporter("KnowledgeTypes")
            for set_id in sets:
                set = self.get_object_even_if_tmp(set_id)
                ex.exportData(set,ex.exportTypeSet)
            import tempfile, os
            filename = tempfile.mktemp()
            ex.createZip(filename)
            file = open(filename,"rb")
            export_data=file.read()
            file.close()
            os.remove(filename)
            REQUEST.RESPONSE.setHeader('content-type','application/zip')
            return export_data
        else:
            raise 'Form dysfunction'

    security.declareProtected(perm_edit, 'import_form_handler')
    def import_form_handler(
        self,
        REQUEST,
        file,
        tts_import='',
        cancel='',
        ):
        """Form handler for TTS importing."""
        if tts_import:
            from ImportExport import Exporter
            import tempfile, os
            filename = tempfile.mktemp()
            f = open(filename,"w+b")
            f.write(file.read())
            f.close()
            import_data=None
            exported = Exporter("KnowledgeTypes",filename)
            os.remove(filename)

            for telem in exported.root.childNodes:
                exported.importTypeSet(telem,self,force_update=1)

            self.get_lang(('common','kb','coursemgmnt'),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_importing'],
                message=REQUEST['L_typesets_imported'],
                action='index_html')
        REQUEST.RESPONSE.redirect(self.state_href(REQUEST, "index_html"))

    # FIXME: input_checks
    security.declareProtected(perm_edit, 'delete_form_handler')
    def delete_form_handler(
        self,
        REQUEST,
        sets,
        delete='',
        cancel='',
        ):
        """Form handler that is called from message_dialog2."""
        if sets:
            from types import StringType
            if type(sets) == StringType:
                sets = (sets,)
        if delete:
            self.delete_sets(sets)
        elif cancel:
            pass
        else:
            # This code should never be reached.
            raise 'FLE Error', 'Unknown button'

        REQUEST.RESPONSE.redirect(self.state_href(REQUEST, "index_html"))


    security.declarePrivate('delete_sets')
    def delete_sets(self,sets):
        for set in sets:
            obj = self.get_object_even_if_tmp(set)
            if self.is_in_tmp(obj):
                self.delete_from_tmp(obj)
            else:
                self._delObject(set)

    security.declareProtected(perm_view, 'get_all_set_names')
    def get_all_set_names(self):
        """Get a list of all original names of sets."""
        names=[]
        for set in self.get_thinking_type_sets():
            if set.get_original_name() not in names:
                names.append(set.get_original_name())
        return names
            
    security.declareProtected(perm_view, 'get_all_set_languages')
    def get_all_set_languages(self):
        """Get a list of all languages of sets."""
        langs=[]
        for set in self.get_thinking_type_sets():
            if set.get_language() not in langs:
                langs.append(set.get_language())
        return langs

    security.declareProtected(perm_view, 'get_set_by_lang_and_name')
    def get_set_by_lang_and_name(self,lang,original):
        """Return list of objects matching
        the given language and original name."""
        sets=[]
        for set in self.get_thinking_type_sets():
            if set.get_language()==lang and \
               set.get_original_name()==original:
                sets.append(set)
        return sets
    
Globals.InitializeClass(ThinkingTypeSetManager)
# EOF


