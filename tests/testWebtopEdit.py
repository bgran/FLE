# $Id: testWebtopEdit.py,v 1.13 2003/06/13 07:57:13 jmp Exp $

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

class testWebtopEdit(unittest.TestCase):
    def setUp(self):
        withUsers()
        self.wt = fle.fle_users.user1.get_webtop()
        self._name='useme'
        self._body='Useless dribble\nwith line  breaks\n\n   and extra whitespace.'
        self._body_rendered='<p>Useless dribble<br />with line  breaks</p><p>&nbsp;&nbsp;&nbsp;and extra whitespace.</p>'
        self._name2='usemetoo'
        self._body2='More useless dribble  \n\n\n  with line  breaks\n   and extra whitespace.'
        self.wt.add_folder_handler(FakeRequest(),'testf',submit='ok')
        self.f=self.wt.objectValues('WebtopFolder')[0]

    def tearDown(self):
        self.wt._delObject(self.wt.objectIds('WebtopFolder')[0])

    def testMemoCreation(self):
        assert len(self.f.objectItems('WebtopMemo'))==0, \
               "Folder contains initial memo!"

        self.f.add_memo_handler(FakeRequest(),self._name,self._body, submit='ok')

        assert len(self.f.objectItems('WebtopMemo'))==1, \
               "Memo creation failed or meta_type is invalid."

        memo = self.f.objectValues('WebtopMemo')[0]

        assert memo.get_name()==self._name, \
               "Memo name is invalid."

        assert memo.get_body()==self._body, \
               "Memo body is broken."

    def testMemoEditing(self):
        self.f.add_memo_handler(FakeRequest(),self._name,self._body, submit='ok')
        memo = self.f.objectValues('WebtopMemo')[0]

        memo.add_memo_handler(FakeRequest(), self._body2, submit='ok')

        assert memo.get_body()==self._body2, \
               "Memo editing failed to save contents correctly."

    def testRenderContents(self):
        self.f.add_memo_handler(FakeRequest(),self._name,self._body, submit='ok')
        memo = self.f.objectValues('WebtopMemo')[0]

        assert memo.render_contents()==self._body_rendered, \
               "Memo rendering does not produce break tags and no-break spaces:\n"+\
               memo.render_contents()

def suite():
    return unittest.makeSuite(testWebtopEdit)

