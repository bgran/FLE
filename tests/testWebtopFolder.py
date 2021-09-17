# $Id: testWebtopFolder.py,v 1.16 2003/06/13 07:57:13 jmp Exp $

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

class testWebtopFolderCreate(unittest.TestCase):
    def setUp(self):
        withUsers()
        self.wt = fle.fle_users.user1.get_webtop()

    def tearDown(self):
        pass

    def testCreateFolder(self):
        _foldername='folder1'
        count = len(self.wt.objectItems())
        self.wt.add_folder_handler(FakeRequest(),_foldername,submit='ok')
        assert len(self.wt.objectItems())==count+1, \
               "Folder creation failed."

        #assert len(self.wt.objectValues('WebtopFolder')[0].objectItems())==1, \
        #       "Folder not created empty."

        assert self.wt.objectValues('WebtopFolder')[0].title==_foldername, \
               "Folder meta type or title invalid after creation."

        self.wt._delObject(self.wt.objectIds('WebtopFolder')[0])
        assert len(self.wt.objectItems())==count, \
               "Folder kill failed."

    def testCreateLink(self):
        _linkname='MyLink'
        _linkurl='http://w3.org/'
        count = len(self.wt.objectItems())
        self.wt.add_link_handler(FakeRequest(),_linkname,_linkurl,submit='ok')
        assert len(self.wt.objectItems())==count+1, \
               "Link creation failed."

        for x in self.wt.objectValues('WebtopLink'):
            if _linkname==x.title:
                assert _linkurl==x.get_url(), \
                       "Link url stored incorrectly."

                self.wt._delObject(x.get_id())
                assert len(self.wt.objectItems())==count, \
                       "Link kill failed."
                return
        self.fail("Link meta type or title invalid after creation.")


    def testCreateMemo(self):
        _memoname='MyMemo'
        _memocont='This is just inane dribble\nwith line feeds\n   and extra spaces'
        count = len(self.wt.objectItems())
        self.wt.add_memo_handler(FakeRequest(),_memoname,_memocont,submit='ok')
        assert len(self.wt.objectItems())==count+1, \
               "Memo creation failed."

        assert self.wt.objectValues('WebtopMemo')[0].title==_memoname, \
               "Memo meta type or title invalid after creation."
        assert self.wt.objectValues('WebtopMemo')[0].get_body()==_memocont, \
               "Memo contents stored incorrectly."

        self.wt._delObject(self.wt.objectIds('WebtopMemo')[0])
        assert len(self.wt.objectItems())==count, \
               "Memo kill failed."

class testWebtopFolderUse(unittest.TestCase):
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
        if len(self.wt.objectIds('WebtopFolder'))>0:
            self.wt._delObject(self.wt.objectIds('WebtopFolder')[0])

    def testIdMapping(self):
        ids = self.f.objectIds('WebtopLink')
        objs = self.f.map_ids_to_objects(ids)

        assert objs[0]==self.item1[1] and objs[1]==self.item2[1], \
               "Id mapping does not work."

    def testRename(self):
        _newname='newuseme'
        self.f.rename_handler(FakeRequest(), (self.item1[0],), (_newname,),
                              submit='ok')

        assert self.item1[1].get_name()==_newname, \
               "Rename failed."

    def testInvalidRename(self):
        try:
            self.f.rename_handler(self.item1[0],self._name2)
        except:
            pass
        else:
            self.fail("Rename did not fail when new name exists.")


    def testMultiTrash(self):
        self.f.remove((self.item1[1],self.item2[1]))
        assert len(self.f.objectItems('WebtopLink'))==0, \
               "Multiple removal failed."

        assert len(self.f.tmp_objects.objectItems('WebtopLink'))==2, \
               "Removed items not found in trash!"


    def testClipboard(self):
        # This test turned off.
        return

        commit()
        self.f.cut((self.item1[1],))
        assert len(self.f.objectItems('WebtopLink'))==1, \
               "Cut operation did not remove object."
        commit()
        self.f.paste()
        assert len(self.f.objectItems('WebtopLink'))==2, \
               "Paste operation did not recreate object."

        commit()
        self.f.paste()
        assert len(self.f.objectItems('WebtopLink'))==3, \
               "Second paste operation did not duplicate object."

        commit()
        self.f.copy((self.item2[1],))
        assert len(self.f.objectItems('WebtopLink'))==3, \
               "Copy didn't work correctly."
        self.f.remove((self.item2[1],))

        commit()
        self.f.paste()
        assert len(self.f.objectItems('WebtopLink'))==3, \
               "Paste didn't work correctly."

        commit()
        c1=0
        c2=0
        for i in self.f.objectValues('WebtopLink'):
            if i.get_url()==self._url:
                c1=c1+1
            elif i.get_url()==self._url2:
                c2=c2+1
        assert c1==2 and c2==1, \
               "Copy/paste operations did not retain object identities."


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(testWebtopFolderCreate))
    s.addTest(unittest.makeSuite(testWebtopFolderUse))
    return s
