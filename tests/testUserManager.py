# $Id: testUserManager.py,v 1.24 2003/06/13 07:57:13 jmp Exp $

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

class testUserManager(unittest.TestCase):
    def setUp(self):
        withUsers()

    def tearDown(self):
        """ """

    def testUserCreation(self):
        """Testing for standard users created in 'withUsers'."""
        users = fle.fle_users.objectIds()
        for i in range(1,4):
            ii=repr(i)
            assert 'user'+ii in users, \
                   "User"+ii+" not created successfully!"

    def testGetRoles(self):
        assert 'User' in fle.fle_users.user2.getRoles() and \
               'FLEAdmin' in fle.fle_users.fleadmin.getRoles() and \
               'User' in fle.fle_users.fleadmin.getRoles(), \
               "UserInfo.getRoles not functional."

    def testGetRolesInObject(self):
        crs = fle.courses.get_child('2')
        assert ('Teacher',) == fle.fle_users.user2.getRolesInObject(crs) and \
               ('Tutor',) == fle.fle_users.user3.getRolesInObject(crs) and \
               ('Student',) == fle.fle_users.user4.getRolesInObject(crs) and \
               len(fle.fle_users.fleadmin.getRolesInObject(crs))==0, \
               "UserInfo.getRolesInObject not functional."

    def testHasRole(self):
        assert fle.fle_users.user2.has_role('User') and \
               fle.fle_users.fleadmin.has_role('FLEAdmin'), \
               "UserInfo.has_role not functional."

    def testHasAnyRole(self):
        assert not fle.fle_users.user2.has_any_role(('Staff','FLEAdmin')) and \
               fle.fle_users.fleadmin.has_any_role(('FLEAdmin','Staff')), \
               "UserInfo.has_any_role not functional."

    def testGroups(self):
        users = fle.fle_users
        count1 = users.get_group_ids_and_names()
        users.add_group('foobar')
        assert 'foobar' in [x[1] for x in users.get_group_ids_and_names()], \
               "Group add or list failed!"
        for x in users.get_group_ids_and_names():
            if x[1]=='foobar':
                gid=x[0]
        users.remove_group(gid)
        assert 'foobar' not in [x[1] for x in users.get_group_ids_and_names()], \
               "Group remove failed!"
        assert count1 == users.get_group_ids_and_names(), \
               "Group count mismatch!"

    def testUserEdit(self):
        users = fle.fle_users.get_users()

        fle.fle_users.add_user(
            uname='joe',
            password='passwd',
            roles=('User',))
        user = fle.fle_users.get_user_info('joe')
        user.set_first_name('Joe')
        user.set_last_name('Smith')
        user.set_email('joe@bar.com')
        user.set_homepage('http://www.mlab.uiah.fi')
        user.set_organization('bar')
        user.set_language('en')

        assert len(fle.fle_users.get_users())==len(users)+1, \
               "Adding a user did not increase user list size correctly."

        fle.fle_users.joe.edit_user_form_handler(
            REQUEST=FakeRequest('joe'),
            # uname='joe',                     # uname
            pwd='passwd',                  # password
            pwd_confirm='passwd',                  # password confirmation
            nickname = None,  # TODO: not used yet
            first_name='Joei',                     # first_name
            last_name='Smithi',                   # last_name
            email='joe@bar.comi',             # email
            organization='orgi',                    # organization
            language='en',                      # language,
            role = None,  # TODO: not used yet
            photo_upload=None,                      # photo_upload
            photo_url='',                        # photo_url
            #group='',                        # group
            address1='Foo Street',              # address
            address2='Fooland',
            city='HELSINKI',                # city
            country='Finland',                 # country
            homepage='http://www.mlab.uiah.fi', # homepage
            phone='123',                     # phone
            gsm='456',                     # gsm
            quote='I\'m prepared for all emergencies but totally unprepared for everyday life.', # quote
            background='ni!',                      # background
            personal_interests='ni!',                      # personal_interests
            professional_interests='ni!',                      # professional_interests
            commit='ok',
            )

        uinfo = fle.fle_users.get_user_info('joe')
        assert uinfo.get_uname()=='joe', \
               "User name invalid after edit."
        assert uinfo.get_last_name()=='Smithi', \
               "User last name invalid after edit."
        assert uinfo.get_first_name()=='Joei', \
               "User first name invalid after edit."
        assert uinfo.get_organization()=='orgi', \
               "User organization invalid after edit."
        assert uinfo.get_city()=='HELSINKI', \
               "User city invalid after edit."

        # change password
        fle.fle_users.joe.edit_user_form_handler(
            FakeRequest('joe'),
            pwd='passwda',                  # password
            pwd_confirm='passwda',          # password confirmation
            commit='ok')

        assert fle.acl_users.getUser('joe').authenticate('passwda', FakeRequest()) == 1, "User password invalid after edit."

        assert fle.acl_users.getUser('joe').authenticate('zpasswda', FakeRequest()) == 0, "User authentication succeed with invalid password."


        #TODO: Check all attributes by calling get_user_info_dict
        # NOTE: get_user_info_dict can't work, and is removed, so
        # NOTE: we will have to get attributes with: get_[attribute]()
        # NOTE: methods of UserInfo class. -granbo

        fle.fle_users.remove_user('joe')
        assert len(fle.fle_users.get_users())==len(users), \
               "Removing a user did not decrease user list size correctly."

    def testFreeze(self):
        uname='user6'
        user = fle.acl_users.getUser(uname)

        password = user._getPassword()
        domains = user.getDomains()
        roles = user.getRoles()

        fle.fle_users.freeze_user(uname)
        fle.fle_users.unfreeze_user(uname)

        user = fle.acl_users.getUser(uname)
        assert password == user._getPassword(), \
               "User's password doesn't survive freezing."
        assert len(domains) == len(user.getDomains()) and \
               not 0 in [x in domains for x in user.getDomains()], \
               "User's domain list doesn't survive freezing."
        assert len(roles) == len(user.getRoles()) and \
               not 0 in [x in roles for x in user.getRoles()], \
               "User's role list doesn't survive freezing: "+str(roles)+" vs. "+str(user.getRoles())


def suite():
    return unittest.makeSuite(testUserManager)
