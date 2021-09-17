# $Id: testWebtop.py,v 1.5 2003/06/13 07:57:13 jmp Exp $

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

class testWebtop(unittest.TestCase):
    def setUp(self):
        withUsers()

    def tearDown(self):
        pass

    def testFindWebtop(self):
        # Possibly create the webtop
        wt1 = fle.fle_users.user1.get_webtop()
        # Second call should use the same webtop
        wt2 = fle.fle_users.user1.get_webtop()
        assert wt1==wt2 and not wt1==None, \
               "Webtop access method nonfunctional."




def suite():
    return unittest.makeSuite(testWebtop)

