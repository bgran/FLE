# $Id: testJamArtefact.py,v 1.5 2003/06/13 07:57:13 jmp Exp $

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

class testJamArtefact(unittest.TestCase):
    def setUp(self):
        withJamming()

    def tearDown(self):
        pass

    def testBasicSanity(self):
        ja = fle.courses.get_courses()[1].get_child('jamming').get_children('JamSession')[0].get_children('JamArtefact')[1]
        assert ja.get_name() == 'waste icon', \
               'Wrong name.'
        assert len(ja.get_parent_ids()) == 1, \
               'Wrong number of parents.'
        assert len(ja.get_children_artefacts()) == 0, \
               'This artefact should not have any children.'

    def testAnnotation(self):
        ja = fle.courses.get_courses()[1].get_child('jamming').get_children('JamSession')[0].get_children('JamArtefact')[1]
        assert ja.get_n_annotations() == 0, \
               'Artefact should not have annotations.'

        import time
        ja.add_annotation('user1', time.time(), 'some annotation text')
        assert ja.get_n_annotations() == 1, \
               'Adding annotation did not work.'


def suite():
    return unittest.makeSuite(testJamArtefact)

