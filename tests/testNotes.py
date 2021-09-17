# $Id: testNotes.py,v 1.7 2003/06/13 07:57:13 jmp Exp $

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

class testNotes(unittest.TestCase):
    def setUp(self):
        withNotes()
        self.ctx=fle.courses.get_courses()[1].get_course_contexts()[1]
        self.note=self.ctx.get_children('Note')[0]

    def tearDown(self):
        pass

    def testNoteBody(self):
        assert self.note.get_body()=='Body 1\nsecond line', \
               "Note body is invalid."
    def testNoteSubject(self):
        assert self.note.get_subject(None)=='Discussion 1', \
               "Note subject is invalid."
    def testNoteAuthor(self):
        assert self.note.get_author()=='user2', \
               "Note author is invalid."
    def testAddFailTts(self):
        try:
            self.ctx.add_reply(None,'user2','foo','bar','','','','')
        except:
            pass
        else:
            self.fail("Reply add without thinking type succeeded.")
    #TODO: Enable this test, fix the code accordingly
    def off_testAddFailAuthor(self):
        try:
            self.ctx.add_reply(
                self.ctx.get_thinking_type_set().\
                get_thinking_types()[0].get_id(),
                'user1','foo','bar','','','','')
        except:
            pass
        else:
            self.fail("Reply with author not in course succeeded.")

    def testStartingNote(self):
        assert self.note.is_starting_note(), \
               "Discussion start note doesn't think so."

    def testFollowingNote(self):
        assert not self.note.get_children('Note')[0].is_starting_note(), \
               "Discussion follow-up note thinks it's starting the thread."

    def testStructure(self):
        assert self.note.get_n_notes()==4, \
               "Note structure not consistent."
        assert self.note.get_children('Note')[0].get_n_notes()==2, \
               "Note structure not consistent, check 2."
        assert self.ctx.get_children('Note')[1].get_n_notes()==1, \
               "Note structure not consistent, check 3."

    def testUnreadCount(self):
        assert self.ctx.get_n_unread_notes('user2')==5, \
               "Unread note count fails."

    def testReadUnread(self):
        count = self.note.get_n_unread_notes('user2')
        self.note.update_reader('user2')
        assert self.note.get_n_unread_notes('user2')==count-1, \
               "Unread note count not decreased upon read."
        assert self.note.is_reader('user2'), \
               "Read note still thinks it's unread."
        del self.note.readers['user2']

def suite():
    return unittest.makeSuite(testNotes)
