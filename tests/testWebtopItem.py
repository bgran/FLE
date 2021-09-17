# $Id: testWebtopItem.py,v 1.8 2003/06/13 07:57:13 jmp Exp $

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

class testWebtopItem(unittest.TestCase):
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
        self.item1 = items[0]
        self.item2 = items[1]

    def tearDown(self):
        self.wt._delObject(self.wt.objectIds('WebtopFolder')[0])

    def testSetIcon(self):
        img1 = fle.images.doc
        img2 = fle.images.doc_small

        item = self.item1[1]
        item.set_icon('/testfle/images/doc')
        assert item.get_icon()==img1, \
               "Item icon not stored correctly."

        item.set_icon('/testfle/images/doc_small')
        assert item.get_icon()==img2, \
               "Item icon not changed correctly."

    def testListItemName(self):
        item = self.item1[1]
        assert item.get_list_item_name()==self._name, \
               "Link list item name returns invalid value."


def suite():
    return unittest.makeSuite(testWebtopItem)

