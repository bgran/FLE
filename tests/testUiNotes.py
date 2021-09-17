# $Id: testUiNotes.py,v 1.24 2003/06/13 07:57:13 jmp Exp $

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

class testUiNotes(unittest.TestCase):
    def setUp(self):
        withNotes()
        #commit()

    def tearDown(self):
        pass

    def testEmptyThread(self):
        _url='/testfle/courses/2/4/6/'
        res = wwwtest(_url,user='user2:passwd2')

        assert re.search('Discussion 2',res) and \
               re.search('Body 2',res), \
               "Note body and subject are not displayed in thread view."

    def testThreadWithReplies(self):
        _url='/testfle/courses/2/4/5/'
        res = wwwtest(_url,user='user2:passwd2')

        assert re.search('Discussion 1',res) and \
               re.search('Body 1',res), \
               "Note body and subject are not displayed in thread view."


    def testNewNoteStatus(self):
        # first make sure we visit notes 5/7 and 5
        _url='/testfle/courses/2/4/5/'
        res = wwwtest(_url,user='user2:passwd2')
        _url='/testfle/courses/2/4/5/7/'
        res = wwwtest(_url,user='user2:passwd2')
        _url='/testfle/courses/2/4/5/'
        res = wwwtest(_url,user='user2:passwd2')

        # check that notes 5 and 5/7 are "read" and note 5/7/9 is not
        # unread notes should have the <b> start tag in the same
        # line before the note subject
        assert re.search('<b>.*Reply to R1/D1',res) and \
               not re.search('<b>.*Discussion 1',res) and \
               not re.search('<b>.*Reply 1 to D1',res), \
               "Read and unread notes aren't displayed correctly."

    def testReply(self):
        _url='/testfle/courses/2/4/5/7/'
        res = wwwtest(_url,user='user2:passwd2')

        assert re.search('Reply 1 to D1',res) and \
               re.search('Body.*r1d1',res), \
               "Note body and subject are not displayed in thread view."

        assert re.search('Test Course 2',res) and \
               re.search('Context2',res) and \
               re.search('Discussion 1',res), \
               "Note context (course, context and thread) not shown."

    def testNotePreviewPublish(self):
        """Test that note previewing and publishing works for thread starters."""
        # CREATE
        _url = "/testfle/courses/2/4/reply_button_handler?tt_id=problem"
        res = wwwtest(_url,user="user2:passwd2",expected=302)
        tmp_id = re.search("Location: tmp_objects/(.*)/edit_form",res).group(1)
        # EDIT
        _url = "/testfle/courses/2/4/tmp_objects/%s/edit_form" % tmp_id
        res = wwwtest(_url,user="user2:passwd2")
        # SUBMIT
        _url = "/testfle/courses/2/4/tmp_objects/%s/edit_note_form_handler?tt_id=problem&subject=subject_foo&url=&url_name=&image_name=&body=body_foo&preview=ok" % tmp_id
        res = wwwtest(_url,user="user2:passwd2",expected=302)
        # PREVIEW
        _url = "/testfle/courses/2/4/tmp_objects/%s/preview_form" % tmp_id
        res = wwwtest(_url,user="user2:passwd2")
        # SUBMIT
        _url = "/testfle/courses/2/4/tmp_objects/%s/preview_form_handler?post=ok" % tmp_id
        res = wwwtest(_url,user="user2:passwd2",expected=302)
        real_id = re.search("Location: .*/(.*)/index_html\?",res).group(1)
        _url = "/testfle/courses/2/4/%s" % real_id

        # VIEW PUBLISHED
        res = wwwtest(_url,user="user2:passwd2")

        assert re.search("subject_foo",res) and \
               re.search("body_foo",res), \
               "Published note doesn't have correct information."

    def testNotePreviewPublish2(self):
        """Check that note previewing and publishing works for thread replies."""
        # CREATE
        _url = "/testfle/courses/2/4/5/reply_button_handler?tt_id=problem"
        res = wwwtest(_url,user="user2:passwd2",expected=302)
        tmp_id = re.search("Location: tmp_objects/(.*)/edit_form",res).group(1)
        # EDIT
        _url = "/testfle/courses/2/4/5/tmp_objects/%s/edit_form" % tmp_id
        res = wwwtest(_url,user="user2:passwd2")
        # SUBMIT
        _url = "/testfle/courses/2/4/5/tmp_objects/%s/edit_note_form_handler?tt_id=problem&subject=subject_foo&url=&url_name=&image_name=&body=body_foo&preview=ok" % tmp_id
        res = wwwtest(_url,user="user2:passwd2",expected=302)
        # PREVIEW
        _url = "/testfle/courses/2/4/5/tmp_objects/%s/preview_form" % tmp_id
        res = wwwtest(_url,user="user2:passwd2")
        # SUBMIT
        _url = "/testfle/courses/2/4/5/tmp_objects/%s/preview_form_handler?post=ok" % tmp_id
        res = wwwtest(_url,user="user2:passwd2",expected=302)
        real_id = re.search("Location: .*/(.*)/index_html\?",res).group(1)
        _url = "/testfle/courses/2/4/5/%s" % real_id

        # VIEW PUBLISHED
        res = wwwtest(_url,user="user2:passwd2")

        assert re.search("subject_foo",res) and \
               re.search("body_foo",res), \
               "Published note doesn't have correct information."

    def testNotePreviewCancel(self):
        """Test that note previewing and canceling works for thread starters."""
        # CREATE
        _url = "/testfle/courses/2/4/reply_button_handler?tt_id=problem"
        res = wwwtest(_url,user="user2:passwd2",expected=302)
        tmp_id = re.search("Location: tmp_objects/(.*)/edit_form",res).group(1)
        # EDIT
        _url = "/testfle/courses/2/4/tmp_objects/%s/edit_form" % tmp_id
        res = wwwtest(_url,user="user2:passwd2")
        # SUBMIT
        _url = "/testfle/courses/2/4/tmp_objects/%s/edit_note_form_handler?tt_id=problem&subject=subject_foo&url=&url_name=&image_name=&body=body_foo&preview=ok" % tmp_id
        res = wwwtest(_url,user="user2:passwd2",expected=302)
        # PREVIEW
        _url = "/testfle/courses/2/4/tmp_objects/%s/preview_form" % tmp_id
        res = wwwtest(_url,user="user2:passwd2")
        # CANCEL
        _url = "/testfle/courses/2/4/tmp_objects/%s/preview_form_handler?cancel=ok" % tmp_id
        res = wwwtest(_url,user="user2:passwd2",expected=302)

    def testNotePreviewCancel2(self):
        """Test that note previewing and cancelin works for thread replies."""
        # CREATE
        _url = "/testfle/courses/2/4/5/reply_button_handler?tt_id=problem"
        res = wwwtest(_url,user="user2:passwd2",expected=302)
        tmp_id = re.search("Location: tmp_objects/(.*)/edit_form",res).group(1)
        # EDIT
        _url = "/testfle/courses/2/4/5/tmp_objects/%s/edit_form" % tmp_id
        res = wwwtest(_url,user="user2:passwd2")
        # SUBMIT
        _url = "/testfle/courses/2/4/5/tmp_objects/%s/edit_note_form_handler?tt_id=problem&subject=subject_foo&url=&url_name=&image_name=&body=body_foo&preview=ok" % tmp_id
        res = wwwtest(_url,user="user2:passwd2",expected=302)
        # PREVIEW
        _url = "/testfle/courses/2/4/5/tmp_objects/%s/preview_form" % tmp_id
        res = wwwtest(_url,user="user2:passwd2")
        # CANCEL
        _url = "/testfle/courses/2/4/5/tmp_objects/%s/preview_form_handler?cancel=ok" % tmp_id
        res = wwwtest(_url,user="user2:passwd2",expected=302)

    def testNotePreviewEdit(self):
        """Note previewing and publishing for thread starters."""
        # CREATE
        _url = "/testfle/courses/2/4/reply_button_handler?tt_id=problem"
        res = wwwtest(_url,user="user2:passwd2",expected=302)
        tmp_id = re.search("Location: tmp_objects/(.*)/edit_form",res).group(1)
        # EDIT
        _url = "/testfle/courses/2/4/tmp_objects/%s/edit_form" % tmp_id
        res = wwwtest(_url,user="user2:passwd2")
        # SUBMIT
        _url = "/testfle/courses/2/4/tmp_objects/%s/edit_note_form_handler?tt_id=problem&subject=subject_foo&url=&url_name=&image_name=&body=body_foo&preview=ok" % tmp_id
        res = wwwtest(_url,user="user2:passwd2",expected=302)
        # PREVIEW
        _url = "/testfle/courses/2/4/tmp_objects/%s/preview_form" % tmp_id
        res = wwwtest(_url,user="user2:passwd2")
        # SUBMIT
        _url = "/testfle/courses/2/4/tmp_objects/%s/preview_form_handler?edit=ok" % tmp_id
        res = wwwtest(_url,user="user2:passwd2",expected=302)
        # RE-EDIT
        _url = "/testfle/courses/2/4/tmp_objects/%s/edit_form" % tmp_id
        res = wwwtest(_url,user="user2:passwd2")
        # SUBMIT
        _url = "/testfle/courses/2/4/tmp_objects/"+tmp_id+"/edit_note_form_handler?subject=subject_foo2&url=&url_name=&image_name=&body=body_foo2&preview=ok"
        res = wwwtest(_url,user="user2:passwd2",expected=302)
        # PREVIEW
        _url = "/testfle/courses/2/4/tmp_objects/%s/preview_form" % tmp_id
        res = wwwtest(_url,user="user2:passwd2")
        # PUBLISH
        _url = "/testfle/courses/2/4/tmp_objects/"+tmp_id+"/preview_form_handler?post=ok"
        res = wwwtest(_url,user="user2:passwd2",expected=302)

        real_id = re.search("Location: .*/(.*)/index_html\?",res).group(1)
        _url = "/testfle/courses/2/4/"+real_id

        # VIEW PUBLISHED
        res = wwwtest(_url,user="user2:passwd2")

        assert re.search("subject_foo2",res) and \
               re.search("body_foo2",res), \
               "Re-edited published note doesn't have correct information."


    def testUiSerlaDefaultSort(self):
        _url='/testfle/courses/2/4/5/?state_url=6,1inline1'
        res = wwwtest(_url,user='user2:passwd2')

        assert re.search("Body 1",res) and \
               re.search("Body r1d1",res) and \
               re.search("Body r1r1d1",res) and \
               re.search("Body r2d1",res), \
               "Inline note view does not show all notes."

    def testUiSerlaTTSort(self):
        _url='/testfle/courses/2/4/5/?state_url=7,10printertt_printer6,1inline1'
        res = wwwtest(_url,user='user2:passwd2')

        assert re.search("Body 1",res) and \
               re.search("Body r1d1",res) and \
               re.search("Body r1r1d1",res) and \
               re.search("Body r2d1",res), \
               "Inline note view (sort by TT) does not show all notes."

    def testUiSerlaPersonSort(self):
        _url='/testfle/courses/2/4/5/?state_url=7,14printerauthor_printer6,1inline1'
        res = wwwtest(_url,user='user2:passwd2')

        assert re.search("Body 1",res) and \
               re.search("Body r1d1",res) and \
               re.search("Body r1r1d1",res) and \
               re.search("Body r2d1",res), \
               "Inline note view (sort by author) does not show all notes."

    def testUiSerlaDateSort(self):
        _url='/testfle/courses/2/4/5/?state_url=7,12printerdate_printer6,1inline1'
        res = wwwtest(_url,user='user2:passwd2')

        assert re.search("Body 1",res) and \
               re.search("Body r1d1",res) and \
               re.search("Body r1r1d1",res) and \
               re.search("Body r2d1",res), \
               "Inline note view (sort by date) does not show all notes."

    def testUiNoteSort(self):
        res = wwwtest('/testfle/courses/2/4/5/',user='user2:passwd2')

        assert -1 < res.find('Discussion 1') < \
               res.find('Reply 1 to D1') < \
               res.find('Reply to R1/D1') < \
               res.find('Reply 2 to D1'), \
               "Thread sort doesn't work."

    def testUiNoteSortByTT(self):
        res = wwwtest('/testfle/courses/2/4/5/?state_url=7,10printertt_printer',user='user2:passwd2')

        assert -1 < res.find('Discussion 1') < \
               res.find('Reply 1 to D1') < \
               res.find('Reply 2 to D1') < \
               res.find('Reply to R1/D1'), \
               "Thread sort by TT doesn't work."

    def testUiNoteSortByAuthor(self):
        res = wwwtest('/testfle/courses/2/4/5/?state_url=7,14printerauthor_printer',user='user2:passwd2')

        assert -1 < res.find('Discussion 1') < \
               res.find('Reply 1 to D1'), \
               "Thread sort by author doesn't work."

    def testUiNoteCensorButton(self):
        _url='/testfle/courses/2/4/6/'
        res = wwwtest(_url,user='user2:passwd2')
        assert re.search('name="censor"',res), \
               "Censor button not shown to teacher."
        res = wwwtest(_url,user='user3:passwd3')
        assert not re.search('name="censor"',res), \
               "Censor button is shown to normal users."
        _url='/testfle/courses/2/4/5/'
        res = wwwtest(_url,user='user2:passwd2')
        assert not re.search('name="censor"',res), \
               "Censor button shown to author."

    def testUiNoteCensoring(self):
##         ctx = fle.courses.get_child('2').get_child('4')
##         tts = ctx.get_thinking_type_set().get_thinking_types()
##         (id,note) = ctx.add_note(tts[2].get_id(),'user3','Offending message','This course sucks!')
##         note.do_publish()
##         commit()

        id=6
        _url='/testfle/courses/2/4/'+str(id)+'/censor_note_handler'
        # User2 is teacher
        res = wwwtest(_url,user='user3:passwd3',expected=401)
        # res = wwwtest(_url,user='user2:passwd2')
        # FIXME: What was the line above supposed to do?

        _url='/testfle/courses/2/4/'+str(id)+'/censor_note_handler?censor=yes'
        res = wwwtest(_url,user='user2:passwd2')

        _url='/testfle/courses/2/4/'+str(id)+'/'
        res = wwwtest(_url,user='user6:passwd6')

        assert not re.search('Discussion 2',res) and \
               not re.search('Body 2',res), \
               "Note body and subject are shown even when censored."

        res = wwwtest(_url,user='user3:passwd3')

        assert re.search('Discussion 2',res) and \
               re.search('Body 2',res), \
               "Author of censored note can't see the note contents."
        assert re.search('Poistettu',res), \
               "Author of censored note can't see censor notice."

        res = wwwtest(_url,user='user2:passwd2')

        assert re.search('Discussion 2',res) and \
               re.search('Body 2',res), \
               "Teacher can't see the censored note contents."
        assert re.search('Poistettu',res), \
               "Teacher can't see censor notice of censored note."
        assert re.search('name="uncensor"',res), \
               "Teacher can't see uncensor button."



def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(testUiNotes))
    return s
