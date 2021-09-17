# $Id: testUiGroupFolder.py,v 1.7 2003/06/13 07:57:13 jmp Exp $

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

class testUiGroupFolder(unittest.TestCase):
    def setUp(self):
        withCourse()
        commit()

    def tearDown(self):
        pass


    def testVisibility(self):
        res = wwwtest('/testfle/courses/2/',user='user2:passwd2')
        assert re.search('gf',res), \
               "Group folder not visible in course page."

    def testContentView(self):
        try:
            res = wwwtest('/testfle/courses/2/gf/',user='user2:passwd2')
        except:
            self.fail("Group folder content view doesn't work.")
        try:
            res = wwwtest('/testfle/courses/2/gf/',user='user1:passwd1',expected=401)
        except:
            self.fail("Non-course member can view group folder.")

    def testSubCreation(self):
        try:
            _url='/testfle/courses/2/gf/add_folder_handler?my_name=subf1&submit=yes'
            wwwtest(_url,expected=302,user='user2:passwd2')
        except:
            self.fail("Teacher cannot create subfolders in group folders.")
        try:
            _url='/testfle/courses/2/gf/add_folder_handler?my_name=subf2&submit=yes'
            wwwtest(_url,expected=302,user='user3:passwd3')
        except:
            self.fail("Tutor cannot create subfolders in group folders.")
        try:
            _url='/testfle/courses/2/gf/add_folder_handler?my_name=subf3&submit=yes'
            wwwtest(_url,expected=302,user='user4:passwd4')
        except:
            self.fail("Student cannot create subfolders in group folders.")
        try:
            _url='/testfle/courses/2/gf/add_folder_handler?my_name=subf4&submit=yes'
            wwwtest(_url,expected=401,user='user1:passwd1')
        except:
            self.fail("Non-attendee can create subfolders in group folders.")


def suite():
    s = unittest.TestSuite()
    # This suite is turned off until we have a working course folder.
    #s.addTest(unittest.makeSuite(testUiGroupFolder))
    return s
