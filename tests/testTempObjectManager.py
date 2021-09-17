# $Id: testTempObjectManager.py,v 1.6 2003/06/13 07:57:13 jmp Exp $

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

class testNewTempObjectManager(unittest.TestCase):
    def setUp(self):
        withUsers()
        #self.ctx=fle.courses.get_courses()[1].get_course_contexts()[1]
        #self.note=self.ctx.get_children('Note')[0]
        self.wt=fle.fle_users.user1.get_webtop()
        self.wt.add_folder_handler(FakeRequest(),'testf',submit='ok')
        self.f=self.wt.objectValues('WebtopFolder')[0]

    def tearDown(self):
        self.wt._delObject(self.wt.objectIds('WebtopFolder')[0])

    def testMoveToTmp(self):
        self.f.add_link_handler(FakeRequest(),'link1','http://foo',submit='ok')
        self.f.add_link_handler(FakeRequest(),'link2','http://bar',submit='ok')

        assert len(self.f.objectItems('WebtopLink'))==2, \
               "Link creation failed."

        obj = self.f.objectValues('WebtopLink')[0]
        self.f.move_to_tmp(obj)

        assert len(self.f.objectItems('WebtopLink'))==1 and \
               len(self.f.tmp_objects.objectItems('WebtopLink'))==1, \
               "Object move to temporary folder failed."

        self.f.move_from_tmp(obj)
        assert len(self.f.objectItems('WebtopLink'))==2 and \
               len(self.f.tmp_objects.objectItems('WebtopLink'))==0, \
               "Object move from temporary folder failed."



def suite():
    return unittest.makeSuite(testNewTempObjectManager)
