# $Id: testInputChecks.py,v 1.8 2003/06/13 07:57:13 jmp Exp $

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

from input_checks import *

class testInputChecks(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testIDs(self):
        assert is_valid_id('foobar') and \
               is_valid_id('id_245') and \
               is_valid_id('1234-255aa') and \
               not is_valid_id('ääkkösiä') and \
               not is_valid_id('with whitespace') and \
               not is_valid_id(''), \
               "ID checking doesn't work."

    def testTitles(self):
        assert is_valid_title('foobar') and \
               is_valid_title('This is a test title') and \
               is_valid_title('Also this *should* work...') and \
               not is_valid_title('HTML <a>is not</a> allowed.') and \
               not is_valid_title('') and \
               "Title checking doesn't work."

        assert not is_valid_title(' foobar'), \
            "Whitespace shouldn't be allowed at start"

        assert not is_valid_title('foobar '), \
            "Whitespace shouldn't be allowed at end"

    def testStripTags(self):
        s = 'test<i>with</I>tags\n<P style="foo">of mixed case</p><BR/>'
        s2 = strip_tags(s)
        assert not (re.search("<",s2) or re.search(">",s2)), \
               "Tag stripping does not work."
        s2 = strip_tags(s,['p'])
        assert re.search("<p",s2), \
               "Tags with parameters aren't identified correctly."
        s2 = strip_tags(s,('i','br'))
        assert re.search("<i",s2) and re.search("</i",s2) and \
               re.search("<br/>",s2) and not re.search("<p",s2) and \
               not re.search("</p",s2), \
               "Legal tags not handled correctly."

    def testRenderVertical(self):
        s = "This is a piece of\ntext with <b>several</b> lines\n\n  of text and some tags."
        s2 = render(s)
        assert re.search("^<p>",s2) and re.search("</p>$",s2) and \
               re.search("</p><p>",s2), \
               "Paragraph embedding not functional."
        assert re.search("<br />",s2), \
               "Break insertion not functional."
        assert not re.search("<b>",s2), \
               "Tag removal not functional."

    def testRenderHorizontal(self):
        s = "This is a piece of\ntext with <b>several</b> lines\n\n  of text and some tags."
        s2 = render(s,do_horizontal_space=1)
        assert re.search("<p>&nbsp;&nbsp;",s2), \
               "Horizontal spacing not functional."

    def testRenderMagic(self):
        s = "This is a piece of\ntext with <b>several</b> lines\n\n<p>  of text and some tags."
        s2 = render(s,do_strip=0)
        assert s==s2, \
               "Magic vertical space cutoff not functional."
        s2 = render(s,legal_tags=['p','b'])
        assert s==s2, \
               "Legal tag specification not functional."

    def testUrls(self):
        assert is_valid_url('http://fle3.uiah.fi/') and \
               is_valid_url('ftp://ftp.funet.fi/foo') and \
               is_valid_url('mailto:foo@foobar.com') and \
               is_valid_url('file:///my/file/here'), \
               "URL checking doesn't recognize proper urls"
        assert not is_valid_url('this is not a url') and \
               not is_valid_url('neitheristhis') and \
               not is_valid_url(':nope.foo') and \
               not is_valid_url('www.fi'), \
               "URL checking accepts invalid urls"


def suite():
    return unittest.makeSuite(testInputChecks)

