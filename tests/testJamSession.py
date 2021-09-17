# $Id: testJamSession.py,v 1.5 2003/06/13 07:57:13 jmp Exp $

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

class testJamSession(unittest.TestCase):
    def setUp(self):
        withJamming()

    def tearDown(self):
        pass

    def testBasicSanity(self):
        js1 = fle.courses.get_courses()[1].get_child('jamming').get_children('JamSession')[0]
        assert js1.get_name() == 'jamming session 1', \
               'Jam session has wrong name.'
        assert js1.get_type() == 'linear', \
               'Jam session has wrong type.'
        assert js1.get_description() == 'This is linear blah blah', \
               'Jam session has wrong description.'

        js2 = fle.courses.get_courses()[1].get_child('jamming').get_children('JamSession')[1]
        assert js2.get_type() == 'tree', \
               'Jam session has wrong type.'

    def testArtefactAddingLinear(self):
        js1 = fle.courses.get_courses()[1].get_child('jamming').get_children('JamSession')[0]

        assert len(js1.get_children('JamArtefact')) == 2, \
               'Unexcepted number of JamArtefacts.'

        try:
            js1.add_artefact_form_handler(
                REQUEST=FakeRequest(),
                artefact_name='foo',
                artefact_upload=FakeUpload(
                'foo',
                fle.images.add_memo.data,
                fle.images.add_memo.getContentType()),
                submit=1,
                )
        except:
            pass
        else:
            self.fail('Adding artefact without giving parent_ids did not raise exception')

        try:
            js1.add_artefact_form_handler(
                REQUEST=FakeRequest(),
                artefact_name='foo',
                artefact_upload=FakeUpload(
                'foo',
                fle.images.add_memo.data,
                fle.images.add_memo.getContentType()),
                parent_ids = (js1.get_children('JamArtefact')[0].get_id(),),
                submit=1,
                )
        except:
            pass
        else:
            self.fail('Adding artefact as to child of non-last artefact on linear jamming session did not raise excpetion')

        js1.add_artefact_form_handler(
            REQUEST=FakeRequest(),
            artefact_name='foo',
            artefact_upload=FakeUpload(
            'foo',
            fle.images.add_memo.data,
            fle.images.add_memo.getContentType()),
            parent_ids = (js1.get_children('JamArtefact')[1].get_id(),),
            submit=1,
            )
        commit()

        assert len(js1.get_children('JamArtefact')) == 3, \
               'Adding artefact failed.'


    def testArtefactAddingTree(self):
        js2 = fle.courses.get_courses()[1].get_child('jamming').get_children('JamSession')[1]

        assert len(js2.get_children('JamArtefact')) == 1, \
               'Unexcepted number of JamArtefacts.'

        try:
            js2.add_artefact_form_handler(
                REQUEST=FakeRequest(),
                artefact_name='foo',
                artefact_upload=FakeUpload(
                'foo',
                fle.images.add_memo.data,
                fle.images.add_memo.getContentType()),
                submit=1,
                )
        except:
            pass
        else:
            self.fail('Adding artefact without giving parent_ids did not raise exception')

        js2.add_artefact_form_handler(
            REQUEST=FakeRequest(),
            artefact_name='foo',
            artefact_upload=FakeUpload(
            'foo',
            fle.images.add_memo.data,
            fle.images.add_memo.getContentType()),
            parent_ids = (js2.get_children('JamArtefact')[0].get_id(),),
            submit=1,
            )
        commit()
        assert len(js2.get_children('JamArtefact')) == 2, \
               'Adding artefact failed.'

        try:
            js2.add_artefact_form_handler(
                REQUEST=FakeRequest(),
                artefact_name='foo',
                artefact_upload=FakeUpload(
                'foo',
                fle.images.add_memo.data,
                fle.images.add_memo.getContentType()),
                parent_ids = (js2.get_children('JamArtefact')[0].get_id(),
                              js2.get_children('JamArtefact')[1].get_id()),
                submit=1,
                )
        except:
            pass
        else:
            self.fail('Adding artefact with several parent_ids did not raise exception')

        try:
            js2.add_artefact_form_handler(
                REQUEST=FakeRequest(),
                artefact_name='foo',
                artefact_upload=FakeUpload(
                'foo',
                fle.images.add_memo.data,
                fle.images.add_memo.getContentType()),
                parent_ids = ('some_id_that_does_not_exist',),
                submit=1,
                )
        except:
            pass
        else:
            self.fail('Adding artefact with invalid parent_ids did not raise exception')


def suite():
    return unittest.makeSuite(testJamSession)
