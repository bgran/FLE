# $Id: testUiWebtop.py,v 1.22 2003/06/13 07:57:13 jmp Exp $

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

class testUiWebtop(unittest.TestCase):
    def setUp(self):
        withNotes()
        commit()

    def tearDown(self):
        pass


    def testRootView(self):
        _url='/testfle/fle_users/user1/webtop/'
        res = wwwtest(_url)

        assert re.search('user1',res,re.M), \
               "User's name not found on webtop page."

        assert re.search('>Test Course<',res,re.M), \
               "User's course not found on webtop page."

    def testNonEmptyView(self):
        _url='/testfle/fle_users/user3/webtop/'
        res = wwwtest(_url)

    def testNonEmptyView2(self):
        _url='/testfle/fle_users/user3/webtop/wt1/'
        res = wwwtest(_url)

    def testViewAccess(self):
        _url='/testfle/fle_users/user1/webtop/'
        # Check that unauthorized user does not have access to
        # webtop  management.
        wwwtest(_url,user='unknown:foo',expected=401)

        # Check that other users have access to the webtop.
        try:
            wwwtest(_url,user='user2:passwd2')
        except AssertionError:
            self.fail("Users can't access other users' webtops.")


    def testNoteCount(self):
        _url='/testfle/fle_users/user4/webtop/'
        res = wwwtest(_url,user='user4:passwd4')

        from vocabulary_fi import webtop

        assert re.search(
            '<td.*?><a href.*?>' + webtop['totals_notes'][0] + \
            '</a>: (\d+) .*/',res).group(1) == \
            re.search('/ (\d+) .*</td>',res).group(1), \
            "Inactive user should have all notes as unread."

    def testNoteCount2(self):
        commit()
        _url='/testfle/fle_users/user2/webtop/'
        res = wwwtest(_url,user='user2:passwd2')

        assert re.search('<td.*>(\d+) .*/',res).group(1) < \
               re.search('/ (\d+) .*</td>',res).group(1), \
               "Active user should not have all notes as unread."

    def testLinkCreate(self):
        res = wwwtest('/testfle/fle_users/user1/webtop/add_link_handler?back_link=http://localhost:80/testfle/courses/2/4/5/index_html&my_name=Discussion+1&url=http://localhost:80/testfle/courses/2/4/5/index_html',user='user1:passwd1')

        assert re.search('Discussion 1',res), \
               "KB link creation onto webtop failed."

        # This doesn't work... the code is ok, but the change isn't
        # visible, for some reason.
##         commit()
##         assert 'Discussion 1' in [x.get_name() for x in fle.fle_users.user1.webtop.list_contents()], \
##                "KB link creation onto webtop failed."

    def testMemoCreatePage(self):
        res = wwwtest('/testfle/fle_users/user1/webtop/wt_add_memo', \
                      user='user1:passwd1')

    def testFolderCreateForm(self):
        res = wwwtest('/testfle/fle_users/user3/webtop/wt_add_folder', \
                      user='user3:passwd3')

    def testItemRenameForm(self):
        res = wwwtest( \
            "/testfle/fle_users/user3/webtop/wt_rename?item_ids=('wt1',)", \
            user='user3:passwd3')

    def testPrefForm(self):
        res = wwwtest( \
            "/testfle/fle_users/user3/webtop/wt_preferences", \
            user='user3:passwd3')

    def testInternalLinkAccess(self):
        res = wwwtest('/testfle/fle_users/user3/webtop/wt1/',
                      user='user2:passwd2')
        assert re.search("/testfle/courses/2/4/5",res) and \
               re.search("/testfle/courses/2/4/5/7/9",res), \
               "Internal links are not active for course participant."

        res = wwwtest('/testfle/fle_users/user3/webtop/wt1/',
                      user='user1:passwd1')
        assert not re.search("/testfle/courses/2/4/5",res) and \
               not re.search("/testfle/courses/2/4/5/7/9",res), \
               "Internal links are active for non-course participant."

def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(testUiWebtop))
    return s
