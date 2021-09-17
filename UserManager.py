# $Id: UserManager.py,v 1.230 2004/10/21 16:44:38 tarmo Exp $
#
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

"""Contains class UserManager, which is the holder and factory object
for FLE users."""

__version__ = "$Revision: 1.230 $"[11:-2]

from time import time
import types, Errors
from urllib import quote_plus

import re
import string
import Globals
import OFS
from Globals import Persistent, Acquisition, PersistentMapping
from OFS.Image import Image
from AccessControl import ClassSecurityInfo

from TraversableWrapper import TraversableWrapper
from Cruft import Cruft
from UserDict import UserDict

from UserInfo import UserInfo
from Webtop import Webtop
from common import get_url, reload_dtml, add_dtml, new_reload_dtml, \
     make_action, get_roles, get_local_roles
from common import perm_view, perm_edit, perm_manage, perm_add_lo
from input_checks import is_valid_title, is_valid_id, is_valid_url, \
     is_valid_uname

# Instance of this class is FLE/fle_users and contains
# all UserInfo objects.
# This class contains factory methods for creating and removing users.
# User editing is in the UserInfo class.
class UserManager(
    TraversableWrapper,
    Cruft,
    Persistent,
    OFS.Folder.Folder,
    OFS.SimpleItem.Item,
    ):
    """FLE user manager."""

    meta_type = 'UserManager'
    dtml_files = (
        ('index_html', 'Index page',
         'ui/UserManager/index_html'),
        ('show_pending', 'Lists pending users',
         'ui/UserManager/show_pending'),
        ('invite_user_form', 'Invite User Form',
         'ui/UserManager/invite_user_form'),
        ('register_user_form', 'Register User Form',
         'ui/UserManager/register_user_form'),
        ('remove_user_form', 'Remove User Form',
         'ui/UserManager/remove_user_form'),
        ('remove_users_confirm', 'Remove Users Confirmation',
         'ui/UserManager/remove_users_confirm'),
        ('group_management_form', 'Group Management Form',
         'ui/UserManager/group_management_form'),

        ('fle_form_header', 'Standard Html Header for forms (UM)',
         'ui/UserManager/fle_form_header'),

        ('fle_html_header', 'Standard FLE Html Header (UM)',
         'ui/UserManager/fle_html_header'),

        ('user_list', '', 'ui/UserManager/user_list'),

        # Taken from UserInfo.py
        ('show_user_info', 'user info page',
         'ui/UserInfo/show_user_info'),
        ('user_info', 'actual content',
         'ui/UserInfo/user_info'),

        ('edit_user_form', '',
         'ui/UserInfo/edit_user_form'),

        )

    security = ClassSecurityInfo()
    security.declareObjectPublic()

##     def __bobo_traverse__(self,request,entry_name=None):
##         if entry_name in self.objectIds('UserInfo'):
##             return getattr(self.UserInfo,entry_name)
##         return getattr(self,entry_name)

    # No additional comments.
    def __init__(self, id, title):
        """Construct FLE User Manager."""
        self.id = id
        self.title = title

        self.pending_users = PersistentMapping()
        self.groups = {}

        self.__images = {}

        for tup in self.dtml_files:
            add_dtml(self, tup)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """Set default permissions for roles."""
        from common import roles_admin, roles_staff, roles_user

        self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_staff, 0)
        self.manage_permission(perm_view, roles_staff, 0)

        getattr(self, 'fle_form_header').manage_permission(
            perm_view,
            ['Authenticated', 'Anonymous',], 1)


    security.declarePrivate('add_group')
    def add_group(self, name):
        """Add a new group."""

        # We would not need 'g'; I put it here only in order to avoid
        # confusion between strings and numbers...
        try:
            key = 'g' + str(max([int(x[1:]) for x in self.groups.keys()]) + 1)
        except ValueError:
            key = 'g1' # no groups yet

        self.groups[key] = name
        self._p_changed = 1

    # No additional comments.
    security.declarePrivate('remove_group')
    def remove_group(self, group_id):
        """Remove a group."""
        if group_id in self.groups.keys():
            del self.groups[group_id]
            self._p_changed = 1

    # No additional comments.
    security.declarePrivate('get_groups')
    def get_group_ids_and_names(self):
        """Get list of groups."""
        return self.groups.items()


    security.declareProtected(perm_view, 'get_users_outside_any_group')
    def get_users_outside_any_group(self):
        """Return a list of UserInfo objects, where nobody belongs to any
        group."""
        return filter(lambda user: not len(user.get_groups()),
                      self.get_active_users())

    def add_group_with_existing_id(self, group_id, group_name):
        """..."""
        self.groups[group_id] = group_name
        self._p_changed = 1

    security.declarePublic('has_user_global_role')
    def has_user_global_role(self, uname, role):
        """Has given user given role."""
        return role in get_roles(self.parent(),uname)

    security.declarePublic('is_power_user')
    def is_power_user(self, uname):
        """Is user a power user?"""

        if not type(uname) is types.StringType:
            # Try to convert uname to string (it is a REQUEST.AUTHENTICATED_USER)
            uname = str(uname)
        if not self.acl_users.getUser(uname):
            return 0
        return getattr(self.fle_users,uname).has_any_role(('FLEAdmin', 'Manager', 'Staff'))

    security.declarePublic('lang_from_auth')
    def lang_from_auth(self, auth):
        """Get language for pending user that has given auth string."""
        for key in self.pending_users.keys():
            if self.pending_users[key][0] == auth:
                return self.pending_users[key][2]

        return 'en'

    # --> this method can be accessed by anyone.
    # --> Be careful to check that only valid invited
    #     users can use this (and only once!) --jmp
    security.declarePublic('add_invited_user')
    def add_invited_user(
        self,
        uname,
        password1,
        password2,
        first_name,
        last_name,
        email,
        auth,
        REQUEST):
        """Add invited user (and remove her from pending users).
        This method is called when an invited user applies the URL
        he/she received in the invitation email."""
        auth_strings = []

        for e in self.pending_users.values():
            auth_strings.append(e[0])

        if auth not in auth_strings:
            return 'Permission denied.' + auth + '-' + str(auth_strings)

        errors = []

        self.get_lang_given(('common', 'usermgmnt'), REQUEST,
                            self.lang_from_auth(auth))

        # Mandatory
        for x,y in (('uname', 'uname'), ('password1', 'password'),
                    ('password2', 'Confirm')):
            if not is_valid_id(eval(x)):
                errors.append(REQUEST['L_' + y])

        for x in ('first_name', 'last_name'):
            if not is_valid_title(eval(x)):
                errors.append(REQUEST['L_' + x])

        # Optional
        if email and not is_valid_title(email):
            errors.append(REQUEST['L_email'])

        if len(errors) > 0:
            return self.message_dialog_error(
                self, REQUEST,
                title=REQUEST['L_invalid_input'],
                message=REQUEST['L_invalid_fields'] + ": '" + \
                "' , '".join(errors) + "'",
                action=apply(
                make_action,
                ['register_user_form'] +
                [(x, eval(x)) for x in
                 ('uname', 'first_name', 'last_name', 'email', 'auth')]))

        if password1 != password2:
            return self.message_dialog_error(
                self, REQUEST,
                title=REQUEST['L_error'],
                message=REQUEST['L_password_mismatch'],
                action=apply(
                make_action,
                ['register_user_form'] +
                [(x, eval(x)) for x in
                 ('uname', 'first_name', 'last_name', 'email', 'auth')]))

        # Remove user from the pending users.
        for key in self.pending_users.keys():
            if self.pending_users[key][0] == auth:
                language = self.pending_users[key][2]
                course_ids = self.pending_users[key][4]
                self.remove_pending_user(key)
                break

        user = self.add_user(uname=uname,
                             password=password1,
                             roles=('User',))
        user.set_first_name(first_name)
        user.set_last_name(last_name)
        user.set_email(email)
        user.set_language(language)

        # Add user to course(s).
        for course_id in course_ids:
            course = self.courses.get_child(course_id)
            course.set_roles(uname, ('Student',))
            if course.has_group_folder():
                course.make_group_folder_proxies((self.get_user_info(uname),))

        if REQUEST:
            REQUEST.RESPONSE.redirect(self.state_href(
                REQUEST, uname+'/edit_user_form'))

    security.declarePrivate('is_nickname_free')
    def is_nickname_free(self, nickname):
        """Checks that given nick name is not already take by somebody
        else. Note that case doesn't matter: if somebody is 'foo'
        nobody can take 'Foo'."""
        return nickname.lower() not in \
               [o.get_nickname().lower() for o in self.get_users()]

    security.declarePrivate('is_uname_free')
    def is_uname_free(self, uname):
        """Checks that given uname is not already take by somebody
        else. Note that case doesn't matter: if somebody is 'foo'
        nobody can take 'Foo'."""
        # Check that same uname isn't already used.
        if uname.lower() in \
               [o.lower() for o in self.acl_users.getUserNames()]:
            return 0
        # Check that no one has an identical nickname.
        return self.is_nickname_free(uname)

    # Called from coursemanager's course_selection.dtml
    security.declarePublic('is_valid_uname')
    def is_valid_uname(self, uname):
        """Public valid uname checking. Checks if the given user name
        exists."""
        return uname in self.acl_users.getUserNames()


    security.declareProtected(perm_edit, 'empty_pwd')
    def empty_pwd(self):
        """Return default empty password. Note, user can't use
        this password."""
        return 'eightchr'

    # Has to be public because ui/UserInfo/edit_user_form uses this.
    security.declarePublic('get_default_webtop_bgs')
    def get_default_webtop_bgs(self):
        """Return a list of default Image objects."""

        from common import bg_stuff

        names = bg_stuff.keys()
        names.sort()
        return [eval('self.images.%s' % x) for x in names]

    security.declareProtected(perm_view, 'get_tmp_image')
    def get_tmp_image(self, REQUEST, image_key):
        """Return temporary object specified by key."""
        t = self.__images[image_key]
        REQUEST.RESPONSE.setHeader('Content-Type', t[1])
        return t[0]

    def __add_tmp_image(self, image, content_type):
        try:
            key = str(max(map(int, self.__images.keys())) + 1)
        except ValueError:
            key = '1'
        self.__images[key] = (image, content_type)
        self._p_changed = 1
        return key

    def __remove_tmp_image(self, key):
        retval = self.__images[key]
        del self.__images[key]
        self._p_changed = 1
        return retval

    security.declareProtected(perm_edit, 'add_user_form_handler')
    def add_user_form_handler(
        self,
        REQUEST=None,

        # actual user info data from forms
        uname = None,
        pwd = '',               # password
        pwd_confirm = '',       # password confirmation
        first_name = None,
        last_name = None,
        email = None,
        organization = None,
        language = None,
        role = None,
        photo_upload = None,
        photo_url = None,
        # group = None,
        address1 = None,
        address2 = None,
        city = None,
        country = None,
        homepage = None,
        phone = None,
        gsm = None,
        quote = None,
        background = None,
        personal_interests = None,
        professional_interests = None,
        webtop_bg_upload=None,
        default_webtop_bg=None,

        photo_key="",
        webtop_bg_key="",

        cancel = '', # submit buttons
        commit = '', #
        ):
        """Handles user creation in UserManager context.
        See UserInfo.edit_user_form_handler for user editing."""

        if cancel:
            if REQUEST:
                REQUEST.RESPONSE.redirect(
                    self.state_href(REQUEST, 'index_html'))
            return

        other_errors = 0
        errors = []
        self.get_lang(('common', 'usermgmnt'), REQUEST)

        for s in ('first_name', 'last_name', 'email', 'organization',
                  'photo_url', 'address1', 'address2', 'city', 'homepage',
                  'phone', 'gsm'):
            e = REQUEST.get(s)
            if e:
                e = e.strip()
                REQUEST.set(s, e)

        # Mandatory
        for x in ('uname', 'first_name', 'last_name'):
            e = REQUEST.get(x)
            if not e or not is_valid_title(e):
                errors.append(REQUEST['L_' + x])

        if not pwd:
            errors.append(REQUEST['L_password'])

        if not pwd_confirm:
            errors.append(REQUEST['L_Confirm'])

        # Optional
        for x in ('email', 'organization', 'language', 'address1',
                  'address2', 'city', 'phone', 'gsm'):
            e = REQUEST.get(x)
            if e and not is_valid_title(e):
                errors.append(REQUEST['L_' + x])

        # These are optional, too.
        if photo_url and not is_valid_url(photo_url):
            errors.append(REQUEST['L_url_to_photo'])
        if homepage and not is_valid_url(homepage):
            homepage='http://'+homepage
        if homepage and not is_valid_url(homepage):
            errors.append(REQUEST['L_homepage'])

        for x in ('quote', 'background', 'personal_interests',
                  'professional_interests'):
            value = REQUEST.get(x)
            if value and ('<' in value or '>' in value):
                errors.append(REQUEST['L_' + x])

        message = '' # empty when no errors in input
        if not self.is_uname_free(uname) or not is_valid_uname(uname):
            title = REQUEST['L_invalid_input']
            # FIXME: Replace this generic error message
            # FIXME: (Requires new keyword for translation file...)
            errors.append(REQUEST['L_uname'])
            message = REQUEST['L_invalid_fields'] + ": '" + \
                      "' , '".join(errors) + "'"
        elif pwd != pwd_confirm:
            title = REQUEST['L_error']
            message = REQUEST['L_password_mismatch']
        elif len(errors) > 0:
            title = REQUEST['L_invalid_input']
            message = REQUEST['L_invalid_fields'] + ": '" + \
                      "' , '".join(errors) + "'"

        if message: # error(s): return a message dialog

            # We can't save photo data to URL.
            if photo_upload and len(photo_upload.filename) > 0:
                photo_key = self.__add_tmp_image(
                    photo_upload.read(),
                    photo_upload.headers['content-type'])
                photo_url = '' # photo_upload overrides photo_url
            else:
                if photo_url and is_valid_url(photo_url) and photo_key:
                    self.__remove_tmp_photo(photo_key)
                    photo_key = ''

            # We can't save custom webtop background image data to URL.
            if webtop_bg_upload and len(webtop_bg_upload.filename) > 0:
                webtop_bg_key = self.__add_tmp_image(
                    webtop_bg_upload.read(),
                    webtop_bg_upload.headers['content-type'])
                 # webtop_bg_upload overrides default_webtop_bg
                default_webtop_bg = ''
            else:
                if default_webtop_bg and webtop_bg_key:
                    self.__remove_tmp_image(webtop_bg_key)
                    webtop_bg_key = ''

            action = apply(
                make_action,
                ['edit_user_form?new=1'] +
                [(x, eval(x)) for x in
                 ('uname',
                  'first_name', 'last_name', 'email', 'homepage',
                  'organization', 'language', 'role',
                  'photo_url', 'address1', 'address2', 'city',
                  'country', 'phone', 'gsm',
                  'quote', 'background', 'personal_interests',
                  'professional_interests', 'default_webtop_bg',
                  'photo_key', 'webtop_bg_key')])

            return self.message_dialog(
                self, REQUEST,
                title=title,
                message=message,
                action=action)

        # This is ugly: we have to make some extra checks because:
        #  * Users with role 'Staff' can create only 'User' can 'Staff' users.
        #  * Users with role 'FLEAdmin' can create any kind of users.
        logged_user = self.get_current_user(REQUEST)
        if role == 'User':
            roles = ('User',)
        elif role == 'Staff':
            # This check is not really needed as this method
            # is already protected so that we know that logged
            # user is at least 'Staff', but let's be paranoid...
            if self.has_user_global_role(logged_user, 'Staff') or \
               self.has_user_global_role(logged_user, 'FLEAdmin'):
                roles = ('User', 'Staff')
            else:
                raise 'FLE Error', \
                      'Only Staff or FLEadmin can' + \
                      'create new users with role Staff'
        elif role == 'FLEAdmin':
            if self.has_user_global_role(logged_user, 'FLEAdmin'):
                roles = ('User', 'FLEAdmin')
            else:
                raise 'FLE Error', \
                      'Only FLEadmin can create new users with role FLEAdmin'
        else:
            raise 'FLE Error', 'Unknown role'

        # Set mandatory paramaters
        uo = self.add_user(uname, pwd, roles)
        uo.set_first_name(first_name)
        uo.set_last_name(last_name)

        # Set photo
        if photo_key:
            photo_tuple = self.__remove_tmp_image(photo_key)
            uo.set_photo(photo_tuple[0], photo_tuple[1])
        if photo_upload and len(photo_upload.filename) > 0:
            uo.set_photo(photo_upload.read(),
                         photo_upload.headers['content-type'])
        elif photo_url and photo_url != 'http://':
            photo_data = get_url(photo_url)
            self.set_photo(photo_data)

        # Set webtop background
        if webtop_bg_key:
            uo.webtop.set_webtop_bg_from_image_data(
                self.__remove_tmp_image(webtop_bg_key)[0])
        if webtop_bg_upload and len(webtop_bg_upload.filename) > 0:
            uo.webtop.set_webtop_bg_from_image_data(webtop_bg_upload.read())
        elif default_webtop_bg:
            uo.webtop.set_webtop_bg_from_default_image(default_webtop_bg)

        # Set remaining parameters.
        for p in ('email', 'organization', 'language', 'address1',
                  'address2', 'city', 'homepage', 'phone', 'gsm',
                  'quote', 'background', 'personal_interests',
                  'professional_interests'):
            if eval(p):
                exec('uo.set_%s(%s)' % (p, p))

        if REQUEST:
            REQUEST.RESPONSE.redirect(
                self.state_href(REQUEST, '%s/show_user_info' % uname))


    # If user with given uname does not exist an exception is raised.
    security.declareProtected(perm_edit, 'freeze_user')
    def freeze_user(self, uname):
        """Freeze user."""
        user = self._getOb(uname)
        if user.is_frozen():
            # User already frozen: do nothing.
            return

        # Staff and fleadmins aren't frozen
        if user.has_any_role(('FLEAdmin','Staff')):
            raise 'FLE Error','User %s is Staff or FLEAdmin!' % uname
        user.freeze_me()

    # If user with given uname does not exist an exception is raised.
    security.declareProtected(perm_edit, 'unfreeze_user')
    def unfreeze_user(self, uname):
        """Unfreeze user."""
        acl_user_obj = self.acl_users.getUser(uname)
        user = self._getOb(uname)

        if user.is_frozen(): user.unfreeze_me()

    security.declarePrivate('add_user')
    # uname: User account name
    #
    # password: The password
    #
    # roles: List of (FLE-wide) roles the user should have
    #
    # domains: List of domains from which the user is allowed to login.
    def add_user(self, uname, password, roles, domains=()):
        """Add user to UserManager."""

        # If the user has no roles and no password, we'll just skip.
        if not password and not roles:
            return
        if uname in self.acl_users.getUserNames():
            raise 'FLE Error', "Trying to add user that already exists in acl_users! (%s)" % (uname)
        try:
            self.acl_users._doAddUser(uname, password, [], list(domains))
        except:
            import sys
            if sys.exc_type=='NotImplemented':
                raise Errors.FleError("The user folder is implemented partially and does not support adding users.")
            raise
        try:
            user = self.add_user_fle(uname,roles)
        except:
            # In case of exception, get rid of user in acl_users.
            try:
                self.acl_users._doDelUsers((uname,))
                raise Errors.FleError("The supplied username %s could not be used. Check the user account information and try again." % uname)
            except KeyError:
                pass
            except:
                import sys
                if sys.exc_type=='NotImplemented':
                    raise Errors.FleError("The user folder is implemented partially and does not support removing users. There was a problem creating the user and now a partially functional user account remains.")
                raise
            # Finally raise an error!
            raise

        self.uncache_sorting_grouping()
        return user

    def add_user_fle(self, uname, roles):
        user = UserInfo(uname)
        self._setObject(uname, user)

        # A clever loop to get to the actual acl_user folder which contains
        # the authenticated user (because it might not be the closest one!)
        obj=self
        while 1:
            acl_user_obj = obj.acl_users.getUser(uname)
            if acl_user_obj:
                acl_user_obj=acl_user_obj.__of__(obj.acl_users)
                break
            obj=obj.aq_parent
        # Get the user object from acl_users, and set it as the
        # owner of the newly created UserInfo object.
        user.changeOwnership(acl_user_obj)

        # Set the userthingy as a owner (local role) to the
        # newly created UserInfo object.
        user.manage_delLocalRoles(user.get_valid_userids())
        user.manage_setLocalRoles(uname, ('Owner',))
        # Set the user's FLE-global roles to the FLE root object.
        self.parent().manage_setLocalRoles(uname,roles)
        return user

    def _create_a_random_string(self):
        """Create a random string (used to authenticate invited users)."""
        from common import random, a_char
        import sha

        secret = ''
        m = sha.new()
        for i in range(5):
            secret = secret + str(random())
            m.update(secret)
            hash = m.digest()
            secret = ''
        for i in hash:
            secret = secret + a_char(ord(i))
        return secret


    # This uses FLE/MailHost object
    # Invited users are stored in self.pending_users which
    # is a dictionary containing secret key, invitation
    # message and language: {'email':(secret, message, language, URL1), ...}
    # Invitation message, language and URL1 are stored for possible
    # re-invitation.
    #
    # Parameters:
    #
    # emails: list of e-mail addresses
    #
    # message: message to be sent via email
    security.declareProtected(perm_edit, 'invite_user')
    def invite_user(self, REQUEST, emails, message, language, course_ids=[]):
        """Invite user by email."""
        import urllib

        self.get_lang(('common','usermgmnt'),REQUEST)
        # This is for calling method from test code
        URL1 = REQUEST.URL1

        if type(course_ids) == types.StringType:
            course_ids = (course_ids,)

        # Figure out who is sending this email.
        user_name = str(REQUEST.AUTHENTICATED_USER)
        send_address = self.get_user_info(user_name).get_email()
        if not send_address:
            # If the user wanting to invite people has no email address,
            # then she must set one, before she can send invitation messages.
            return self.message_dialog_error(
                self, REQUEST,
                title=REQUEST['L_no_email'],
                message=REQUEST['L_no_email_explanation'],
                action = apply(
                make_action,
                ['invite_user_form'] +
                [(x, eval(x)) for x in ('emails', 'message', 'language')] +
                [('course_ids', str(course_ids))]
                ))

        errors = []
        self.get_lang(('common', 'usermgmnt'), REQUEST)
        if not emails: # FIXME: input_checks: something more fancy?
            return self.message_dialog_error(
                self, REQUEST,
                title=REQUEST['L_invalid_input'],
                message=REQUEST['L_invalid_fields'] + ": '" + \
                REQUEST['L_email_addresses'] +"'",
                action = apply(
                make_action,
                ['invite_user_form'] +
                [(x, eval(x)) for x in ('emails', 'message', 'language')] +
                [('course_ids', str(course_ids))]
                ))

        # Check if user has hacked input.
        uinfo = self.fle_users.get_user_info(user_name)
        course_ids_of_user = [x.get_id() for x in uinfo.user_courses()]
        if not uinfo.has_role('FLEAdmin'):
            for course_id in course_ids:
                if course_id not in course_ids_of_user:
                    raise 'FLE Error', 'Hey you! You are not on that course!'

        # FIXME: input_checks: should message be checked?

        emails = string.replace(emails, ",", " ")
        emails = string.split(emails)
        emails_ok = []
        emails_error = []

        from smtplib import SMTPRecipientsRefused, SMTPException

        for email in emails:

            # Create a random string (used to authenticate invited users)
            secret = self._create_a_random_string()

            try:
                self.__send_invitation(str(email),send_address,message,secret,language,URL1,course_ids)
            except SMTPRecipientsRefused:
                emails_error.append(str(email))
            except SMTPException, ex:
                return self.message_dialog_error(self, REQUEST,
                    title=REQUEST['L_error'],
                    message=REQUEST['L_could_not_send_invitation']+"\n"+ex.smtp_error,
                    action="index_html")
            except AttributeError:
                return self.message_dialog_error(self, REQUEST,
                    title=REQUEST['L_error'],
                    message=REQUEST['L_could_not_send_invitation'],
                    action="index_html")
            else:
                emails_ok.append(str(email))
                # invitation message is needed for re-invitation
                self.pending_users[email] = (secret, message, language, URL1,
                                         course_ids)
                self._p_changed = 1

        if emails_error:
            msg=REQUEST['L_invitations_sent_to'] % ", ".join(emails_ok)
            msg2=REQUEST['L_invitations_not_sent_to'] % ", ".join(emails_error)
            return self.message_dialog_error(
                self, REQUEST,
                title=REQUEST['L_invitations_sent'] + " (" + REQUEST['L_error']+")",
                message=msg + " " + msg2,
                action="index_html")
        else:
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_invitations_sent'],
                message=REQUEST['L_invitations_sent_to'] % ", ".join(emails_ok),
                action='index_html')

    # An exception is raised if email is invalid.
    # FIXME: re-invitation needs invitation message to be stored
    # This uses FLE/MailHost object
    security.declareProtected(perm_edit, 're_invite_user')
    def re_invite_user(self, email, send_address):
        """Re-invite user by email."""

        secret, message, language, URL1, course_ids = self.pending_users[email]
        self.__send_invitation(email,send_address,message,secret,language,URL1,course_ids)

    def __send_invitation(self,to_address,from_address,message,secret,language,baseurl,course_ids):

        # encode secret authentication key for
        # transfering it in an url
        #
        import urllib
        secret_encoded = urllib.quote(secret)
        mailhost = self.MailHost
        to_encoded = urllib.quote(to_address)

        url = '%s/register_user?email=%s&auth=%s' % \
              (baseurl, to_encoded, secret_encoded)

        inv_lang_dict = {}
        self.get_lang_given(('common', 'usermgmnt'),
                            inv_lang_dict, language)

        msg = "Content-Type: text/plain; charset=UTF-8\n\n"+\
              inv_lang_dict['L_invitation_header']+'\n'+\
              message + '\n' + \
              inv_lang_dict['L_invitation_footer'] + url
        subject = inv_lang_dict['L_invitation_subject']
        subject = self.__encode_subject(subject)

        mailhost.send(msg,to_address,from_address,subject,encode="quoted-printable")

    def __encode_subject(self, subject):
        import mimetools
        import StringIO

        u_subject = unicode(subject, 'utf-8')
        lines = []
        line = ''
        length = 32
        for c in u_subject:
            line += c.encode('utf-8')
            if len(line) > length:
                lines.append(line)
                line = ''
                length = 40
        lines.append(line)

        retval = ''
        for line in lines:
            a = StringIO.StringIO(line)
            b = StringIO.StringIO()
            mimetools.encode(a, b, 'base64')
            b.seek(0)
            retval += '=?utf-8?b?' + b.read().strip() + '?=\r\n '
        retval = retval[:-3]

        return retval

    # This calls register_user_form.
    security.declarePublic('register_user')
    def register_user(self, email, auth, REQUEST):
        """Register a pending user (when invited user registers himself)."""
        import urllib

        self.get_lang(('common','usermgmnt'),REQUEST)

        if not email in self.pending_users.keys():
            return self.message_dialog_error(
                self, REQUEST,
                title=REQUEST['L_registration_failed'],
                message=REQUEST['L_invitation_key_used'],
                action="")

        # auth string must be decoded
        if self.pending_users[email][0] != urllib.unquote(auth):
            return self.message_dialog_error(
                self, REQUEST,
                title=REQUEST['L_registration_failed'],
                message=REQUEST['L_authorization_failed'],
                action="")

        REQUEST['email']=email
        REQUEST['auth']=auth
        return self.register_user_form(
            self, REQUEST)

    # FIXME: How to handle all the objects that the user owns and that have
    # links to user's information (like user's name or photo)?
    security.declareProtected(perm_manage, 'remove_user')
    def remove_user(self, uname):
        """Remove user."""
        if not uname in self.objectIds():
            raise 'FLE Error', 'Given user does not exist.'

        try:
            acl_users = self.acl_users
            acl_users._doDelUsers((uname,))
            self._delObject(uname)
            self.uncache_sorting_grouping()
        except:
            import sys
            if sys.exc_type=='NotImplemented':
                raise Errors.FleError("The user folder is implemented partially and does not support removing users.")
            raise

    # Country list lives in this method.
    security.declarePublic('get_countries')
    def get_countries(self):
        """Return list of all(?) countries in the world (in English)"""
        from countries import country_list
        return country_list

    security.declarePublic('get_user_info')
    def get_user_info(self, uname):
        """Return a the uname UserInfo object."""
        from types import StringType
        if not type(uname) is StringType:
            raise 'FLE Error', 'Argument uname is not string type! (and this is the wrong place to convert it).'

        # Get user info object from fle_users folder
        try:
            return self.get_child(uname)
        except AttributeError:
            raise Errors.FleError('No such FLE user: %s' % (uname))

    security.declareProtected(perm_manage, 'reload_dtml')
    def reload_dtml(self, REQUEST=None):
        """Reload dtml files from the file system."""
        reload_dtml(self, self.dtml_files)

        # This page needs to be viewable without authentication.
        getattr(self,'register_user_form').manage_permission(
            perm_view,
            ['Authenticated', 'Anonymous',], 1)

        if REQUEST:
            self.get_lang(('common','usermgmnt'),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_dtml_reloaded'],
                message=REQUEST['L_dtml_files_reloaded'],
                action='index_html')

    security.declareProtected(perm_manage, 'remove_users_confirm_handler')
    def remove_users_confirm_handler(
        self,
        REQUEST,
        user_string = '',
        remove = '',  # form submit buttons
        cancel = '',  #
        ):
        """Handle input from the remove_users_confirm.dtml"""
        if remove:
            self.get_lang(('common','usermgmnt'),REQUEST)
            success = []
            failure = []
            users = string.split(user_string)

            for user in users:
                try:
                    self.remove_user(user)
                    success.append(user)
                except:
                    failure.append(user)

            message=REQUEST['L_removed_users'] % success
            if failure:
                message += '<br>'+REQUEST['L_not_removed_users'] % failure

            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_users_removed'],
                message=message,
                action='index_html')

        elif cancel:
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))
            return
        else:
            raise 'FLE Error', 'Unknwon button' # Should never happen

    # No additional comments.
    security.declareProtected(perm_edit, 'form_handler')
    def form_handler(
        self,
        REQUEST,
        users = '',
        freeze = '',   # submit buttons
        unfreeze = '', #
        remove = '',   #
        ):
        """Handle input from the fle_users/index_html form."""
        if users == '':
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))
            return
        if type(users) is types.StringType:
            users = [users,]

        if freeze:
            for user in users:
                self.freeze_user(user)
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))
            return
        elif unfreeze:
            for user in users:
                self.unfreeze_user(user)
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))
            return
        elif remove:
            # FIXME: input checks?
            user_string = users[0]
            for user in users[1:]:
                user_string += "%20" + user
            REQUEST.RESPONSE.redirect(
                self.state_href(
                REQUEST,
                'remove_users_confirm?user_string=%s' % user_string))
            return
        else:
            # This code should never be reached.
            raise 'FLE Error', 'Unknown button'

    # No additional comments.
    security.declareProtected(perm_edit, 'remove_pending_user')
    def remove_pending_user(self, email):
        """Remove pending user."""
        try:
            del self.pending_users[email]
        except KeyError:
            pass
        self._p_changed = 1

    # No additional comments.
    security.declareProtected(perm_view, 'get_pending_users')
    def get_pending_users(self):
        """Get emails of pending users."""
        return self.pending_users.keys()

    security.declarePublic('get_users')
    def get_users(self):
        """Return a list of UserInfo objects (active and frozen)."""
        return self.get_children('UserInfo')

##     def foo_get_user_names(self):
##         """..."""
##         res=""
##         for user in self.get_users():
##             res = res+"%s,%s,%s\n" % (user.get_nickname(),user.get_first_name(),user.get_last_name())
##         return res

    security.declarePublic('get_active_users')
    def get_active_users(self):
        """Return a list of active (non-frozen) UserInfo objects."""
        actives = []
        for user in self.get_users():
            if not user.is_frozen(): actives.append(user)
        return actives

    security.declarePublic('get_active_users')
    def get_sorted_users(self, start_letter, stop_letter,
                         sort_criteria,userfilter='active'):
        """Return a list of UserInfo objects sorted by given criteria (whose
        first letter of sort criteria is between start_letter and stop_letter
        (including those))."""

        if not sort_criteria: sort_criteria = 'uname'

        start_letter = unichr(int(start_letter)).encode('utf-8')
        stop_letter = unichr(int(stop_letter)).encode('utf-8')

        def uname_comp(x,y):
            a = x.get_uname().lower()
            b = y.get_uname().lower()
            if a < b:     return -1
            elif  a == b: return  0
            else:         return  1

        def nickname_comp(x,y):
            a = x.get_nickname().lower()
            b = y.get_nickname().lower()
            if a < b:     return -1
            elif  a == b: return  0
            else:         return  1

        def first_name_comp(x,y):
            a = x.get_first_name().lower()
            b = y.get_first_name().lower()
            if a < b:     return -1
            elif  a == b: return  0
            else:         return  1

        def last_name_comp(x,y):
            a = x.get_last_name().lower()
            b = y.get_last_name().lower()
            if a < b:     return -1
            elif  a == b: return  0
            else:         return  1

        def first_char_in_lower(s):
            try:
                return unicode(s, 'utf-8')[0].lower().encode('utf-8')
            except IndexError:
                # s is empty -> return space
                return ' '

        sort_funcs = {'uname': uname_comp,
                      'nickname': nickname_comp,
                      'first_name': first_name_comp,
                      'last_name': last_name_comp}

        if userfilter=='all':
            retval = self.get_users()
        else:
            retval = self.get_active_users()
        retval.sort(sort_funcs[sort_criteria])
        if sort_criteria == 'uname':
            return filter(lambda
                          x, start = start_letter, stop = stop_letter,
                          fc = first_char_in_lower:
                          (fc(x.get_uname()) >= start and
                           fc(x.get_uname()) <= stop),
                          retval)
        elif sort_criteria == 'nickname':
            return filter(lambda
                          x, start = start_letter, stop = stop_letter,
                          fc = first_char_in_lower:
                          (fc(x.get_nickname()) >= start and
                           fc(x.get_nickname()) <= stop),
                          retval)
        elif sort_criteria == 'first_name':
            return filter(lambda
                          x, start = start_letter, stop = stop_letter,
                          fc = first_char_in_lower:
                          (fc(x.get_first_name()) >= start and
                           fc(x.get_first_name()) <= stop),
                          retval)
        elif sort_criteria == 'last_name':
            return filter(lambda
                          x, start = start_letter, stop = stop_letter,
                          fc = first_char_in_lower:
                          (fc(x.get_last_name()) >= start and
                           fc(x.get_last_name()) <= stop),
                          retval)
        else:
            raise 'FLE Error', 'How on earth we did not get exception before?'

    security.declareProtected(perm_edit, 'make_temp_user')
    def make_temp_user(self, uname):
        """Make temporary user from existing user."""
        return self.fle_root().temp_objects.add_object(
            self.get_child(uname))

    # FIXME: input_checks
    # No additional comments.
    security.declareProtected(perm_edit, 'pending_users_form_handler')
    def pending_users_form_handler(
        self,
        REQUEST,
        users = '',
        remove = '',    # submit buttons
        re_invite = '', #
        cancel = '',    #
        ):
        """Handle input from the fle_users/show_pending.dtml form."""
        self.get_lang(('common','usermgmnt'),REQUEST)
        if cancel:
            # go back to the user management index page
            REQUEST.RESPONSE.redirect(self.state_href(
                REQUEST, 'index_html'))
            return

        elif re_invite:
            user_name = str(REQUEST.AUTHENTICATED_USER)
            send_address = self.get_user_info(user_name).get_email()
            if not send_address:
                self.get_lang(('common', 'usermgmnt'), REQUEST)

                # FIXME: selected users are not passed back!!!
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_no_email'],
                    message=REQUEST['L_no_email_explanation'],
                    action='show_pending')


            # FIXME: check that invitation succeeds
            # Make sure that we use a list of strings!
            if type(users) is types.StringType:
                users = [users,]
            count = 0
            for user in users:
                try:
                    self.re_invite_user(user, send_address)
                    count += 1
                except:
                    pass

            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_re_invitations_sent'],
                message=REQUEST['L_re_invitations_sent_to'] % str(count),
                action='show_pending')

        elif remove:
            success = []
            failure = []

            # Make sure that we use a list of strings!
            if type(users) is types.StringType:
                users = [users,]

            for user in users:
                try:
                    self.remove_pending_user(user)
                    success.append(user)
                except:
                    failure.append(user)

            message = REQUEST['L_pending_removed_users'] % success
            if failure:
                message += '<br>'+ \
                           REQUEST['L_pending_not_removed_users'] % failure

            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_pending_users_removed'],
                message=message,
                action='show_pending')

        else:
            # This code should never be reached.
            raise 'FLE Error', 'Unknown button'


    def group_management_form_handler(
        self,
        REQUEST,
        name=None,
        add=None,
        update=None,
        ):
        """Handle input from the ui/UserManagager/group_mnanagement_form.dtml
        form."""
        if add:
            self.add_group(name)
        elif update:
            add_list = REQUEST.form.keys()
            for u in self.get_users():
                for g_id in [g[0] for g in self.get_group_ids_and_names()]:

                    if g_id + '_' + u.get_uname() in add_list:
                        u.add_to_group(g_id)
                    else:
                        u.remove_from_group(g_id)

        else:
            # This code should never be reached.
            raise 'FLE Error', 'Unknown button'

        REQUEST.RESPONSE.redirect(self.state_href(
            REQUEST, 'group_management_form'))


    security.declareProtected(perm_manage, 'cleanup_webtops')
    def cleanup_webtops(self):
        """Sets webtop items' owners to be the webtop owners.
        and remove unwanted GroupFolderProxy objects"""

        course_ids = [c.get_id() for c in self.courses.get_courses()]
        for user in self.get_users():
            print "Cleaning for user %s..." % user.get_uname()
            self.set_owner_of_webtop(user.webtop,user.get_uname())

            # Older versions of Fle3 did not remove GroupFolderProxy
            # objects from trashcans in webtops when a course was deleted.
            # So we have to clean up things here:
            user.get_webtop().recursive_cleanup_for_group_folder_proxies(
                course_ids)


    def set_owner_of_webtop(self,folder,uname):
        for item in folder.objectValues(('WebtopFolder','WebtopFile','WebtopLink','WebtopMemo')):
            print "Cleaning %s" % item.get_id()
            item.set_author(uname)
            if item.meta_type=='WebtopFolder':
                self.set_owner_of_webtop(item,uname)


    security.declarePrivate('uncache_sorting_grouping')
    def uncache_sorting_grouping(self):
        if hasattr(self,
                   '_' + self.__class__.__name__+ '__cached_sorting_grouping'):
            del self.__cached_sorting_grouping

    security.declareProtected(perm_view, 'get_sorting_grouping')
    def get_sorting_grouping(self, n_max_users_per_group, sort_criteria, userfilter='active'):
        """Return something like:
        [('a','g'), ('h','m'), ('n','s'), ('t','z')]"""

        # If we are lucky, the value is already cached.
        try:
            n = n_max_users_per_group
            # Cache by combined sorting criteria and user filter
            return self.__cached_sorting_grouping[n][sort_criteria+userfilter]
        except:
            pass

        if type(n_max_users_per_group) == types.StringType:
            n_max_users_per_group = int(n_max_users_per_group)
        if not sort_criteria: sort_criteria = 'uname'

        if userfilter=='all':
            method='get_users'
        else:
            method='get_active_users'
        code = "[u.%s() for u in self."+method+"()]"

        lower_names = eval(code %
                           {'uname': 'get_uname',
                            'nickname': 'get_nickname',
                            'first_name': 'get_first_name',
                            'last_name':  'get_last_name'}[sort_criteria])
        lower_names.sort()
        lower_names = [unicode(x, 'utf-8') for x in lower_names]
        lower_names = [x.lower() for x in lower_names]

        for i in range(len(lower_names)):
            if lower_names[i] == '': lower_names[i] = ' '

        min_letter = 65535
        max_letter = 0
        for c in [x[0] for x in lower_names]:
            if ord(c) < min_letter:
                min_letter = ord(c)
            if ord(c) > max_letter:
                max_letter = ord(c)

        letters=u''.join([unichr(i) for i in range(min_letter, max_letter+1)])

        retval = []
        t_start_index= 0
        n = 0
        for i in range(0, len(letters)):
            n += len(filter(lambda x, c=letters[i]: x[0] == c, lower_names))
            #    number of names starting with current letter

            if (n == n_max_users_per_group) or \
               ((n > n_max_users_per_group) and (t_start_index == i)):
                retval.append((letters[t_start_index], letters[i]))
                t_start_index = i + 1
                n = 0
            elif n > n_max_users_per_group:
                retval.append((letters[t_start_index], letters[i-1]))
                t_start_index = i
                n = len(
                    filter(lambda x, c=letters[i]: x[0] == c, lower_names))
            elif i == len(letters)-1:
                # We have to create/close the last group even if it
                # is not full yet
                if n > 0:
                    retval.append((letters[t_start_index], letters[i]))
                else:
                    retval[-1] = (retval[-1][0], letters[-1])

        for i in range(0, len(retval)):
            retval[i] = (str(ord(retval[i][0])), str(ord(retval[i][1])))

        # Cache retval (Note, we suppose that n_max_users_per_group is
        # constant, otherwise caching is not efficient.)
        n = n_max_users_per_group
        if (hasattr(self, '__cached_sorting_grouping')) and \
           (n in self.__cached_sorting_grouping.keys()):
            if self.__cached_sorting_grouping[n].keys():
                self.__cached_sorting_grouping[n][sort_criteria+userfilter] = retval
            else:
                self.__cached_sorting_grouping[n] = {(sort_criteria+userfilter) : retval}
        else:
            self.__cached_sorting_grouping = {n: {(sort_criteria+userfilter): retval}}

        self._p_changed = 1

        return retval


Globals.InitializeClass(UserManager)
# EOF
