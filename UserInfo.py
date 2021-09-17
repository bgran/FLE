# $Id: UserInfo.py,v 1.161 2003/11/13 12:44:50 tarmo Exp $
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

"""Contains class UserInfo, which contains the FLE specific details
of registered users."""

__version__ = "$Revision: 1.161 $"[11:-2]

import time, string, types
import os.path

try:
    from PIL import Image
    PIL_imported = 1
except ImportError:
    PIL_imported = 0
import cStringIO

import Globals
import OFS
from Globals import Persistent, Acquisition
import AccessControl
from AccessControl import ClassSecurityInfo
from IUserInfo import IUserInfo
import TraversableWrapper
from Cruft import Cruft
from Webtop import Webtop
from CourseManager import IDManager
from common import add_dtml_obj, reload_dtml, add_dtml, get_url, styles_path, \
     image_file_path, add_image_obj, make_action, get_roles, get_local_roles, \
     bg_stuff
#from common import user_timeout_delay
#from TempObjectManager import TempObjectManager
from input_checks import render, is_valid_title, is_valid_url, normal_entry_tags
from common import perm_view, perm_edit, perm_manage, perm_add_lo
from XmlRpcApi import UserInfoXMLRPC
from Globals import PersistentMapping
from MaptoolInterface import MaptoolInterface

# An instance of this class holds all user specific information
# with the exception of access control, which is handled by the
# standard Zope objects in acl_users. Fle3 no longer has global
# roles, but rather local roles attached to the FLE root object.
#
# Some acl information is handled here (like password changing),
# but those functions transfer to Zope internals as fast as possible.
class UserInfo(
    OFS.Folder.Folder,
    Persistent,
    TraversableWrapper.TraversableWrapper,
    Cruft,
    AccessControl.Role.RoleManager,
    OFS.SimpleItem.Item,
    IDManager,
    UserInfoXMLRPC,
    MaptoolInterface,
    ):
    """FLE user information."""
    meta_type = 'UserInfo'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    __implements__ = IUserInfo

    dtml_files = (
        )

##     def __bobo_traverse__(self,request,entry_name=None):
##         if entry_name=='webtop':
##             print "WEBTOP BOBO!"
##             return getattr(self.aq_inner.ui.Webtop,entry_name)
##         return getattr(self,entry_name)

    def __init__(self, id_):
        """Construct UserInfo object."""
        self.id = id_
        #self.title = title
        self.title = ''
        self.uname = id_
        self.__last_active = {}
        self.__frozen = 0

        self.__edit_tbl = PersistentMapping()

        IDManager.__init__(self)

        # Set permissions:
        # We iterate first over all set_* methods in this class, and protect them
        # with the Edit permission (see manage_afterAdd), and then we set the
        # View permissions for all get_* methods.
        for prefix in ['set_', 'get_']:
            for func in filter(lambda x,p=prefix:x[:len(p)] == p, dir(self)):
                if prefix == 'set_':
                    UserInfo.security.declareProtected('Edit', func)
                elif prefix == 'get_':
                    UserInfo.security.declareProtected('View', func)

        #self.set_first_name(first_name)
        #self.set_last_name(last_name)
        #self.set_email(email)
        #self.set_language(language)
        ## NOTE: Wrong. Stuff like this should have their own container classes.
        #self.set_photo(photo) # This is picture binary data
        self.__group_id_list = []
        self.set_address1('')
        self.set_address2('')
        self.set_city('')
        self.set_country('')
        self.set_homepage('')
        self.set_phone('')
        self.set_gsm('')
        self.set_quote('')
        self.set_background('')
        self.set_personal_interests('')
        self.set_professional_interests('')
        self.set_language('en') # Dirty hack ..
        self.set_organization('')

        for tup in self.dtml_files:
            add_dtml(self, tup)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """Set default permissions for roles."""

        wt = Webtop().__of__(self)
        self._setObject('webtop', wt)

        for obj in (self, self.get_child('webtop')):
            obj.manage_delLocalRoles([t[0] for t in obj.get_local_roles()])
            obj.changeOwnership(self.acl_users.getUser(
                self.get_uname()).__of__(self.acl_users))
            obj.manage_setLocalRoles(self.get_uname(), ('Owner',))

        self.manage_addFolder('own_styles')
        f = open(os.path.join(styles_path, 'personal_style_sheet.dtml'))
        code = f.read()
        f.close()

        code = code.replace('own_styles',
                            'fle_users/' + self.get_uname() + '/own_styles',
                            1)

        self.own_styles.manage_addFile(
            id='my_style_sheet',
            file=code,
            title='',
            content_type='text/css')

        self.set_webtop_bg_from_default_image('bgcolor_rd')

        from common import roles_admin, roles_staff, roles_user

        self.manage_permission(perm_manage, roles_admin, 0)
        self.manage_permission(perm_edit, roles_staff+('Owner',), 0)
        self.manage_permission(perm_view, roles_user, 0)

    security.declareProtected(perm_manage, 'reload_dtml')
    def reload_dtml(self, REQUEST=None):
        """Reload dtml files from the file system."""
        reload_dtml(self, self.dtml_files)

        if REQUEST:
            self.get_lang(('common',),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_dtml_reloaded'],
                message=REQUEST['L_dtml_files_reloaded'],
                action='index_html')

    # Each person has two personal stylesheets:
    #  -  my_style_sheet modifies webtop background
    #  -  my_style_sheet_tab modifies webtop tab background
    security.declarePrivate('modify_style_sheet')
    def modify_stylesheet(self, colour, image_path):
        """Modify personal stylesheets to use given colour
        and background image."""

        f = open(os.path.join(styles_path, 'personal_style_sheet.dtml'))
        code = f.read()
        f.close()

        code = code.replace('XXXXXX', colour)
        code = code.replace('YYYYYY', image_path)

        try:
            self.own_styles._delObject('my_style_sheet')
            self.own_styles._delObject('my_style_sheet_tab')
        except:
            pass

        code = str(code) # for some reason, code is sometimes unicode
        self.own_styles.manage_addFile(
            id='my_style_sheet',
            file=code,
            title='',
            content_type='text/css')

        code = code.replace('.mainbg ', '.wtbg-tab ')
        code = code.replace('.main ', '.wt-tab ')
        self.own_styles.manage_addFile(
            id='my_style_sheet_tab',
            file=code,
            title='',
            content_type='text/css')

    security.declareProtected(perm_view, 'get_photo_tag')
    # Our (simple) version of the tag() method of Zope's Image class.
    def get_photo_tag(self, REQUEST, **args):
        """Return HTML img tag for user's photo."""
        if self.has_photo():
            url = self.find_URL_of_fle_root(REQUEST) + \
                  '/fle_users/' + self.uname + '/get_photo'
            extra_params = ''
            arg_keys_lower = map(string.lower, args.keys())

            if not 'alt' in arg_keys_lower:
                extra_params += ' alt=""'
            if not 'height' in arg_keys_lower:
                extra_params += ' height="32"'
            if not 'width' in arg_keys_lower:
                extra_params += ' width="32"'
            if not 'border' in arg_keys_lower:
                extra_params += ' border="0"'

            for key in args.keys():
                extra_params += ' %s="%s"' % (key, args[key])

            return '<img src="%s"%s />' % (url, extra_params)
        else:
            # User has no photo -> show default user image.

            # NOTE: At the moment default image is not 32x32... find
            # NOTE: out if there is any reason for that?
            args['width']='32'
            args['height']='32'
            return apply(self.fle_root().images.user.tag, [], args)

    security.declareProtected(perm_view, 'has_photo')
    def has_photo(self):
        """Return whether user has photo."""
        return not not self.get_photo()

    security.declareProtected(perm_view, 'get_webtop')
    def get_webtop(self):
        """Return the webtop of the user."""
        return self.get_child('webtop')

    security.declarePrivate('freeze_me')
    def freeze_me(self):
        """Freeze the user."""
        fle=self.parent().parent()
        uname=self.get_uname()
        self.__roles = get_local_roles(fle,self.get_uname())
        fle.manage_delLocalRoles((uname,))
        self.__frozen = 1
        self._p_changed = 1

    security.declarePrivate('unfreeze_me')
    def unfreeze_me(self):
        """Unfreeze the user."""
        fle=self.parent().parent()
        uname=self.get_uname()
        fle.manage_setLocalRoles(uname,self.__roles)
        del self.__roles
        self.__frozen = 0
        self._p_changed = 1

    security.declarePublic('is_frozen')
    def is_frozen(self):
        """Am I frozen?"""
        try:
            return self.__frozen
        except:
            return 0

    def getPassword(self):
        return self.acl_users.getUser(self.get_uname())._getPassword()

    def getFrozenPassword(self):
        return self.__password

    def getDomains(self):
        return self.acl_users.getUser(self.get_uname()).getDomains()

    def getFrozenDomains(self):
        return self.__domains

    # Get "global" roles, eg. the roles given for the FLE root object.
    def getRoles(self):
        return get_roles(self.parent().parent(),self.get_uname())

    def getFrozenRoles(self):
        return self.__roles

    # Get roles specified for just one object, and not acquired from above.
    def getRolesInObject(self,object):
        return get_local_roles(object,self.get_uname())

    security.declareProtected(perm_view, 'user_courses')
    def user_courses(self, REQUEST=None):
        """Return a list of the courses the user is on."""
        ac = []
        uname = self.get_uname()
        for course in self.fle_root().courses.get_courses():
            if uname in [u.get_uname() for u in course.get_all_users()]:
                ac.append(course)
        return ac

    security.declareProtected(perm_view, 'user_course_ids')
    def user_course_ids(self):
        """Return a list of ids of the courses the user is on."""
        return [c.get_id() for c in self.user_courses()]

    security.declareProtected(perm_view, 'get_thinking_types_on_user_courses')
    # Return something like:
    #  [ [[tts_id1, tts1_name], [[tt1_id, tt1_name], [tt2_id, tt2_name], ...]],
    #    [[tts_id2, tts2_name], [[tt1_id, tt1_name], [tt2_id, tt2_name], ...]],
    #    ...
    #  ]
    def get_thinking_types_on_user_courses(self):
        """..."""
        retval = []
        contexts = []
        for c in self.user_courses():
            contexts += c.get_course_contexts()
        for cc in contexts:
            if cc.get_thinking_type_set_id() not in [x[0][0] for x in retval]:
                tts = cc.get_thinking_type_set()
                retval.append( [[tts.get_id(), tts.get_name()],
                                [[tt.get_id(), tt.get_name()] for tt \
                                 in tts.get_thinking_types()]
                                ])
        return retval


    security.declarePrivate('set_state')
    def set_state(self, state):
        """Set state."""
        self.__state = state

    security.declarePrivate('get_state')
    def get_state(self):
        """Get state."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__state'):
            return ""
        else:
            return self.__state

    security.declarePrivate('set_nickname')
    def set_nickname(self, nickname):
        """Set nickname."""
        self.__nickname = nickname

    security.declareProtected(perm_view, 'has_nickname')
    def has_nickname(self):
        """Is the nick name set?"""
        if not hasattr(self, '_' + self.__class__.__name__+ '__nickname'):
            return 0
        return not not self.__nickname

    security.declareProtected(perm_view, 'may_edit_nickname')
    def may_edit_nickname(self,REQUEST):
        """Can user edit this user's nickname?"""
        if not self.has_nickname():
            return 1
        uname = str(REQUEST.AUTHENTICATED_USER)
        user = getattr(self.fle_users,uname)
        if user.has_any_role(('FLEAdmin','Staff')):
            return 1
        return 0

    security.declareProtected(perm_edit, 'set_first_name')
    def set_first_name(self, name):
        """Set first name."""
        self.__first_name = name

    security.declareProtected(perm_edit, 'set_last_name')
    def set_last_name(self, name):
        """Set last name."""
        self.__last_name = name

    security.declareProtected(perm_edit, 'set_email')
    def set_email(self, email):
        """Set email."""
        self.__email = email

    security.declareProtected(perm_edit, 'set_language')
    def set_language(self, language):
        """Set language."""
        self.__language = language

    security.declareProtected(perm_edit, 'set_photo')
    def set_photo(self, photo, content_type=None):
        """Set photo."""

        try:
            # Try to crop and scale image to 32x32 pixels and
            # convert it into JPEG format...
            if not PIL_imported:
                print "Can't scale user's photo. PIL not installed."
                raise ''

            s = cStringIO.StringIO(photo)
            im = Image.open(s)
            (width, height) = im.size

            if width == 32 and height == 32 and im.format == 'JPEG':
                # If the image is already 32x32 JPEG image, we want to
                # avoid doing JPEG compression again (lossy!)
                # This is important when exporting/importing FLE.
                raise ''

            if im.mode != 'RGB':
                im = im.convert('RGB')

            if width != height:
                smaller = min(width, height)
                bigger = max(width, height)

                if width == smaller:
                    # Tall image: save top part of the image
                    im = im.crop(( 0, 0, smaller, smaller))
                else:
                    # Wide image: save center part of the image
                    im = im.crop(( (width-height)/2, 0, smaller, smaller))

            im = im.resize((32,32), Image.BICUBIC)

            s = cStringIO.StringIO()
            im.save(s, "JPEG", quality=100)
            s.seek(0)
            self.__photo = s.read()
            self.__photo_type = 'image/jpeg'
        except:
            # ... or failing that just use the original image.
            # (The failure happens if the system has not PIL installed,
            #  or if the PIL can't read the image format, or if the PIL
            #  was compiled without JPEG support, or then something
            #  completely different...)
            self.__photo = photo
            self.__photo_type = content_type


    security.declarePrivate('get_groups')
    def get_groups(self):
        """Return a list ids of groups that the users belongs to."""
        return self.__group_id_list

    security.declareProtected(perm_view, 'belongs_to_group')
    def belongs_to_group(self, group_id):
        """Does the user belong to a group (given by group_id)?"""
        return group_id in self.__group_id_list

    security.declarePrivate('add_to_group')
    def add_to_group(self, group_id):
        """Add user to a group (given by group_id)."""
        if group_id not in self.__group_id_list:
            self.__group_id_list.append(group_id)
            self._p_changed = 1

    security.declarePrivate('remove_from_group')
    def remove_from_group(self, group_id):
        """Remove user from a group (given by group_id)."""
        if group_id in self.__group_id_list:
            self.__group_id_list.remove(group_id)
            self._p_changed = 1

    security.declareProtected(perm_edit, 'set_address1')
    def set_address1(self, address1):
        """Set address.1 (street address)"""
        self.__address1 = address1

    security.declareProtected(perm_edit, 'set_address2')
    def set_address2(self, address2):
        """Set address.2 (postal address)"""
        self.__address2 = address2

    security.declareProtected(perm_edit, 'set_city')
    def set_city(self, city):
        """Set city."""
        self.__city = city

    security.declareProtected(perm_edit, 'set_country')
    def set_country(self, country):
        """Set country."""
        self.__country = country

    security.declareProtected(perm_edit, 'set_homepage')
    def set_homepage(self, homepage):
        """Set homepage."""
        self.__homepage = homepage

    security.declareProtected(perm_edit, 'set_phone')
    def set_phone(self, phone):
        """Set phone."""
        self.__phone = phone

    security.declareProtected(perm_edit, 'set_gsm')
    def set_gsm(self, gsm):
        """Set gsm."""
        self.__gsm = gsm

    security.declareProtected(perm_view, 'get_webtop_bg_image_path')
    def get_webtop_bg_image_path(self):
        """Get webtop image path used in the style sheet."""
        if self.__webtop_bg_name in bg_stuff.keys():
            return 'images/'+ self.__webtop_bg_name
        else:
            return 'fle_users/' + self.get_uname() + \
                   '/own_styles/' + self.__webtop_bg_name

    security.declareProtected(perm_view, 'get_webtop_bg_colour_name')
    def get_webtop_bg_colour_name(self):
        """Get webtop background name."""
        if hasattr(self,
                   '_' + self.__class__.__name__+ '__webtop_bg_name'):
            if self.__webtop_bg_name in bg_stuff.keys():
                return bg_stuff[self.__webtop_bg_name][0]

        return 'rd'

    security.declareProtected(perm_view, 'get_webtop_bg_name')
    def get_webtop_bg_name(self):
        """Get webtop background name."""
        if not hasattr(self,
                       '_' + self.__class__.__name__+ '__webtop_bg_name'):
            return ""
        return self.__webtop_bg_name

    # FIXME:
    security.declareProtected(perm_view, 'get_bg_colour_name')
    def get_bg_colour_name(self):
        """..."""
        return self.get_webtop_bg_colour_name()

    security.declarePrivate('set_webtop_bg_from_image_data')
    def set_webtop_bg_from_image_data(self, image_data):
        """Set Webtop background image."""
        try: self.own_styles._delObject(self.__webtop_bg_name)
        except: pass

        # Change name every time, making it easier for web browser to detect
        # that the image has changed.
        name = 'own_bg' + self.generate_id()
        self.own_styles.manage_addImage(name, image_data,
                                        'Webtop background')
        self.__webtop_bg_name = name
        self.modify_stylesheet('cc3333', 'fle_users/' + self.get_uname() + \
                               '/own_styles/' + name)
        self.__using_custom_image = 1

    security.declarePrivate('set_webtop_bg_from_default_image')
    def set_webtop_bg_from_default_image(self, image_name):
        """Set Webtop background image."""
        try: self.own_styles._delObject(self.__webtop_bg_name)
        except: pass
        self.__webtop_bg_name = image_name
        self.modify_stylesheet(bg_stuff[image_name][1], 'images/' + image_name)
        self.__using_custom_image = 0

    security.declareProtected(perm_view, 'is_webtop_bg_using_custom_image')
    def is_webtop_bg_using_custom_image(self):
        """Has user uploaded some custom image to be used as a webtop
        background?"""
        try: return self.__using_custom_image
        except: return 0

    security.declareProtected(perm_edit, 'set_quote')
    def set_quote(self, quote):
        """Set quote."""
        self.__quote = quote

    security.declareProtected(perm_edit, 'set_background')
    def set_background(self, background):
        """Set background."""
        self.__background = background

    security.declareProtected(perm_edit, 'set_personal_interests')
    def set_personal_interests(self, p_i):
        """Set personal interests."""
        self.__personal_interests = p_i

    security.declareProtected(perm_edit, 'set_professional_interests')
    def set_professional_interests(self, p_i):
        """Set professional interests."""
        self.__professional_interests = p_i

    security.declareProtected(perm_edit, 'set_organization')
    def set_organization(self, p_i):
        """Set organization."""
        self.__organization = p_i

    security.declarePublic('get_uname')
    def get_uname(self):
        """Get user name."""
        return self.uname

    security.declarePublic('get_nickname')
    def get_nickname(self):
        """Get user's visible nick name."""
        if not self.has_nickname():
            return self.get_uname()
        else:
            return self.__nickname

    security.declareProtected(perm_view,'get_first_name')
    def get_first_name(self):
        """Get first name."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__first_name'):
            return ""
        else:
            return self.__first_name

    security.declareProtected(perm_view,'get_last_name')
    def get_last_name(self):
        """Get last name."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__last_name'):
            return ""
        else:
            return self.__last_name

    security.declareProtected(perm_view, 'get_email')
    def get_email(self):
        """Get email."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__email'):
            return ""
        else:
            return self.__email
    security.declareProtected(perm_view, 'get_language')
    def get_language(self):
        """Get language."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__language'):
            return ""
        else:
            return self.__language
    security.declareProtected(perm_view, 'get_photo')
    def get_photo(self, REQUEST=None):
        """Get photo."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__photo'):
            return ""
        else:
            if REQUEST and self.__photo_type:
                REQUEST.RESPONSE.setHeader('content-type',self.__photo_type)
            return self.__photo

    security.declareProtected(perm_view, 'get_photo_type')
    def get_photo_type(self):
        """Get photo's content type."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__photo_type'):
            return ""
        else:
            return self.__photo_type

    security.declareProtected(perm_view, 'get_address1')
    def get_address1(self):
        """Get address1. (street address)"""
        if not hasattr(self, '_' + self.__class__.__name__+ '__address1'):
            return ""
        else:
            return self.__address1
    security.declareProtected(perm_view, 'get_address2')
    def get_address2(self):
        """Get address2. (postal address2)"""
        if not hasattr(self, '_' + self.__class__.__name__+ '__address2'):
            return ""
        else:
            return self.__address2
    security.declareProtected(perm_view, 'get_country')
    def get_country(self):
        """Get country."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__country'):
            return ""
        else:
            return self.__country
    security.declareProtected(perm_view, 'get_homepage')
    def get_homepage(self):
        """Get homepage."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__homepage'):
            return ""
        else:
            return self.__homepage
    security.declareProtected(perm_view, 'get_phone')
    def get_phone(self):
        """Get phone."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__phone'):
            return ""
        else:
            return self.__phone
    security.declareProtected(perm_view, 'get_gsm')
    def get_gsm(self):
        """Get gsm."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__gsm'):
            return ""
        else:
            return self.__gsm
    security.declareProtected(perm_view, 'get_quote')
    def get_quote(self):
        """Get quote."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__quote'):
            return ""
        else:
            return self.__quote

    security.declareProtected(perm_view, 'render_quote')
    def render_quote(self):
        """Render quote."""
        return render(
            self.get_quote(),
            legal_tags=normal_entry_tags)

    security.declareProtected(perm_view, 'get_background')
    def get_background(self):
        """Get background."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__background'):
            return ""
        else:
            return self.__background

    security.declareProtected(perm_view, 'render_background')
    def render_background(self):
        """Render background."""
        return render(
            self.get_background(),
            legal_tags=normal_entry_tags)


    security.declareProtected(perm_view, 'get_personal_interests')
    def get_personal_interests(self):
        """Get personal interests."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__personal_interests'):
            return ""
        else:
            return self.__personal_interests

    security.declareProtected(perm_view, 'render_personal_interests')
    def render_personal_interests(self):
        """Render personal interests."""
        return render(
            self.get_personal_interests(),
            legal_tags=normal_entry_tags)

    security.declareProtected(perm_view, 'get_professional_interests')
    def get_professional_interests(self):
        """Get professional interests."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__professional_interests'):
            return ""
        else:
            return self.__professional_interests

    security.declareProtected(perm_view, 'render_professional_interests')
    def render_professional_interests(self):
        """Render professional interests."""
        return render(
            self.get_professional_interests(),
            legal_tags=normal_entry_tags)

    security.declareProtected(perm_view, 'get_organization')
    def get_organization(self):
        """Get organization."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__organization'):
            return ""
        else:
            return self.__organization

    security.declareProtected(perm_view, 'get_city')
    def get_city(self):
        """Get city."""
        if not hasattr(self, '_' + self.__class__.__name__+ '__city'):
            return ""
        else:
            return self.__city

    security.declarePrivate('update_active')
    def update_active(self, course_id):
        """Update the user activity record."""
        self.__last_active[course_id] = time.time()
        self._p_changed = 1

    security.declarePrivate('last_active')
    def last_active(self, course_id):
        """Return time when user was last active."""
        return self.__last_active[course_id]

    security.declareProtected(perm_edit, 'set_password')
    def set_password(self, pwd):
        roles = self.acl_users.getUser(self.get_id()).roles
        self.acl_users._doChangeUser(self.getId(), pwd, roles, [])

    security.declareProtected(perm_edit, 'set_roles')
    def set_roles(self, roles):
        """Set user's Fle global roles."""
        if type(roles) == types.StringType: roles = [roles]
        else: roles = list(roles)
        fle=self.parent().parent()
        person=self.get_uname()
        fle.manage_delLocalRoles((person,))
        fle.manage_setLocalRoles(person,roles)

    security.declareProtected(perm_view, 'has_role')
    def has_role(self, role):
        """Has user given role."""
        return role in get_roles(self.parent().parent(),self.get_uname())

    security.declareProtected(perm_view, 'has_any_role')
    def has_any_role(self, roles):
        """Has user any of given role."""
        real_roles = get_roles(self.parent().parent(),self.get_uname())
        for role in roles:
            if role in real_roles: return 1

        return 0

    security.declareProtected('View', 'has_right_to_edit')
    def has_right_to_edit(self, REQUEST):
        logged_user = self.parent().get_user_info(self.get_current_user(REQUEST))
        if self.has_role('FLEAdmin'):
            if not logged_user.has_role('FLEAdmin'):
                return 0
            else:
                # a user with FLEAdmin role can edit do anything (even edit
                # other user with FLEAdmin role.
                return 1
        elif self.get_id() == logged_user.get_id():
            return 1
        else:
            return self.is_power_user(
                self.get_current_user(REQUEST))


    security.declareProtected(perm_edit, 'edit_user_form_handler')
    def edit_user_form_handler(
        self,
        REQUEST,

        # actual user info data from forms
        pwd = '',               # password
        pwd_confirm = '',       # password confirmation
        nickname = None,
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

        cancel = '',
        commit = '',
        ):
        """User info edit form handler."""

        if cancel:
            if REQUEST:
                REQUEST.RESPONSE.redirect(
                    self.state_href(REQUEST, 'show_user_info'))
            return

        if not self.has_right_to_edit(REQUEST):
            raise 'FLE Error', \
                  'I am sorry Dave. I am afraid I cannot do that.'

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
        for x in ('first_name', 'last_name'):
            e = REQUEST.get(x)
            if e and not is_valid_title(e):
                errors.append(REQUEST['L_' + x])

        # Optional
        for x in ('nickname', 'email', 'organization', 'language', 'address1',
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

        # Check that the nick name isn't already taken
        if nickname and nickname!=self.get_nickname():
            if nickname in \
               [x.get_uname() for x in self.fle_users.get_users()]\
               or nickname in \
               [x.get_nickname() for x in self.fle_users.get_users()]:
                errors.append(REQUEST['L_nickname'])

        if len(errors) > 0:
            # Update photo, because we can't save that to URL.
            if photo_upload and len(photo_upload.filename) > 0:
                self.set_photo(photo_upload.read(),
                               photo_upload.headers['content-type'])

            # Similar (but not identical!) reasons here...
            if webtop_bg_upload and len(webtop_bg_upload.filename) > 0:
                self.webtop.set_webtop_bg_from_image_data(
                    webtop_bg_upload.read())
            elif default_webtop_bg:
                self.webtop.set_webtop_bg_from_default_image(default_webtop_bg)

            action = apply(
                make_action,
                ['edit_user_form'] +
                [(x, REQUEST.get(x)) for x in
                 ('first_name', 'last_name', 'email', 'homepage',
                  'organization', 'language', 'role',
                  'photo_url', 'default_webtop_bg',
                  'address1', 'address2', 'city',
                  'country', 'phone', 'gsm',
                  'quote', 'background', 'personal_interests',
                  'professional_interests')])

            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_invalid_input'],
                message=REQUEST['L_invalid_fields'] + ": '" + \
                "' , '".join(errors) + "'",
                action=action)

        if nickname!=None and nickname!=self.get_nickname() \
           and self.may_edit_nickname(REQUEST):
            self.set_nickname(nickname)

        if webtop_bg_upload and len(webtop_bg_upload.filename) > 0:
            self.webtop.set_webtop_bg_from_image_data(webtop_bg_upload.read())
        elif default_webtop_bg:
            self.webtop.set_webtop_bg_from_default_image(default_webtop_bg)

        self.edit_info(
            first_name, last_name, email, organization, language,
            photo_upload, photo_url, [], address1, address2, city,
            country, homepage, phone, gsm, quote,
            background, personal_interests,
            professional_interests)

        if role:
            if role == 'User':
                self.set_roles(('User',))
            elif role in ('Staff', 'FLEAdmin'):
                self.set_roles(('User', role))
            else:
                raise 'FLE Error', 'Invalid role'

        if pwd and (pwd != self.empty_pwd()):
            # change password
            if pwd == pwd_confirm:
                self.set_password(pwd)

                # If user changed her own password, return a message dialog
                # (with info that the browser will ask for username/password).
                if repr(REQUEST.AUTHENTICATED_USER) == self.get_uname():
                    self.get_lang(('common','usermgmnt'),REQUEST)
                    return self.message_dialog(
                        self, REQUEST,
                        title=REQUEST['L_passwd_changed'],
                        message=REQUEST['L_passwd_changed_explanation2'],
                        action='show_user_info')

            else:
                if REQUEST:
                    self.get_lang(('common','usermgmnt'),REQUEST)
                    return self.message_dialog(
                        self, REQUEST,
                        title=REQUEST['L_error'],
                        message=REQUEST['L_password_mismatch'],
                        action='edit_user_form')

        if REQUEST:
            REQUEST.RESPONSE.redirect(
                self.state_href(REQUEST, 'show_user_info'))



    # Implementation of edit_user_form_handler without http code.
    security.declarePrivate('edit_info')
    def edit_info(
        self,

        first_name = None,
        last_name = None,
        email = None,
        organization = None,
        language = None,
        photo_upload = None,
        photo_url = None,
        group_ids = [],
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
        ):
        """Commits changes in userinfo object."""

        if first_name != None: self.set_first_name(first_name)
        if last_name != None: self.set_last_name(last_name)
        if email != None: self.set_email(email)
        if organization != None: self.set_organization(organization)
        if language != None: self.set_language(language)
        for g_id in group_ids: self.add_to_group(g_id)
        if address1 != None: self.set_address1(address1)
        if address2 != None: self.set_address2(address2)
        if city != None: self.set_city(city)
        if country != None: self.set_country(country)
        if homepage != None: self.set_homepage(homepage)
        if phone != None: self.set_phone(phone)
        if gsm != None: self.set_gsm(gsm)
        if quote != None: self.set_quote(quote)
        if background != None: self.set_background(background)
        if personal_interests != None:
            self.set_personal_interests(personal_interests)
        if professional_interests != None:
            self.set_professional_interests(professional_interests)

        if photo_upload != None:
            if hasattr(photo_upload,'filename') and \
               len(photo_upload.filename) > 0:
                photo_data = photo_upload.read()
                self.set_photo(photo_data,photo_upload.headers['content-type'])
                return
        if photo_url != None and photo_url != '' and photo_url != 'http://':
            photo_data = get_url(photo_url)
            self.set_photo(photo_data)

Globals.InitializeClass(UserInfo)

# EOF
