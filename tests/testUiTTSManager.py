# $Id: testUiTTSManager.py,v 1.11 2003/06/13 07:57:13 jmp Exp $

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
import re
from Errors import *

class testUiTTSManager(unittest.TestCase):
    def setUp(self):
        withCourse()
        commit()

    def tearDown(self):
        pass

    def testTTSManager(self):
        _url='/testfle/courses/typesets/'
        res = wwwtest(_url,user='fleadmin:ni')

        assert re.search('Progressive Inquiry',res) and \
               re.search('Design Thinking Types',res), \
               "Type sets not displayed!"

    def testTTSInfo(self):
        _url='/testfle/courses/typesets/pitt/'
        res = wwwtest(_url,user='fleadmin:ni')

        assert re.search('Progressive Inquiry',res), \
               "Type set info not displayed!"

        assert re.search(fle.typesets.pitt.get_description()[:30],res), \
               "Type set description not displayed!"

    def testTTSHelp(self):
        _url='/testfle/courses/2/4/6/describe_thinking_types'
        res = wwwtest(_url,user='fleadmin:ni')

        assert re.search('Progressive Inquiry',res), \
               "Type set info not displayed!"



    def testTTSCopy(self):
        _url='/testfle/courses/typesets/start_edit_from_existing?tts_id=pitt'
        res = wwwtest(_url,user='fleadmin:ni',expected=302)
        tmp_id = re.search("Location: .*/(.*)/edit_form_1_3\?",res).group(1)

        commit()
        _url='/testfle/courses/typesets/tmp_objects/'+tmp_id+'/'
        res = wwwtest(_url,user='fleadmin:ni')

        assert re.search('Progressive Inquiry',res) and \
               re.search('(fleadmin)',res), \
               "Draft TTS not displayed correctly."

        _url='/testfle/courses/typesets/'
        res = wwwtest(_url,user='fleadmin:ni')

        assert re.search('tmp_objects.*(fleadmin)',res), \
               "Draft TTS not shown in list."

        _url='/testfle/courses/typesets/tmp_objects/'+tmp_id+'/finalize_set'
        res = wwwtest(_url,user='fleadmin:ni',expected=302)
        _url='/testfle/courses/typesets/'
        res = wwwtest(_url,user='fleadmin:ni')

        assert re.search('(fleadmin)',res) and \
               not re.search('tmp_objects.*(fleadmin)',res), \
               "Finalized TTS not shown in list."

        #real_id = getattr(fle.typesets.tmp_objects,tmp_id).get_id()
        _url='/testfle/courses/typesets/form_handler?delete=yes&sets=tts1'
        res = wwwtest(_url,user='fleadmin:ni',expected=200)
        _url='/testfle/courses/typesets/delete_form_handler?delete=yes&sets=tts1'
        res = wwwtest(_url,user='fleadmin:ni',expected=302)
        commit()
        _url='/testfle/courses/typesets/'
        res = wwwtest(_url,user='fleadmin:ni')
##         assert not re.search('(fleadmin)',res) and \
##                not re.search('Unfinished',res), \
##                "TTS delete does not work."
##         commit()


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(testUiTTSManager))
    return s

