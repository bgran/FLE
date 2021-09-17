# $Id: testWebtopTrash.py,v 1.10 2003/06/13 07:57:13 jmp Exp $

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

class testWebtopTrash(unittest.TestCase):
    def setUp(self):
        withUsers()
        self.wt = fle.fle_users.user1.get_webtop()
        self._name='useme'
        self._url='http://w3.org/'
        self._name2='usemetoo'
        self._url2='http://evvk.org/'
        self.wt.add_folder_handler(FakeRequest(),'testf',submit='ok')
        self.f=self.wt.objectValues('WebtopFolder')[0]
        self.f.add_link_handler(FakeRequest(),self._name,self._url,submit='ok')
        self.f.add_link_handler(FakeRequest(),self._name2,self._url2,submit='ok')
        items = self.f.objectItems('WebtopLink')
        self.item1=items[0]
        self.item2=items[1]

    def tearDown(self):
        self.wt._delObject(self.wt.objectIds('WebtopFolder')[0])

    def testListing(self):
        assert len(self.wt.trash.list_contents())==0, \
               "Trash is not initially empty!"

        self.f.remove((self.item1[1],))
        assert len(self.wt.trash.list_contents())==1, \
               "Trash list does not see deleted items, it is: "+\
               str(self.wt.trash.list_contents())

    def testSingleRestore(self):
        self.f.remove(
            (self.item1[1],
             self.item2[1],)
            )
        assert len(self.wt.trash.list_contents())==2, \
               "Trash list does not see deleted items."

        self.wt.trash.form_handler(
            str(self.item1[0]),
            restore='restore')

        assert len(self.wt.trash.list_contents())==1 and \
               len(self.f.objectItems('WebtopLink'))==1, \
               "Individual recovery via form does not work."

    def testMultiRestore(self):
        self.f.remove(
            (self.item1[1],
             self.item2[1],)
            )

        self.wt.trash.form_handler(
            (self.item1[0],self.item2[0],),
            restore='restore')

        assert len(self.wt.trash.list_contents())==0 and \
               len(self.f.objectItems('WebtopLink'))==2, \
               "Multi-recovery via form does not work."

    def testEmptyTrash(self):
        self.f.remove(
            (self.item1[1],
             self.item2[1],)
            )

        self.wt.trash.form_handler(
            REQUEST=FakeRequest(),
            empty_trash='do it! empty the whole trashcan!')

        assert len(self.wt.trash.list_contents())==0 and \
               len(self.f.objectItems('WebtopLink'))==0, \
               "'Empty trash' not work."

    # We don't have functionality to remove specific items from
    # the trash anymore.

##    def testSingleRemove(self):
##        self.f.remove(
##            (self.item1[1],
##             self.item2[1],)
##            )

##        self.wt.trash.form_handler(
##            str(self.item1[0]),
##            remove='ok')

##        assert len(self.wt.trash.list_contents())==1 and \
##               len(self.f.objectItems('WebtopLink'))==0, \
##               "Removal of file from trash does not work."

##    def testMultipleRemove(self):
##        self.f.remove(
##            (self.item1[1],
##             self.item2[1],)
##            )

##        self.wt.trash.form_handler(
##            (self.item1[0],self.item2[0],),
##            remove='ok')

##        assert len(self.wt.trash.list_contents())==0 and \
##               len(self.f.objectItems('WebtopLink'))==0, \
##               "Removal of files from trash does not work."

def suite():
    return unittest.makeSuite(testWebtopTrash)

