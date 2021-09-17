# $Id: testImportExport.py,v 1.32 2003/06/13 07:57:13 jmp Exp $

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

from tests import *
import unittest
from Errors import *
import ImportExport
import ImportExportEML

class testImportExport(unittest.TestCase):
    def setUp(self):
        withJamming()
        withTTSs()
        commit()

    def tearDown(self):
        pass

    def testEMLExport(self):
        res=fle.courses.get_child('2').eml_export()

    def testExport(self):
        from ZODB.POSException import ConflictError
        try:
            fle.courses.objectValues('Course')[0].get_name()
        except ConflictError:
            commit()

        exported = ImportExport.Exporter("FLE")
        exported.exportData(fle.typesets,exported.exportGlobalTypes)
        exported.exportData(fle.courses,exported.exportKB)
        exported.exportData(fle.courses, exported.exportJamming)
        exported.exportData(fle.fle_users,exported.exportUsers)
        exported.createZip("export.zip")

        #print ""
        #print "EXPORT DATA: " + str(exported.binarydata.get_counter()) + " binary data packages stored, XML document has size "+str(len(exported.dom.toxml()))
        #print "export.zip created."

    def testExportedDataImport(self):
        file = open("export.zip","rb")
        zipdata = file.read()
        file.close()

        from FLE import manage_addFLE

        ###
        # This kludge is used to make sure the imported FLE installation
        # is owned by nobody. Otherwise the owner will be the user
        # that was last used in an authenticated http request.
        # NOTE: This may have to be re-entered into FLE.py somewhere.
        from AccessControl.SecurityManagement import newSecurityManager
        import AccessControl.SpecialUsers
        newSecurityManager(None,AccessControl.SpecialUsers.nobody)
        ###
        import time
        s_time=time.time()
        app.manage_addProduct['FLE'].manage_addFLE('imported','Imported','impadmin','ni','ni','Imp','Admin','create','smtp.imp.org','25',FakeUpload("export.zip",zipdata,'application/zip'))
        e_time=time.time()
        print "[import time: %s]" % str(e_time-s_time)

        # Test the installation
        imp = app.imported

        l1 = fle.typesets.objectIds()
        l2 = imp.typesets.objectIds()
        l1.sort()
        l2.sort()
        assert l1 == l2, \
               "ThinkingTypeSetManager contents don't match after import."

        l1 = fle.typesets.tmp_objects.objectValues()[0]
        l2 = imp.typesets.tmp_objects.objectValues()[0]
        assert l1.get_name() == l2.get_name(), \
               "Unfinished TTS not imported correctly."

        l1 = [x.get_id() for x in fle.typesets.pitt.get_thinking_types()]
        l2 = [x.get_id() for x in imp.typesets.pitt.get_thinking_types()]
        assert l1 == l2, \
               "ThinkingTypeSet contents (types and order) don't match after import."

        assert fle.typesets.pitt.summary.get_icon().data == \
               app.imported.typesets.pitt.summary.get_icon().data, \
               "ThinkingType icons not imported correctly."

        assert fle.typesets.pitt.get_description() == \
               app.imported.typesets.pitt.get_description(), \
               "ThinkingType set descriptions not imported correctly."

        assert [x.get_id() for x in fle.typesets.pitt.get_possible_follow_ups(fle.typesets.pitt.problem)] == \
               [x.get_id() for x in imp.typesets.pitt.get_possible_follow_ups(imp.typesets.pitt.problem)], \
               "ThinkingType follow-up rules not imported correctly."

        assert len(fle.typesets.pitt.problem.get_description()) == \
               len(imp.typesets.pitt.problem.get_description()), \
               "ThinkingType descriptions not imported correctly."


        l1 = fle.courses.objectIds()
        l2 = imp.courses.objectIds()
        l1.sort()
        l2.sort()
        assert l1 == l2, \
               "CourseManager contents don't match after import."

        c1 = fle.courses.get_courses()[0]
        c2 = imp.courses.get_courses()[0]

        assert c1.get_description() == \
               c2.get_description(), \
               "Course descriptions not imported correctly."

        assert c1.get_methods() == \
               c2.get_methods(), \
               "Course methods not imported correctly."

        c1 = fle.courses.get_courses()[1]
        c2 = imp.courses.get_courses()[1]

        assert c1.get_course_context_names().sort() == \
               c2.get_course_context_names().sort(), \
               "Course's contexts not imported correctly."

        cx1 = c1.get_course_contexts()[1]
        cx2 = c2.get_course_contexts()[1]

        assert cx1.get_description() == \
               cx2.get_description(), \
               "Context descriptions not imported correctly."

        assert cx1.get_long_description() == \
               cx2.get_long_description(), \
               "Context descriptions not imported correctly."

        assert cx1.get_n_notes() == \
               cx2.get_n_notes(), \
               "Course's contexts not imported correctly."

        n1 = cx1.objectValues('Note')[0]
        n2 = cx2.objectValues('Note')[0]

        assert n1.get_real_subject() == n2.get_real_subject(), \
               "Note subject doesn't match after import."

        assert n1.get_body() == n2.get_body(), \
               "Note body doesn't match after import."

        assert round(n1.get_creation_time()) == \
               round(n2.get_creation_time()), \
               "Note timestamp doesn't match after import."

        read1 = n1.get_readers_with_all_dates()
        read2 = n2.get_readers_with_all_dates()
        for (uname,dates) in read1.items():
            assert uname in read2.keys(), \
                   "Note reader "+uname+" is missing from import!\n"+repr(read1)+" versus "+repr(read2)
            dates2 = read2[uname]
            assert dates['count'] == dates2['count'], \
                   "Number of read times for "+uname+" doesn't match after import."
            assert len(dates['when'])==len(dates2['when']), \
                   "Timestamps missing from imported note read list."
            for w in dates['when']:
                assert round(w) in [round(x) for x in dates2['when']], \
                       "Timestamp mismatch in imported not read list."

        n1 = n1.objectValues('Note')[0]
        n2 = n2.objectValues('Note')[0]
        assert n1.get_image_data() == n2.get_image_data(), \
               "Note image data not imported correctly."
        assert n1.get_image_name() == n2.get_image_name(), \
               "Note image names not imported correctly."


        u1 = fle.fle_users.get_user_info('user2')
        u2 = imp.fle_users.get_user_info('user2')

        assert u1.get_uname() == u2.get_uname() and \
               u1.get_quote() == \
               u2.get_quote() and \
               u1.get_personal_interests() == \
               u2.get_personal_interests() and \
               u1.get_professional_interests() == \
               u2.get_professional_interests() and \
               u1.get_photo() == \
               u2.get_photo() and \
               u1.get_last_name() == \
               u2.get_last_name(), \
               "User information not imported correctly."

        u1 = fle.acl_users.getUser('user2')
        u2 = imp.acl_users.getUser('user2')

        assert u1.getRolesInContext(fle.courses.get_child('2')) == \
               u2.getRolesInContext(imp.courses.get_child('2')), \
               "Users' course specific roles not imported correctly."

        u1 = fle.fle_users.get_user_info('user5')
        u2 = imp.fle_users.get_user_info('user5')

        assert u1.is_frozen() and u2.is_frozen(), \
               "User freeze status not imported correctly."

        for x in u1.getRolesInObject(fle.courses.get_child('2')):
            assert x in u2.getRolesInObject(imp.courses.get_child('2')), \
               "Frozen user's course specific roles not imported correctly."


        w1 = fle.fle_users.user3.webtop
        w2 = imp.fle_users.user3.webtop
        # wt1: folder
        # wt1.wt2: file
        # wt1.wt3: link
        wf1=w1.wt1
        wf2=w2.wt2
        try:
            wf2.wt3
            wf2.wt4
        except:
            self.fail("Webtop contents not imported correctly.")

        assert wf1.wt2.getContentType() == \
               wf2.wt3.getContentType(), \
               "Webtop file content type not imported correctly."
        assert wf1.wt2.data == \
               wf2.wt3.data, \
               "Webtop file contents not imported correctly."
        assert wf1.wt3.get_url() in \
               [x.get_url() for x in wf2.objectValues('WebtopLink')], \
               "External webtop link not imported correctly."
        assert wf1.wt4.get_body() in \
               [x.get_body() for x in wf2.objectValues('WebtopMemo')], \
               "WebtopMemo contents not imported correctly."
        int_links = []
        for item in wf2.objectValues('WebtopLink'):
            if item.is_internal_link():
                int_links.append(item)
        assert wf1.wt5.get_obj_ref().get_real_subject() in  \
               [x.get_obj_ref().get_real_subject() for x in int_links] and \
               wf1.wt6.get_obj_ref().get_real_subject() in \
               [x.get_obj_ref().get_real_subject() for x in int_links], \
               "Internal webtop links do not hold on to correct objects."

        assert fle.fle_users.user3.get_webtop_bg_name() == \
               imp.fle_users.user3.get_webtop_bg_name(), \
               "Custom Webtop background not imported correctly."
        assert fle.fle_users.user3.get_webtop_bg_image_path() == \
               imp.fle_users.user3.get_webtop_bg_image_path(), \
               "Custom Webtop background not imported correctly."
        assert fle.fle_users.user3.get_webtop_bg_colour_name() == \
               imp.fle_users.user3.get_webtop_bg_colour_name(), \
               "Custom Webtop background not imported correctly."

        assert fle.fle_users.user2.get_webtop_bg_name() == \
               imp.fle_users.user2.get_webtop_bg_name(), \
               "Pre-defined Webtop background not imported correctly."
        assert fle.fle_users.user2.get_webtop_bg_image_path() == \
               imp.fle_users.user2.get_webtop_bg_image_path(), \
               "Pre-defined Webtop background not imported correctly."
        assert fle.fle_users.user2.get_webtop_bg_colour_name() == \
               imp.fle_users.user2.get_webtop_bg_colour_name(), \
               "Pre-defined Webtop background not imported correctly."


        c1 = fle.courses.get_courses()[1]
        c2 = imp.courses.get_courses()[1]

        jam_session_names_1 = [x.get_name() for x in
                               c1.jamming.objectValues('JamSession')]
        jam_session_names_1.sort()

        jam_session_names_2 = [x.get_name() for x in
                               c1.jamming.objectValues('JamSession')]
        jam_session_names_2.sort()

        assert jam_session_names_1 == jam_session_names_2, \
               "JamSessions not imported correctly."

        js1 = c1.jamming.objectValues('JamSession')[0]
        js2 = c2.jamming.objectValues('JamSession')[0]

        assert js1.get_name() == js2.get_name() and \
               js1.get_type() == js2.get_type() and \
               js1.get_description() == js2.get_description() and \
               js1.get_n_artefacts() == js2.get_n_artefacts() and \
               js1.get_n_unread_artefacts(u1.get_uname()) == \
               js2.get_n_unread_artefacts(u1.get_uname()), \
               "JamSessions not imported correctly."

        jam_artefacts_1 = js1.objectValues('JamArtefact')
        jam_artefacts_2 = js2.objectValues('JamArtefact')

        assert len(jam_artefacts_1) == len(jam_artefacts_2), \
               "Too few or too many JamArtefacts imported."

        for i in range(0, len(jam_artefacts_1)):
            ja1 = jam_artefacts_1[i]
            ja2 = jam_artefacts_2[i]

            assert len(ja1.get_children_artefacts()) == \
                   len(ja2.get_children_artefacts()), "1"

            assert len(ja1.get_children_artefacts()) == \
                   len(ja2.get_children_artefacts()) and \
                   ja1.get_name() == ja2.get_name() and \
                   ja1.get_data() == ja2.get_data() and \
                   ja1.get_content_type() == ja2.get_content_type() and \
                   ja1.get_author() == ja2.get_author() and \
                   ja1.get_annotations(FakeRequest()) == \
                   ja2.get_annotations(FakeRequest()) and \
                   len(ja1.get_parent_ids()) == len(ja2.get_parent_ids()), \
                   "JamArtefact not imported correctly."

    def testEMLExport(self):
        from ZODB.POSException import ConflictError
        try:
            fle.courses.objectValues('Course')[0].get_name()
        except ConflictError:
            commit()

        exported = ImportExportEML.Exporter()
        exported.exportCourse(fle.courses.get_child('2'))
        exported.createZip("eml_export.zip")


def suite():
    return unittest.makeSuite(testImportExport)

