# $Id: testCourse.py,v 1.10 2003/06/13 07:57:13 jmp Exp $

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
from common import get_roles

class testCourse(unittest.TestCase):
    def setUp(self):
        withNotes()

    def tearDown(self):
        pass

    def testStudentAddRemove(self):
        c = fle.courses.get_courses()[0]
        count = len(c.get_all_users())
        c.add_student('user2')
        assert len(c.get_all_users())==count+1, \
               "User adding failed!"

        c.add_student('user3')
        assert len(c.get_all_users())==count+2, \
               "User adding failed!"

        try:
            c.add_student('unknown1')
        except:
            pass
        else:
            self.fail("Invalid user name did not raise exception.")
        c.remove_person('user3')
        c.remove_person('user2')
        assert len(c.get_all_users())==count, \
               "User removal failed!"

        try:
            c.remove_person('unknown1')
        except:
            pass
        else:
            self.fail("Removing a nonexistent user did not raise exception.")

        try:
            c.remove_person('user2')
        except:
            pass
        else:
            self.fail("Removing a non-participating user did not raise exception.")

class testCourseRoles(unittest.TestCase):
    def setUp(self):
        c = fle.courses.get_courses()[0]
        c.add_student('user2')
        c.add_student('user3')

    def tearDown(self):
        c = fle.courses.get_courses()[0]
        c.remove_person('user2')
        c.remove_person('user3')

    def testInitialRoles(self):
        c = fle.courses.get_courses()[0]
        assert 'Teacher' in get_roles(c,'user1'), \
               "Initial teacher role invalid."
        assert 'Student' not in get_roles(c,'user1'), \
               "Initial teacher role invalid."

        assert 'Student' in get_roles(c,'user2'), \
               "Initial user role invalid."
        assert 'Teacher' not in get_roles(c,'user2'), \
               "Initial user role invalid."

    def testRoleManipulation(self):
        c = fle.courses.get_courses()[0]
        c.set_roles('user2',('Teacher','Student'))
        r = get_roles(c,'user2')
        assert ('Teacher' in r and 'Student' in r and len(r) >= 2), \
               "Role setting does not work correctly."
        assert c.has_role('user2','Teacher') and \
               c.has_role('user2','Student'), \
               "has_role does not work."
        c.set_roles('user2',('Student',))
        r = get_roles(c,'user2')
        assert ('Student' in r and len(r) >= 1), \
               "Role removal does not work correctly."

class testCourseContextCreation(unittest.TestCase):
    def setUp(self):
        withNotes()

    def testContextCreate(self):
        c = fle.courses.get_courses()[0]
        c.add_course_context('Context1','Test context','pitt','Description',
                             FakeRequest('user1'),publish='publish')
        cont = c.get_course_contexts()
        assert len(cont)==1 and cont[0].get_name()=='Context1', \
               "Context add does not work."

        id = cont[0].get_id()
        c._delObject(id)



def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(testCourse))
    s.addTest(unittest.makeSuite(testCourseRoles))
    s.addTest(unittest.makeSuite(testCourseContextCreation))
    return s
