# $Id: testCourseManager.py,v 1.6 2003/06/13 07:57:13 jmp Exp $

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

class testCourseManager(unittest.TestCase):
    def setUp(self):
        withNotes()

    def tearDown(self):
        pass

    def testCourseCreation(self):
        courses = fle.courses.objectItems('Course')
        assert len(courses)==2, \
               "Course amount invalid after initial course creation."
        assert courses[0][1].get_name()=='Test Course', \
               "Course name stored incorrectly."
        assert courses[1][1].get_name()=='Test Course 2', \
               "Course name stored incorrectly."

    def testCourseTeachers(self):
        courses = fle.courses.objectItems('Course')
        assert courses[0][1].get_all_users()[0].get_uname()=='user1', \
               "Initial teacher invalid."
        assert courses[1][1].get_all_users()[0].get_uname()=='user2', \
               "Initial teacher invalid."

def suite():
    return unittest.makeSuite(testCourseManager)
