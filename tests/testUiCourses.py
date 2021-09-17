# $Id: testUiCourses.py,v 1.16 2003/06/13 07:57:13 jmp Exp $

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
import re
from Errors import *

class testUiCourses(unittest.TestCase):
    def setUp(self):
        withNotes()
        commit()

    def tearDown(self):
        pass


    def testCourseManagement(self):
        _url='/testfle/courses/'
        res = wwwtest(_url,user='fleadmin:ni')

        assert re.search('Test Course</a>',res) and \
               re.search('Test Course 2</a>',res), \
               "Both courses not found on courses page."

    def testCourseManagementAccess(self):
        _url='/testfle/courses/'
        # Check that default user (user1) does not have access to
        # course management.
        wwwtest(_url,expected=401)

    def testCourseParticipants(self):
        _url='/testfle/courses/1/'
        res = wwwtest(_url)

        assert re.search('user1',res) and \
               not re.search('user2',res), \
               "Course participants are not displayed."

    def testCourseViewAccess(self):
        _url='/testfle/courses/1/'
        # Check that only course participants are allowed here.
        wwwtest(_url,user='user2:passwd2',expected=401)
        wwwtest(_url,user='unknown:foo',expected=401)

    def testSecondCourseParticipants(self):
        _url='/testfle/courses/2/'
        res = wwwtest(_url,user='user2:passwd2')

        assert re.search('user2',res) and \
               re.search('user3',res) and \
               not re.search('user1',res), \
               "Course participants are not displayed."

    def testSecondCourseViewAccess(self):
        _url='/testfle/courses/2/'
        # Check that only course participants are allowed here.
        wwwtest(_url,expected=401)

    def testCourseViewContexts(self):
        _url='/testfle/courses/2/'
        res = wwwtest(_url,user='user2:passwd2')

        assert re.search('Context1',res) and \
               re.search('Context2',res), \
               "Course contexts are not displayed."

        assert re.search('Discussion 1',res) and \
               re.search('Discussion 2',res), \
               "Discussions not displayed in course view."

    def testCourseContextView(self):
        _url='/testfle/courses/2/4/'
        res = wwwtest(_url,user='user2:passwd2')

        assert re.search('Context2',res) and \
               re.search('Discussion 1',res) and \
               re.search('Discussion 2',res), \
               "Context view does not show discussions or context name."

    def testCourseInfo(self):
        _url='/testfle/courses/2/course_info'
        res = wwwtest(_url,user='user2:passwd2')

        assert re.search('Test Course 2',res) and \
               re.search('UnitTesting',res) and \
               re.search('MediaLab',res) and \
               re.search('user2',res) and \
               re.search('user3',res), \
               "Course info page invalid."

    def testCourseContextInfoEdit(self):
        _url='/testfle/courses/2/4/edit_course_context_form'
        res = wwwtest(_url,user='user2:passwd2')

        assert re.search('Context2',res) and \
               re.search('Description 2\nof several\nlines',res) and \
               re.search('Progressive Inquiry',res), \
               "Course context info edit page invalid."

    def testCourseEdit(self):
        _url='/testfle/courses/add_course_form_1_2?course_id=2'
        res = wwwtest(_url,user='fleadmin:ni')
        assert re.search('Test Course 2',res), \
               "Course edit page not ok."

        _url='/testfle/courses/add_course_form_handler?course_id=2&my_name=Test+Course+2&organisation=MediaLab&desc=Course+2+for+FLE+testing+now+edited&methods=UnitTesting&start_date=2002-1-23&end_date=2008-11-30&add=Submit'
        res = wwwtest(_url,user='fleadmin:ni',expected=302)

        _url='/testfle/courses/add_course_form_1_2?course_id=2'
        res = wwwtest(_url,user='fleadmin:ni')
        assert re.search('Test Course 2',res) and \
               re.search('Course 2 for FLE testing now edited',res), \
               "Course edit failed."

    def testCourseContextEditAccess(self):
        _url='/testfle/courses/2/4/'
        res = wwwtest(_url,user='user2:passwd2')
        assert re.search('edit_course_context_form',res), \
               "Context edit link not shown to teacher."

        res = wwwtest(_url,user='user4:passwd4')
        assert not re.search('edit_course_context_form',res), \
               "Context edit link shown to student."

        res = wwwtest(_url,user='user3:passwd3')
        assert re.search('edit_course_context_form',res), \
               "Context edit link not shown to tutor."

    def testCourseContextCreateAccess(self):
        _url='/testfle/courses/2/'
        res = wwwtest(_url,user='user2:passwd2')

        assert re.search('Luo kurssiosuus',res), \
               "Context create link not shown to teacher."

        _url='/testfle/courses/2/'
        res = wwwtest(_url,user='user3:passwd3')

        assert not re.search('Luo uusi kurssiosuus',res), \
               "Context create link shown to student."


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(testUiCourses))
    return s
