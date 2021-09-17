# $Id: testFLEInstall.py,v 1.21 2003/06/13 07:57:13 jmp Exp $

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
import os
from common import get_roles

class testFLEInstall(unittest.TestCase):
    def testInstall(self):
        assert app.objectValues('FLE'), \
               "FLE installation failed!"

    def testFleUser(self):
        fleu = fle.fle_users.objectIds()
        assert 'fleadmin' in fleu, \
               "fleadmin missing from fle_users!"
    def testAclUser(self):
        aclu = fle.acl_users.getUserNames()
        assert 'fleadmin' in aclu, \
               "fleadmin missing from acl_users!"
    def testRoles(self):
        reqs = ['FLEAdmin','Staff','User']
        roles = fle.valid_roles()
        for id in reqs:
            assert id in roles, \
                   "Role "+id+" missing!"
    def testUserRoles(self):
        #roles=fle.acl_users.getUsers()[0].getRoles()
        roles = get_roles(fle,'fleadmin')
        assert 'FLEAdmin' in roles and 'User' in roles, \
               "Administrator does not have FLEAdmin+User roles!"

    def testLanguages(self):
        assert len(fle.langs.keys())>=2, \
               "Languages aren't loaded properly."
        message="Missing keywords:"
        errors=0
        en = fle.langs['en']
        # Check that keywords for 'en' are in all languages
        for (la_name,la) in fle.langs.items():
            for (mod,trans) in la.items():
                if mod=='removed':
                    pass
                else:
                    for keyword in en[mod].keys():
                        if keyword!='charset_encoding' and \
                           not keyword in trans.keys():
                            message+=" "+la_name+"/"+mod+": "+keyword
                            errors+=1

        message2="Extra keywords:"
        # Check that no language contains keywords not in 'en'
        for (la_name,la) in fle.langs.items():
            for (mod,trans) in la.items():
                if mod=='removed':
                    message2+=" UNUSED KEYWORDS IN 'removed' MODULE"
                    errors+=1
                else:
                    for keyword in trans.keys():
                        if not keyword in en[mod].keys():
                            message2+=" "+la_name+"/"+mod+": "+keyword
                            errors+=1


        message3 = "Unused keywords:"
##         for (mod,trans) in en.items():
##             for keyword in trans.keys():
##                 lines = os.popen("grep -r 'L_%s' . | grep -v '\.pyc'" % keyword).readlines()
##                 print keyword+"/"+str(len(lines))+"/"+str(errors)
##                 if len(lines)==0:
##                     message3+=" "+mod+": "+keyword
##                     errors+=1

        assert errors==0, \
               "Language translations not ok!\n"+message+"\n"+message2+"\n"+message3


    def testTypeSets(self):
        assert fle.typesets.pitt.sort_order == \
               ['problem', 'my_expl', 'sci_expl', 'evaluation', 'summary'], \
               "Thinking type sort order not correct."

        assert fle.typesets.pitt.get_description(), \
               "TTS descriptions not loaded."

##     def testDeveloperControls(self):
##         _url = '/testfle/courses/'
##         res = wwwtest(_url,user='fleadmin:ni')
##         assert not re.search('Controls for developers',res), \
##                "Developer controls are initially visible."
##         fle.show_developer_controls=1
##         commit()
##         res = wwwtest(_url,user='fleadmin:ni')
##         assert re.search('Controls for developers',res), \
##                "Developer controls not shown even when property is activated."
##         fle.show_developer_controls=0
##         commit()
##         res = wwwtest(_url,user='fleadmin:ni')
##         assert not re.search('Controls for developers',res), \
##                "Developer controls shown even when property is deactivated."

def suite():
    return unittest.makeSuite(testFLEInstall)

