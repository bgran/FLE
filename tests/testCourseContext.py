# $Id: testCourseContext.py,v 1.16 2003/06/13 07:57:13 jmp Exp $

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

class testCourseContext(unittest.TestCase):
    def setUp(self):
        withNotes()

    def tearDown(self):
        pass

    def testInitialDiscussions(self):
        ctx = fle.courses.get_courses()[1].get_course_contexts()[1]
        assert len(ctx.get_children('Note'))==2, \
               "Discussion creation failed."
        assert ctx.get_n_notes()==5, \
               "Note amount calculation broken."
        assert ctx.get_n_unread_notes('user2')==5, \
               "Unread note amount calculation broken."


    def testInformation(self):
        ctx = fle.courses.get_courses()[1].get_course_contexts()[1]
        assert ctx.get_author()=='user3', \
               "Context owner name invalid."
        assert ctx.get_long_description()=='Long description 2\n\nContains several\n line feeds and whitespace.', \
               "Context long description invalid."
        assert ctx.get_course_ref()==fle.courses.get_courses()[1], \
               "Context course reference invalid."

##     def testEditInformation(self):
##         ctx = fle.courses.get_courses()[1].get_course_contexts()[1]

##         name = ctx.get_name()
##         tts_id = ctx.get_thinking_type_set_id()
##         desc = ctx.get_description()
##         desc_long = ctx.get_long_description()
##         # edit context info
##         ctx.edit_course_context(
##             REQUEST = FakeRequest(),
##             my_name = name,
##             description = desc,
##             description_long = '*modified* Long description 2',
##             publish='ok')

##         assert ctx.get_long_description()=='*modified* Long description 2', \
##                "Context long description invalid."

##         # check thinking type set
##         assert ctx.get_thinking_type_set_id() == 'pitt'

##         # return old context info
##         ctx.edit_course_context(
##             REQUEST = FakeRequest(),
##             my_name = name,
##             description = desc,
##             description_long = desc_long,
##             publish='ok')

    def testNoteStructure(self):
        ctx = fle.courses.get_courses()[1].get_course_contexts()[1]
        discussions = ctx.objectValues('Note')
        assert len(discussions)==2, \
               "Discussion amount invalid."
        replies = discussions[0].objectValues('Note')
        assert len(replies)==2, \
               "Replies for first discussion lost."
        assert len(replies[0].objectValues('Note'))==1, \
               "Reply to first discussion reply lost."

    def testTypeSet(self):
        ctx = fle.courses.get_courses()[1].get_course_contexts()[1]

        assert [x.get_id() \
                for x in ctx.get_thinking_type_set().get_thinking_types()] == \
                [x.get_id() \
                for x in fle.typesets.pitt.get_thinking_types()], \
                "Context knowledge type set does not match global set."


def suite():
    return unittest.makeSuite(testCourseContext)
