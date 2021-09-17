# $Id: CourseManager.py,v 1.163 2005/01/15 11:07:36 tarmo Exp $

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

"""Contains class CourseManager, which acts as a factory object for Courses and also the container for the courses."""

__version__ = '$Revision: 1.163 $'[11:-2]

import re, string, time
import strptime
import OFS, Globals, AccessControl
from Globals import Persistent

from Products.ZCatalog.ZCatalog import ZCatalog

from TraversableWrapper import Traversable, TraversableWrapper
from Course import Course
from common import new_reload_dtml, reload_dtml, add_dtml, iterate_fle_path, \
     quote_html_hack, make_action
from common import perm_view, perm_edit, perm_manage, perm_add_lo, \
     roles_admin, roles_staff, roles_user
from input_checks import is_valid_title
from Thread import Thread
from PrinterManager import PrinterManager
from AccessControl import ClassSecurityInfo
from Cruft import Cruft
from XmlRpcApi import CourseManagerXMLRPC

from common import course_level_roles
from common import roles_teacher, roles_tutor, roles_student

class IDManager(Thread):
    security = ClassSecurityInfo()

    def __init__(self):
        self.__id_counter = 0L
    # Overrides generate_id from Thread!

    security.declarePrivate('generate_id')
    def generate_id(self):
        """Return a probably random integer."""
        self.__id_counter += 1L
        return str(self.__id_counter)

# CourseManager exists in FLE/courses and contains all the courses
# that the FLE installation holds.
class CourseManager(
    OFS.Folder.Folder,
    TraversableWrapper,
    Traversable,
    Cruft,
    Persistent,
    AccessControl.Role.RoleManager,
    OFS.SimpleItem.Item,
    #FilterManager,
    IDManager,
    CourseManagerXMLRPC,
    ):
    """FLE Coursemanager."""
    meta_type = 'CourseManager'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    dtml_files = (
        ('index_html', 'Index page',
         'ui/CourseManager/index_html'),
        ('add_course_form_1_2', 'Add Course Form (1/2)',
         'ui/CourseManager/add_course_form_1_2'),
        ('add_course_form_2_2', 'Add Course Form (2/2)',
         'ui/CourseManager/add_course_form_2_2'),
        ('edit_course_resources', 'Course resource editing',
         'ui/CourseManager/edit_course_resources'),
        ('import_form', 'Import form',
         'ui/CourseManager/import_form'),
        ('note_html', 'Index page of the note',
         'ui/Note/index_html'),
        ('context_html', 'Index page of the course context',
         'ui/CourseContext/index_html'),
        ('course_html', 'Index page of the course',
         'ui/Course/index_html'),
        ('course_selection', '',
         'ui/CourseManager/course_selection'),
        ('course_info', 'Course information page',
         'ui/CourseManager/course_info'),
        ('course_info_content', 'Course information page',
         'ui/CourseManager/course_info_content'),
         ('course_info_jm', 'Course information page in Jamming',
         'ui/CourseManager/course_info_jm'),
        ('kb_search', 'Search', 'ui/Course/kb_search'),
        ('kb_search_results', 'Search Results ',
         'ui/Course/kb_search_results'),

        ('fle_form_header', 'Standard Html Header for forms (CM)',
         'ui/CourseManager/fle_form_header'),

        ('fle_html_header', 'Standard FLE Html Header (CM)',
         'ui/CourseManager/fle_html_header'),


        # Taken from Note.py
        ('describe_thinking_types', '', 'ui/Note/describe_thinking_types'),
        ('edit_form', '', 'ui/Note/edit_form'),
        ('preview_form', 'Preview Form', 'ui/Note/preview_form'),
        ('content', '', 'ui/Note/content'),
        ('list_readers', '', 'ui/Note/list_readers'),
        ('repr_thread', '', 'ui/Note/repr_thread'),
        ('repr_tt', '', 'ui/Note/repr_tt'),
        ('repr_author', '', 'ui/Note/repr_author'),
        ('repr_date', '', 'ui/Note/repr_date'),
        ('censor_form','','ui/Note/censor_form'),
        # Taken from CourseContext.py
        ('edit_course_context_form', '',
         'ui/CourseContext/edit_course_context_form'),
        ('setup_roleplay_form', '',
         'ui/CourseContext/setup_roleplay_form'),
        # For each course:
        ('add_resource_form', '',
         'ui/CourseManager/add_resource_form'),
        ('edit_announcements', '',
         'ui/CourseManager/edit_announcements'),
        ('add_announcement_form', '',
         'ui/CourseManager/add_announcement_form'),
        # GroupFolder, taken from Course.py
        ('wt_add_folder', 'Webtop folder', 'ui/Webtop/wt_add_folder'),
        ('wt_upload'    , 'Upload file'  , 'ui/Webtop/wt_upload'),
        ('wt_add_link'  , 'Add link'     , 'ui/Webtop/wt_add_link'),
        ('wt_add_memo'  , 'Add memo'     , 'ui/Webtop/wt_add_memo'),
        ('wt_view_memo' , 'View memo'    , 'ui/Webtop/wt_view_memo'),
        ('wt_rename'    , 'Rename'       , 'ui/Webtop/wt_rename'),
        # Maptool page
        ('maptool'      , 'Maptool launcher' , 'ui/Course/maptool'),
        )


    # No additional comments.
    def __init__(self, id):
        """Construct Course manager object."""
        self.id = id
        self.title = ''

        IDManager.__init__(self)

        for role in course_level_roles:
            self._addRole(role)

        for tup in self.dtml_files:
            add_dtml(self, tup)

        from common import new_reload_dtml
        #new_reload_dtml(self, self.dtml_files)

        printers = PrinterManager('printers', 'PrinterManager')
        self._setObject('printers', printers)


        catalog = ZCatalog('catalog_jam_artefacts',
                           'ZCatalog for JamArtefacts')
        # indexes
        catalog.addIndex('get_name', 'TextIndex')
        catalog.addIndex('get_artefact_type', 'FieldIndex')
        catalog.addIndex('get_author', 'FieldIndex')
        catalog.addIndex('get_bodies_in_annotations', 'TextIndex')
        catalog.addIndex('get_authors_in_annotations', 'KeywordIndex')
        catalog.addIndex('get_course_id', 'FieldIndex')

        # metadata
        catalog.addColumn('get_name')
        catalog.addColumn('get_author')
        catalog.addColumn('absolute_url')
        catalog.addColumn('get_jam_session_name')

        self._setObject('catalog_jam_artefacts', catalog)


        catalog = ZCatalog('catalog_notes', 'ZCatalog for notes')

        # indexes
        catalog.addIndex('get_subject', 'TextIndex')
        catalog.addIndex('get_body', 'TextIndex')
        catalog.addIndex('get_author', 'FieldIndex')
        catalog.addIndex('get_tt_id', 'FieldIndex')
        # get_thinking_type_set_id acquired from CourseContext
        catalog.addIndex('get_thinking_type_set_id', 'FieldIndex')
        catalog.addIndex('get_course_id', 'FieldIndex')
        catalog.addIndex('get_course_context_id', 'FieldIndex')

        # metadata
        catalog.addColumn('get_subject')
        catalog.addColumn('get_author')
        catalog.addColumn('absolute_url')
        catalog.addColumn('get_course_name')
        catalog.addColumn('get_course_context_name')
        catalog.addColumn('get_tt_colour')
        catalog.addColumn('get_tt_abbreviation')
        catalog.addColumn('get_tt_icon_url_postfix')

        self._setObject('catalog_notes', catalog)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """Set default permissions for roles."""

        self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_staff, 0)
        self.manage_permission(perm_view, roles_user, 0)
        self.manage_permission(perm_add_lo, roles_staff, 0)


    security.declareProtected(perm_manage, 'reload_dtml')
    # No additional comments.
    def reload_dtml(self, REQUEST=None):
        """Reload dtml file from the file system."""
        reload_dtml(self, self.dtml_files)
        if REQUEST:
            self.get_lang(('common','coursemgmnt'),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_dtml_reloaded'],
                message=REQUEST['L_dtml_files_reloaded'],
                action='index_html')

    security.declareProtected(perm_view, 'get_bg_colour_name')
    def get_bg_colour_name(self):
        """Return background colour name code so that we are able
        to pick up right files from images folder."""
        return 'br'

    security.declareProtected(perm_add_lo, 'add_course_impl')
    def add_course_impl(self,teacher):
        """Implementation for add_course."""
        obj = Course(
            self,
            '', # name
            (teacher,),
            '', # desc
            '', # organisation
            '', # methods
            '', # starting_date
            '', # ending_date
            )
        id = obj.id
        self._setObject(id, obj)
        return id

    security.declareProtected(perm_add_lo, 'add_course_form_handler')
    # form handler for add_course_form_1_2.dtml
    def add_course_form_handler(
        self,
        REQUEST,
        course_id, my_name, desc, organisation, methods,
        start_date, end_date,
        creating_new_course='',
        do_groupfolder='',
        do_announcements='',
        cancel='', # submit buttons
        add='',    #
        ):
        """Check user input data."""
        if cancel:
            # cancel button press
            if creating_new_course:
                REQUEST.RESPONSE.redirect(self.state_href(
                    REQUEST, 'index_html'))
            else:
                REQUEST.RESPONSE.redirect(self.state_href(
                    REQUEST, 'course_info?course_id=%s' % course_id))
            return

        elif not add: raise 'FLE Error', 'Unknown button'

        # Ok, add button pressed

        action=apply(
            make_action,
            ['add_course_form_1_2'] +
            [(x, eval(x)) for x in
             ('my_name', 'desc', 'organisation', 'methods',
              'start_date', 'end_date', 'do_groupfolder')])
        if course_id:
            action += '&course_id=' + course_id
        else:
            action += '&creating_new_course=1'

        my_name=my_name.strip()
        if not is_valid_title(my_name):
            self.get_lang(('common','coursemgmnt'),REQUEST)
            return self.message_dialog_error(
                self, REQUEST,
                title=REQUEST['L_invalid_name'],
                message=REQUEST['L_give_valid_name'],
                action=action)

        if creating_new_course and my_name in [x.get_name()
                                            for x in self.get_courses()]:
            self.get_lang(('common','coursemgmnt'),REQUEST)
            return self.message_dialog_error(
                self, REQUEST,
                title=REQUEST['L_invalid_name'],
                message=REQUEST['L_name_taken'] % my_name,
                action=action)

        if not creating_new_course \
           and my_name != self.get_child(course_id).get_name() \
           and my_name in [x.get_name() for x in self.get_courses()]:
            self.get_lang(('common','coursemgmnt'),REQUEST)
            return self.message_dialog_error(
                self, REQUEST,
                title=REQUEST['L_invalid_name'],
                message=REQUEST['L_name_taken'] % my_name,
                action=action)

        from common import convert_date # convert dates to time.time()-format

        errors = []
        self.get_lang(('common', 'coursemgmnt'), REQUEST)

        if not start_date:
            starting_date = 0
        else:
            try:
                time_tuple = strptime.strptime(start_date,
                                               REQUEST['L_short_date_format'])
                starting_date = convert_date(str(time_tuple[2]), # day
                                             str(time_tuple[1]), # month
                                             str(time_tuple[0])) # year
            except: errors.append(REQUEST['L_starting_date'])

        if not end_date:
            ending_date = 0
        else:
            try:
                time_tuple = strptime.strptime(end_date,
                                               REQUEST['L_short_date_format'])
                ending_date = convert_date(str(time_tuple[2]), # day
                                           str(time_tuple[1]), # month
                                           str(time_tuple[0])) # year
            except: errors.append(REQUEST['L_ending_date'])

        organisation = organisation.strip()
        if organisation and not is_valid_title(organisation):
            errors.append(REQUEST['L_organization'])

        # desc and methods are not checked because render_description() and
        # render_methods() methods in Course filter out unwanted HTML tags.

        if len(errors) > 0:
            return self.message_dialog_error(
                self, REQUEST,
                title=REQUEST['L_invalid_input'],
                message=REQUEST['L_invalid_fields'] + ": '" + \
                "' , '".join(errors) + "'",
                action=action)

        # edit an existing course
        if creating_new_course:
            teacher = str(REQUEST.AUTHENTICATED_USER)
            # This will raise an exception if the teacher does not exist.
            self.fle_root().fle_users.get_user_info(teacher)
            # Create new course, then proceed with updating it with
            # supplied data
            course_id = self.add_course_impl(teacher)

        course_obj = self.get_child(course_id)
        course_obj.update(
            my_name,
            desc,
            organisation,
            methods,
            starting_date,
            ending_date,
            )

        if creating_new_course:
            if do_groupfolder:
                course_obj.add_folder('CourseFolder')
            if do_announcements:
                course_obj.add_announcements()
        else:
            if do_groupfolder and not course_obj.has_group_folder():
                course_obj.add_folder('CourseFolder')
            if do_announcements and not course_obj.has_announcements():
                course_obj.add_announcements()
            # elif not do_groupfolder and course_obj.has_group_folder():
            #    course_obj._delObject('gf')

            
        return REQUEST.RESPONSE.redirect(
            self.state_href(REQUEST,
                            'course_info?course_id=%s' % course_id))

    security.declareProtected(perm_view, 'get_unames_on_my_courses')
    def get_unames_on_my_courses(self, REQUEST):
        """Return a list of unames (users that are on some course
        than the caller."""
        uname = str(REQUEST.AUTHENTICATED_USER)

        uname_list = []
        for course in self.get_courses():
            unames_in_course = course.get_all_users_id()
            if uname in unames_in_course:
                uname_list += unames_in_course

        retval = []
        for uname in uname_list:
            if uname not in retval:
                retval.append(uname)

        return retval

    security.declareProtected(perm_edit, 'get_courses')
    # No additional comments.
    def get_courses(self, REQUEST=None):
        """Return a list of Course objects in this manager."""
        return self.get_children('Course')

    security.declareProtected(perm_edit, 'get_user_ids_on_course')
    def get_user_ids_on_course(self, course_id):
        """Return UserInfo ids (list) on a given course."""
        return self.get_child(course_id).get_all_users_id()

    security.declareProtected(perm_edit, 'get_users_not_on_the_course')
    # No additional comments
    def get_users_not_on_the_course(self, course_id):
        """Get all users who are not on the given course.
        Return list of UserInfo objects."""
        try:
            course_obj = self.get_child(course_id)
        except AttributeError:
            raise 'FLE Error', 'Errorneous course id.'

        attendees = course_obj.get_all_users()
        all_users = self.fle_users.get_active_users()

        non_att = []

        for user in all_users:
            if user not in attendees:
                non_att.append(user)

        return non_att

    # FIXME: input_checks
    security.declareProtected(perm_edit, 'add_users_form_handler')
    # handler for form add_course_form_2_2.dtml
    def add_users_form_handler(
        self, course_id,
        REQUEST,
        groups_None='',     # checkboxes
        users_None='',
        users_Teacher='',
        users_Tutor='',
        users_Student='',
        None_to_Teacher='', # submit buttons
        Teacher_to_None='',
        None_to_Tutor='',
        Tutor_to_None='',
        None_to_Student='',
        Student_to_None='',
        Tutor_to_Teacher='',
        Teacher_to_Tutor='',
        Student_to_Tutor='',
        Tutor_to_Student='',
        ):
        """Adding and removing users from a given course."""
        import types

        course = self.get_child(course_id)
        orphans = self.fle_users.get_users_outside_any_group()

        if groups_None:
            if type(groups_None) is types.StringType:
                groups_None = (groups_None,)

            for user in self.fle_users.get_users():
                for g_id in groups_None:
                    if (g_id == 'g0' and user in orphans) or \
                       (g_id != 'g0' and user.belongs_to_group(g_id)):
                        try:
                            users_None.append(user.get_uname())
                        except:
                            users_None = [user.get_uname()]

        for x in ('None_to_Teacher', # left/right
                  'Teacher_to_None',
                  'None_to_Tutor',
                  'Tutor_to_None',
                  'None_to_Student',
                  'Student_to_None',
                  'Tutor_to_Teacher', # up/down
                  'Teacher_to_Tutor',
                  'Student_to_Tutor',
                  'Tutor_to_Student'):
            if eval(x):
                m = re.match("^(.*)_to_(.*)", x)
                old_role = m.group(1)
                new_role = m.group(2)

                users = "users_%s" % old_role
                if eval(users):

                    owners = [u[0] for u in self.get_local_roles()]

                    if type(eval(users)) is types.StringType:
                        exec '%s = [%s,]' % (users, users)

                    if new_role == 'None':
                        for user in eval(users):
                            course.remove_person(user)
                            if course.has_group_folder():
                                course.remove_folder_link(
                                    (self.fle_users.get_user_info(user),))
                    else:
                        for user in eval(users):
                            if user in owners:
                                new_roles = (new_role, 'Owner')
                            else:
                                new_roles = (new_role,)
                            course.set_roles(user, new_roles)
                            if old_role=='None' and course.has_group_folder():
                                course.make_group_folder_proxies(
                                    (self.fle_users.get_user_info(user),))
                else:
                    self.get_lang(('common','coursemgmnt'),REQUEST)
                    return self.message_dialog_error(
                        self, REQUEST,
                        title=REQUEST['L_select_some_users'],
                        message=REQUEST['L_select_some_users'],
                        action='add_course_form_2_2?course_id=' + course_id)

                REQUEST.RESPONSE.redirect(self.state_href(
                    REQUEST,
                    'add_course_form_2_2?course_id=' + course_id))
                return

        # Should be never reached.
        return REQUEST

    security.declareProtected(perm_manage, 'courses_form_handler')
    # index_html form handler
    def courses_form_handler(
        self,
        REQUEST,
        delete='', # form submit button
        course_export='',
        course_ids=None,
        ):
        """Form handler for courses index page."""
        import types

        if not course_ids:
            self.get_lang(('common','coursemgmnt'),REQUEST)
            return self.message_dialog_error(
                self, REQUEST,
                title=REQUEST['L_no_course_selected'],
                message=REQUEST['L_select_course_first'],
                action='index_html')

        if delete:
            self.get_lang(('common', 'coursemgmnt'),REQUEST)
            if type(course_ids) == types.StringType: course_ids = (course_ids,)
            return self.message_dialog2(
                self, REQUEST,
                title = REQUEST['L_confirmation'],
                message = REQUEST['L_are_you_sure'] + '<br>' + \
                '<br>'.join([getattr(self, ci).get_name() for ci in course_ids]),
                handler = 'delete_courses_form_handler',
                extra_value_name = 'course_ids',
                extra_values = course_ids,
                option1_value = REQUEST['L_cancel'],
                option1_name = 'cancel',
                option2_value = REQUEST['L_ok'],
                option2_name = 'delete'
                )

            REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))
        elif course_export:
            params=''
            if type(course_ids) == types.StringType: course_ids = (course_ids,)
            for c_id in course_ids:
                params+='&course_ids=%s' % c_id
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'download/fle_courses.zip')+"&src="+self.get_url_to_object(self)+"do_courses_export"+params)
        else:
            # This code should never be reached.
            raise 'FLE Error', 'Unknown button'

    security.declareProtected(perm_manage, 'do_courses_export')
    # index_html form handler
    def do_courses_export(self,REQUEST):
        import types
        from ImportExport import Exporter
        course_ids = REQUEST.get('course_ids')
        ex = Exporter("Courses")
        if type(course_ids) == types.StringType: course_ids = (course_ids,)

        for c_id in course_ids:
            course = self.get_child(c_id)
            ex.exportData(course.get_all_users(),ex.exportUserList)
            ex.exportData(course,ex.exportCourse)
        import tempfile, os
        filename = tempfile.mktemp()
        ex.createZip(filename)
        file = open(filename,"rb")
        export_data=file.read()
        file.close()
        os.remove(filename)
        REQUEST.RESPONSE.setHeader('content-type','application/zip')
        return export_data

    security.declareProtected(perm_manage, 'courses_text_export')
    def courses_text_export(self,REQUEST):
        """Exports all specified courses in text format."""
        import types
        course_ids = REQUEST.get('course_ids')
        if not course_ids:
            course_ids = self.objectIds("Course")
        if type(course_ids) == types.StringType: course_ids = (course_ids,)

        import tempfile, os, zipfile
        filename = tempfile.mktemp()
        zip = zipfile.ZipFile(filename,"w",zipfile.ZIP_DEFLATED)
        for c_id in course_ids:
            course = self.get_child(c_id)
            data = course.text_export(REQUEST)
            zip.writestr(zipfile.ZipInfo(c_id+".txt"),data)
        zip.close()
        file = open(filename,"rb")
        export_data=file.read()
        file.close()
        os.remove(filename)
        REQUEST.RESPONSE.setHeader('content-type','application/zip')
        return export_data

    # FIXME: input_checks
    security.declareProtected(perm_manage, 'delete_courses_form_handler')
    def delete_courses_form_handler(
        self,
        REQUEST,
        course_ids,
        delete='',
        cancel='',
        ):
        """Form handler that is called from message_dialog2."""
        if delete:
            import types
            if type(course_ids) == types.StringType: course_ids = (course_ids,)
            for course_id in course_ids:
                for wt in [user.get_webtop() for user in
                           self.get_child(course_id).get_all_users()]:
                    wt.recursive_delete_group_folder_proxy(course_id)

                self._delObject(course_id)
        elif cancel:
            pass
        else:
            # This code should never be reached.
            raise 'FLE Error', 'Unknown button'

        REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))



    # FIXME: input_checks
    security.declareProtected(perm_view,'change_course_form_handler')
    # FIXME: I don't really have any clue where this should be, so I just
    # FIXME: put it in the path downstream from note contextes.
    def change_course_form_handler(
        self,
        course_id,
        REQUEST):
        """Change course."""

        # Jamming?
        m = re.match("^(.*?/courses/).*?/jamming", REQUEST.URL0)
        if m:
            url = m.group(1) + course_id + '/jamming/'

        else: # No, must be knowledge building
            url = re.match("^(.*?/courses/)", REQUEST.URL0).group(1) + \
                  course_id

        # Save selected course to state so can return that
        # course when user clicks kb or jamming tab.
        REQUEST.RESPONSE.redirect(self.state_href_set_string(
            REQUEST, url, 'course_id', course_id))
        return

    security.declareProtected(perm_view,'redirect_to_kb_on_some_course')
    # Called when user clicks 'Knowledge Building' tab in the UI.
    def redirect_to_kb_on_some_course(self, REQUEST):
        """Redirect to Knowledge Building."""
        course_id = self.return_course_id_for_user(REQUEST)
        if not course_id:
            uname = str(REQUEST.AUTHENTICATED_USER)
            if uname:
                return REQUEST.RESPONSE.redirect(self.state_href(
                    REQUEST, '../fle_users/'+uname+'/webtop/'))
##            return self.message_dialog(
##                self, REQUEST,
##                title=REQUEST['L_error'],
##                message=REQUEST['L_password_mismatch'],
##                action='redirect_to_kb_on_some_course')
            raise 'FLE Error', 'How could this ever happen?'

        self.change_course_form_handler(course_id, REQUEST)

    security.declareProtected(perm_view, 'redirect_to_jm_on_some_course')
    def redirect_to_jm_on_some_course(self, REQUEST):
        """Redirect to Knowledge Building."""
        course_id = self.return_course_id_for_user(REQUEST)
        url = re.match("^(.*?/courses/)", REQUEST.URL0).group(1) + \
              course_id + '/jamming'
        REQUEST.RESPONSE.redirect(self.state_href_set_string(
            REQUEST, url, 'course_id', course_id))


    def return_course_id_for_user(self,REQUEST):
        uname = str(REQUEST.AUTHENTICATED_USER)
        if not self.fle_root().fle_users.is_valid_uname(uname):
            return None

        course_id = self.state_get_string(REQUEST, 'course_id')
        if course_id:
            try: # Make sure that the course is not deleted.
                self.get_child(course_id)
                return course_id
            except AttributeError:
                pass # Course deleted -> fall through.

        # Pick any course where the user is a participant.
        for c in self.get_courses():
            if uname in self.get_user_ids_on_course(c.get_id()):
                return c.get_id()

        return None


    security.declarePublic('has_courses')
    def has_courses(self):
        """Return boolean describing whether there is an existing course on
        the system."""
        return not not self.get_children('Course')

    security.declarePublic('get_announcements')
    def get_announcements(self):
        """Return list of courses that have announcements."""
        courses=[]
        for c in self.get_courses():
            if c.has_announcements():
                courses.append(c)
        return courses

    def get_course_id_from_req(self, req):
        """Extract a course id from REQUEST. This is needed by
        the CourseManager.course_selection dtml method."""
        path = req.PATH_TRANSLATED
        i = string.find(path, "courses")
        ri = string.rfind(path, "courses")
        if (i == -1) or (ri == -1):
            return None
        if (ri != i):
            # There is more than one 'courses' word in path.
            # We'll have to use the reverse one.
            i = ri
        plst = filter(lambda x:x, string.split(path[i:], '/'))
        try:
            return plst[1]
        except IndexError:
            return None

    def get_formatted_current_date(self, REQUEST):
        """Return date formatted depending on user's language."""
        self.get_lang(('common',), REQUEST)
        return time.strftime(REQUEST['L_short_date_format'], time.localtime())

    def import_form_handler(
        self,
        REQUEST,
        file,
        course_import='',
        cancel='',
        ):
        """Form handler for course importing."""
        if course_import:
            from ImportExport import Exporter
            import tempfile, os
            filename = tempfile.mktemp()
            f = open(filename,"w+b")
            f.write(file.read())
            f.close()
            import_data=None
            exported = Exporter("Courses",filename)
            os.remove(filename)

            uelem = exported.root.getElementsByTagName("Users")[0]
            exported.importUsers(uelem,self.parent())

            for celem in exported.root.getElementsByTagName("Course"):
                course = exported.importCourse(celem,self)
                if REQUEST:
                    self.get_lang(('common','coursemgmnt'),REQUEST)
                    course.set_name(course.get_name()+" %s" % REQUEST['L_course_imported'])

            exported.importUsersWebtops(uelem,self.parent())

            self.get_lang(('common','kb','coursemgmnt'),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_importing'],
                message=REQUEST['L_courses_imported'],
                action='index_html')
        REQUEST.RESPONSE.redirect('index_html')



Globals.InitializeClass(CourseManager)

# EOF
