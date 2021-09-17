# $Id: testUiUserManager.py,v 1.10 2003/06/13 07:57:13 jmp Exp $

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

class testUiUserManager(unittest.TestCase):
    def setUp(self):
        withUsers()
        commit()

    def tearDown(self):
        pass

    def testUserManager(self):
        _url='/testfle/fle_users/'
        res = wwwtest(_url,user='fleadmin:ni')

        assert re.search('user1',res) and \
               re.search('user2',res) and \
               re.search('user3',res), \
               "Users not displayed on user management front page."

##     def testUserManagementAccess(self):
##         _url='/testfle/fle_users/'
##         # Check that default user (user1) does not have access to
##         # course management.
##         try:
##             wwwtest(_url,expected=401)
##         except AssertionError:
##             self.fail("Normal user can view user management front page.")

    def testUserInfoView(self):
        _url='/testfle/fle_users/user2/show_user_info'
        res = wwwtest(_url,user='fleadmin:ni')

        assert re.search('user2',res) and \
               re.search('First2',res) and \
               re.search('Last2',res) and \
               re.search('joe2@foo.fi',res) and \
               re.search('Quote2',res) and \
               re.search('>fi<',res) and \
               re.search('Country2',res), \
               "User info not displayed correctly."

    def testUserEditForm(self):
        _url='/testfle/fle_users/user2/edit_user_form'
        res = wwwtest(_url,user='fleadmin:ni')

        assert re.search('user2',res), \
               "User edit form invalid."

    def testUserEditFormAccess(self):
        _url='/testfle/fle_users/user2/edit_user_form'
        res = wwwtest(_url,user='user2:passwd2')
        res = wwwtest(_url,user='fleadmin:ni')
        _url='/testfle/fle_users/user2/edit_user_form_handler'
        res = wwwtest(_url,user='fleadmin:ni')
        res = wwwtest(_url,user='user2:passwd2')
        res = wwwtest(_url,user='user1:passwd1',expected=401)

    def testUserInfoViewAccess(self):
        _url='/testfle/fle_users/user2/show_user_info'
        # called by user1
        res = wwwtest(_url)

    def testUserInvitationAccess(self):
        try:
            wwwtest('/testfle/fle_users/invite_user',expected=401)
        except AssertionError:
            self.fail("Normal user can invite users")

    def testUserInvitationForm(self):
        res = wwwtest('/testfle/fle_users/invite_user_form',user='fleadmin:ni')
        assert re.search('value="Invite"',res), \
               "Invitation form not found in invitation page"

    def testUserInvitation(self):
        res = wwwtest('/testfle/fle_users/invite_user?emails:string=foo@bar.com&message=This+is+a+test+invitation&language=en&course_ids=2',user='fleadmin:ni')
        assert not re.search('errordialogbg',res), \
               "Error during user invitation"

##        commit()
##         assert 'foo@bar.com' in fle.fle_users.pending_users.keys(), \
##                "Invited e-mail not added to pending users"

        (header,body) = sent_emails[-1]
        import quopri
        from cStringIO import StringIO
        mfile = StringIO(body)
        mfile2 = StringIO()
        quopri.decode(mfile,mfile2)
        body = mfile2.getvalue()

        rs = re.search('http://127.0.0.1/Zope(.*)',body)
        _url=rs.group(1)
        res = wwwtest(_url,user='')

        assert re.search('action="add_invited_user"',res), \
               "Invited user registration form not shown."
        auth = re.search('name="auth" type="hidden" value="(.*)">',res).group(1)

        res = wwwtest('/testfle/fle_users/add_invited_user?uname=invuser&password1=ni&password2=ni&first_name=inv&last_name=user&email=foo@bar.com&auth=%s' % auth,user='',expected=302)

##         commit()
##         assert 'foo@bar.com' not in fle.fle_users.pending_users.keys(), \
##                "Registered user not removed from pending users"


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(testUiUserManager))
    return s
