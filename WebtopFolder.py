# $Id: WebtopFolder.py,v 1.88 2003/06/13 07:57:12 jmp Exp $
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

"""Contains class WebtopFolder, which represents a folder in a user's webtop."""

__version__ = "$Revision: 1.88 $"[11:-2]

from copy import copy
from urllib import quote_plus, quote
import Globals
from common import reload_dtml, add_dtml
from input_checks import is_valid_title, is_valid_url, strip_all
from WebtopItem import WebtopItem
from WebtopLink import WebtopLink
from WebtopMemo import WebtopMemo
from WebtopFile import WebtopFile
from Cruft import Cruft
import Webtop
import OFS
import FLE
from TraversableWrapper import TWFolder
from TempObjectManager import TempObjectManager
from AccessControl import ClassSecurityInfo
from common import add_dtml
from common import perm_view, perm_edit, perm_manage, perm_add_lo
from common import intersect_bool

# This class acts as a container to other WebtopItems and as the factory
# object used to manipulate them.
class WebtopFolder(
    WebtopItem,
    OFS.Folder.Folder,
    TempObjectManager,
    Cruft):
    """A folder in a Webtop."""
    meta_type = "WebtopFolder"

    list_of_types=('WebtopFolder', 'WebtopLink', 'WebtopMemo', 'WebtopFile',
                   'GroupFolder', 'GroupFolderProxy')
    security = ClassSecurityInfo()

    def __init__(self, parent, name):
        """Construct the webtop folder object."""
        WebtopItem.__init__(self,parent,name)
        TempObjectManager.__init__(self)
        #new_reload_dtml(self, self.dtml_files)
        self.set_icon('images/fol_small')

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self,item,container):
        """Clean up creation - create the TempObjectManager
        and set permissions."""
        TempObjectManager.manage_afterAdd(self, item, container)
        WebtopItem.manage_afterAdd(self, item, container)
        #self.manage_permission('Edit', ['FLEAdmin', 'Owner'], 1)

    # for ZCatalog
    security.declarePrivate('get_content')
    def get_content(self):
        """Return content (names of this folder's Webtop items in
        one string)"""
        return ' '.join(
            [o.get_name() for  o in self.objectValues(
            ('WebtopFolder', 'WebtopLink', 'WebtopMemo', 'WebtopFile'))])

    security.declareProtected(perm_view, 'has_content')
    def has_content(self):
        """Any WebtopItems in this folder?"""
        return len(self.objectIds(self.list_of_types)) > 0

    security.declareProtected(perm_view, 'list_contents')
    def list_contents(self, criteria=''):
        """Returns a list of all different WebtopItems in this folder."""

        # When sorting by type, display GroupFolders first, then
        # WebtopFolder, and finally others according to their
        # meta_type (& some extra data, see code below.)
        def __sort_func(a,b):
            if a == 'GroupFolderProxy': return -1
            if a == 'WebtopFolder' and b != 'GroupFolderProxy': return -1
            return a <= b

        def __case_insensitive_sort_func(a,b):
            a_lower = a.lower()
            b_lower = b.lower()
            if a_lower < b_lower: return -1
            elif a_lower == b_lower: return 0
            else: return 1

        if criteria == '': criteria = 'date'

        objs = self.objectValues(self.list_of_types)

        if criteria == 'type':
            d = {}
            mtypes = []
            for o in objs:
                mtype = o.meta_type
                if mtype == 'WebtopFile': mtype += o.get_content_type()

                # We append name in order to get unique keys
                mtype += o.get_name()
                mtypes.append(mtype)
                d[mtype] = o

            mtypes.sort(__sort_func)
            s_objs = []
            for n in mtypes:
                s_objs.append(d[n])

            return s_objs

        elif criteria == 'name':
            d = {}
            names = []
            for o in objs:
                name = o.get_name()
                names.append(name)
                d[name] = o

            names.sort(__case_insensitive_sort_func)
            s_objs = []
            for n in names:
                s_objs.append(d[n])

            return s_objs

        elif criteria == 'size':
            d = {}
            sizes = []
            for o in objs:
                # We append name in order to get unique keys
                # 10 digits should be enough for everybody. :-)
                size = '%010d' % o.get_size() + o.get_name()
                sizes.append(size)
                d[size] = o

            sizes.sort()
            s_objs = []

            for n in sizes:
                s_objs.append(d[n])

            return s_objs


        elif criteria == 'date':
            d = {}
            timestamps = []
            for o in objs:
                # We append name in order to get unique keys
                timestamp = '%012.4f' % o.get_timestamp() + o.get_name()
                timestamps.append(timestamp)
                d[timestamp] = o

            timestamps.sort()
            timestamps.reverse()
            s_objs = []
            for n in timestamps:
                s_objs.append(d[n])

            return s_objs

        else:
            raise 'FLE Error', 'Unknown sort criteria'

    security.declareProtected(perm_edit, 'add_folder_handler')
    def add_folder_handler(
        self, REQUEST, my_name,
        submit = '', # form buttons
        cancel = '', #
        ):
        """Handles the input from folder add form."""

        self.get_lang(('common','webtop'),REQUEST)
        my_name = strip_all(my_name)
        if submit:
            if not is_valid_title(my_name):
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_name'],
                    message=REQUEST['L_give_valid_name'],
                    action='wt_add_folder?my_name=%s' % quote_plus(my_name))
            if my_name in [o.get_name() for o in self.list_contents()]:
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_name'],
                    message=REQUEST['L_name_taken'] % my_name,
                    action='wt_add_folder?name=%s' % quote_plus(my_name))

            fold_obj = self.add_folder(my_name)
            fold_obj.set_author(str(REQUEST.AUTHENTICATED_USER))
        elif cancel:
            pass
        else:
            # This code should never be reached.
            raise 'FLE Error', 'Unknown button'

        return REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))

    security.declarePrivate('add_folder')
    def add_folder(self,name):
        """Implementation of add_folder_handler without http code."""
        f = WebtopFolder(self,name)
        self._setObject(f.id,f)
        return f.__of__(self)

    security.declareProtected(perm_edit, 'add_link_handler')
    def add_link_handler(
        self, REQUEST, my_name, url,
        type = '',
        submit = '', # form buttons
        cancel = '', #
        back_link = '', # 'add link to webtop' feature outside webtop
        ):
        """Handles the input from link add form."""

        if REQUEST:
            self.get_lang(('common','webtop'),REQUEST)
        my_name = strip_all(my_name)
        if submit:
            if not is_valid_title(my_name):
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_name'],
                    message=REQUEST['L_give_valid_name'],
                    action='wt_add_link?my_name=%s&my_url=%s' % \
                    (quote_plus(my_name), quote_plus(url)))
            elif my_name in [o.get_name() for o in self.list_contents()]:
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_name'],
                    message=REQUEST['L_name_taken'] % my_name,
                    action='wt_add_link?my_name=%s&url=%s' % \
                    (quote_plus(my_name), quote_plus(url)))
            if not is_valid_url(url):
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_url'],
                    message=REQUEST['L_invalid_url_message'],
                    action='wt_add_link?my_name=%s&url=%s' % \
                    (quote_plus(my_name), quote_plus(url)))
            link_obj = self.add_link(my_name, url)
            link_obj.set_author(str(REQUEST.AUTHENTICATED_USER))
        elif back_link:
            if not is_valid_title(my_name):
##                return self.message_dialog(
##                    self, REQUEST,
##                    title=REQUEST['L_invalid_name'],
##                    message=REQUEST['L_give_valid_name'],
##                    action=back_link)
                # I think raise is more appropriate here because
                # if we have invalid name here, we have a _bug_
                # and not an user error. --jmp 2002-02-20
                raise 'FLE Error', 'Invalid name for link.'

            # If name already exists generate a new name...
            my_name = self.__build_name(my_name)

            link_obj = self.add_link(my_name,url,1)
            link_obj.set_author(str(REQUEST.AUTHENTICATED_USER))
            if REQUEST:
                return self.message_dialog(
                    self, REQUEST,
                    title=REQUEST['L_webtop_link_added'],
                    message=REQUEST['L_added_webtop_link'] % (type, my_name),
                    action=back_link)
            else:
                return
        elif cancel:
            pass
        else:
            # This code should never be reached.
            raise 'FLE Error', 'Unknown button'

        if REQUEST:
            REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))

    security.declarePrivate('add_link')
    def add_link(self,name,url_or_obj,internal=0):
        """Implementation of add_link_handler without http code."""
        l = WebtopLink(self,name,url_or_obj,internal)
        self._setObject(l.id,l)
        return l.__of__(self)

    security.declarePrivate('add_group_folder_proxy')
    def add_group_folder_proxy(self, name, course_id):
        """Create GroupGolderProxy into WebtopFolder."""
        from GroupFolderProxy import GroupFolderProxy
        uname = str(self.getOwner())

        name = self.__build_name(name)

        l = GroupFolderProxy(self, name, course_id)
        self._setObject(l.id, l)

        l.changeOwnership(self.acl_users.getUser(uname).__of__(self.acl_users))

        # Copy local roles that user (owner of the WebtopFolder) has
        # on the course to the GroupFolderProxy. (+ everybody should
        # own her own GroupFolderProxy!)
        for user, roles in self.courses.get_child(course_id).get_local_roles():
            if uname == user:
                self.get_child(l.id).manage_setLocalRoles(uname,
                                                          roles + ('Owner',))
                return

        raise 'FLE Error', 'User does not have any role in the course!'

    security.declarePrivate('recursive_delete_group_folder_proxy')
    def recursive_delete_group_folder_proxy(self, course_id):
        """Delete all GroupFolderProxy objects (pointing to given
        course) in this folder and recursively in all subfolders."""

        for proxy in self.objectValues('GroupFolderProxy'):
            if proxy.get_course_this_belongs_to().get_id() == course_id:
                self._delObject(proxy.get_id())

        for folder in self.objectValues(('WebtopFolder', 'TWFolder')):
            folder.recursive_delete_group_folder_proxy(course_id)

    security.declarePrivate('recursive_cleanup_for_group_folder_proxies')
    def recursive_cleanup_for_group_folder_proxies(self, save_ids):
        """Delete all GroupFolderProxy objects in this folder and
        recursively in all subfolders unless GroupFolderProxy belongs
        to some course given by save_ids."""
        for proxy in self.objectValues('GroupFolderProxy'):
            if proxy.get_course_this_belongs_to().get_id() not in save_ids:
                self._delObject(proxy.get_id())

        for folder in self.objectValues(('WebtopFolder', 'TWFolder')):
            folder.recursive_cleanup_for_group_folder_proxies(save_ids)
        

    security.declareProtected(perm_edit, 'add_file_handler')
    def add_file_handler(
        self, REQUEST, my_name, file=None,
        key = '',
        submit = '', # form buttons
        cancel = '', #
        ):
        """Handles the input from upload form."""

        self.get_lang(('common','webtop'),REQUEST)
        my_name = strip_all(my_name)
        if submit:
            message = ''

            if self.get_quota() >= 0: # Quota in use?
                # Would we exceed the quota?
                if file and len(file.filename):
                    file.seek(0, 2)
                    size = self.find_class_obj(Webtop.Webtop).get_size() + \
                           file.tell()
                    file.seek(0, 0)

                    if size > self.get_quota():
                        return self.message_dialog_error(
                            self, REQUEST,
                            title=REQUEST['L_quota_reached_title'],
                            message=REQUEST['L_quota_reached'],
                        action='index_html')

            # Check name
            if not is_valid_title(my_name):
                message = REQUEST['L_give_valid_name']+'. '
            elif my_name in [o.get_name() for o in self.list_contents()]:
                message = REQUEST['L_name_taken'] % my_name

            # Check file
            if not key:
                if (not file) or len(file.filename) is 0:
                    message += ' '+REQUEST['L_no_file_supplied']

            if message:
                if (not key) and file and len(file.filename) > 0:
                    key = self.add_tmp_object(WebtopFile(self, 'spam', file))
                if key: action = 'wt_upload?key=%s&my_name=%s' % \
                                 (quote_plus(key),
                                  quote_plus(my_name))
                else: action = 'wt_upload?my_name=%s' % quote_plus(my_name)
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_error'],
                    message=message,
                    action=action)
            else:
                if key:
                    f = self.remove_tmp_object(key)
                    f.set_name(my_name)
                    self._setObject(f.id,f)
                    f.set_author(str(REQUEST.AUTHENTICATED_USER))
                else:
                    file_obj = self.add_file(my_name,file)
                    file_obj.set_author(str(REQUEST.AUTHENTICATED_USER))

        elif cancel:
            if key: self.remove_tmp_object(key)
        else:
            # This code should never be reached.
            raise 'FLE Error', 'Unknown button'

        REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))

    security.declarePrivate('add_file')
    def add_file(self,name,file):
        """Implementation of add_file_handler without http code."""
        f = WebtopFile(self, name, file)
        self._setObject(f.id,f)
        return f.__of__(self)

    security.declareProtected(perm_edit, 'add_memo_handler')
    def add_memo_handler(
        self,
        REQUEST,
        my_name,
        contents,
        submit='',
        cancel=''):
        """Handles the input from memo add form."""

        self.get_lang(('common','webtop'),REQUEST)
        my_name = strip_all(my_name)
        if submit:
            if not is_valid_title(my_name):
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_name'],
                    message=REQUEST['L_give_valid_name'],
                    action='wt_add_memo?my_name=%s&contents=%s' % \
                    (quote_plus(my_name), quote_plus(contents)))
            elif my_name in [o.get_name() for o in self.list_contents()]:
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_name'],
                    message=REQUEST['L_name_taken'] % my_name,
                    action='wt_add_memo?my_name=%s&contents=%s' % \
                    (quote_plus(my_name), quote_plus(contents)))
            else:
                memo_obj = self.add_memo(my_name,contents)
                memo_obj.set_author(str(REQUEST.AUTHENTICATED_USER))

        elif cancel:
            pass
        else:
            # This code should never be reached.
            raise 'FLE Error', 'Unknown button'

        REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))

    security.declarePrivate('add_memo')
    def add_memo(self,name,contents):
        """Implementation of add_memo_handler without http code."""
        m = WebtopMemo(self,name,contents)
        self._setObject(m.id,m)
        return m.__of__(self)

    security.declareProtected(perm_edit, 'form_handler')
    def form_handler(
        self,
        item_ids=None,
        copy='', cut='', paste='',           # submit buttons
        remove='', rename='', select_all='', #
        REQUEST=None):
        """Handles the input from folder default form:
        item copy/cut/paste, remove and rename operations."""
        self.get_lang(('common','webtop'),REQUEST)

        # Quota reached? (GroupFolders don't use quota.)
        if not intersect_bool(
            ('GroupFolder', 'GroupFolderProxy'),
            [t[0].meta_type for t in self.list_parents_to_top()]) \
            and self.is_quota_limit_reached() and (copy or cut or paste):
            if REQUEST:
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_quota_reached_title'],
                    message=REQUEST['L_quota_reached'],
                    action='index_html')
            else:
                raise 'FLE Error', \
                      "Can't copy/cut/paste when quota is reached."
        if select_all:
            REQUEST.RESPONSE.redirect(
                self.state_href(REQUEST, 'index_html?select_all=1'))
            return
        if paste:
            self.paste()
        elif item_ids:
            from types import StringType
            if type(item_ids) is StringType:
                item_ids=(item_ids,)
            objs = self.map_ids_to_objects(item_ids)

            if remove:
                self.remove(objs)
            elif copy:
                self.copy(objs)
            elif cut:
                self.cut(objs)
            elif rename:
                REQUEST.RESPONSE.redirect(
                    self.state_href(REQUEST, 'wt_rename?item_ids=%s' % \
                                    quote(repr(item_ids))))
                return
            else:
                raise 'No action specified!'
        else:
            if REQUEST:
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_no_item_selected'],
                    message=REQUEST['L_select_item_first'],
                    action='index_html')

        REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))

    # FIXME: input_checks
    security.declareProtected(perm_edit, 'rename_helper')
    # This is called from wt_rename to convert a list stored in url
    # back to list. There are two cases:
    #
    # 1. User select some object on index_html page and clicks 'rename':
    #
    #    index_html(dtml) -> form_handler -> redirect to wt_rename(dtml)
    #
    #    In this case only Ids of objects are passed to form_handler
    #
    #
    # 2. As long user gives invalid input we are in the following loop:
    #
    #    wt_rename -> rename_handler -> message_dialog(dtml) -> wt_rename
    #
    #    Here we have pass user's invalid names back to wt_rename so
    #    that user doesn't have to start everytime from scratch.
    def rename_helper(self, expr1, expr2=None):
        """Helper function for DTML method wt_rename.dtml"""
        if not expr2:
            return eval(expr1)
        else:
            id_list = eval(expr1)
            name_list = eval(expr2)
            retval = []
            for i in range(len(id_list)):
                retval.append((id_list[i], name_list[i]))
            return retval

    security.declarePrivate('get_clipboard')
    def get_clipboard(self):
        """Locates and returns a reference to the webtop's clipboard."""
        return self.parent().get_clipboard()

    security.declareProtected(perm_view, 'is_clipboard_empty')
    def is_clipboard_empty(self):
        """Is clipboard empty?"""
        return not self.get_clipboard().objectIds()

    def __clear_clipboard(self):
        """Empties the webtop's clipboard."""
        clip = self.get_clipboard()
        for item_id in clip.objectIds():
            clip._delObject(item_id)
        return clip

    security.declarePrivate('copy')
    def copy(self,items):
        """Copies items into the webtop's clipboard."""
        clip = self.__clear_clipboard()
        for item in items:
            newitem = item._getCopy(self)
            #print "[copied item: %s from %s]" % (repr(newitem), repr(item))
            newitem.id = self.generate_id()
            clip._setObject(newitem.id,newitem)
        #print "CLIPBOARD: %s" % repr(clip.objectItems())

    security.declarePrivate('cut')
    def cut(self,items):
        """Cuts items into the webtop's clipboard."""
        clip = self.__clear_clipboard()
        for item in items:
            self._delObject(self.find_id_used_in_parent(item))
            clip._setObject(item.id,item)
        #print "CLIPBOARD: %s" % repr(clip.objectItems())

    # FIXME: i18n word 'copy'
    def __build_name(self,name):
        """Constructs a name for an item pasted from the clipboard.
        If the item's own name is already used, a suitable
        postfix is added."""
        if not self.name_exists(name):
            return name

        iter = 1
        newname=name+' (copy)'
        while self.name_exists(newname):
            iter += 1
            newname=name+' (copy ' + str(iter) + ')'
        return newname

    security.declarePrivate('paste')
    def paste(self):
        """Pastes items from the webtop's clipboard."""
        clip = self.get_clipboard()
        for item in clip.objectValues():
            newitem = item._getCopy(self)
            #print "[pasted item: %s]" % repr(newitem)
            newitem.id = self.generate_id()
            newitem.set_name(self.__build_name(newitem.get_name()))
            self._setObject(newitem.id,newitem)

    security.declarePrivate('remove')
    # items: list of removable object references in current
    def remove(self,items):
        """Removes items from this folder, placing them in trash.
        Or actually: in the tmp_objects folder inside this WebtopFolder."""
        for item in items:
            self.move_to_tmp(item)

    security.declareProtected(perm_edit, 'rename_handler')
    def rename_handler(
        self, REQUEST,
        item_id_list,
        new_name_list,
        submit = '', # form buttons
        cancel = '', #
        ):
        """Handles rename_form submission."""

        if submit:

            bad_names = []
            for name in new_name_list:
                if not is_valid_title(name):
                    bad_names.append(name)

            if bad_names:
                self.get_lang(('common', 'webtop',),REQUEST)
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_name'],
                    message=REQUEST['L_invalid_names'] +' %s' % \
                    " ".join([repr(n) for n in bad_names]),
                    action='wt_rename?item_ids=%s&names=%s' % \
                    (quote(repr(item_id_list)),
                     quote(repr(new_name_list))))

            # Same name given for several object?
            new_names = list(copy(new_name_list))
            new_names.sort()
            for i in range(len(new_names)-1):
                if new_names[i] == new_names[i+1]:
                    self.get_lang(('webtop',),REQUEST)
                    return self.message_dialog_error(
                        self, REQUEST,
                        title=REQUEST['L_invalid_name'],
                        message=REQUEST['L_same_names'],
                        action='wt_rename?item_ids=%s&names=%s' % \
                        (quote(repr(item_id_list)),
                         quote(repr(new_name_list))))


            # Some other object has already some given name?

            # FIXME: slow: 'not in' inside loop...
            names_in_use = [o.get_name() for o in \
                            filter(lambda x, y=item_id_list: \
                                   x.get_id() not in y,
                                   self.list_contents())]

            bad_names = []
            for name in new_name_list:
                if name in names_in_use:
                    bad_names.append(name)

            if bad_names:
                self.get_lang(('webtop',),REQUEST)
                return self.message_dialog_error(
                    self, REQUEST,
                    title=REQUEST['L_invalid_name'],
                    message=REQUEST['L_names_in_use'] + ' %s' % \
                    " ".join([repr(n) for n in bad_names]),
                    action='wt_rename?item_ids=%s&names=%s' % \
                    (quote(repr(item_id_list)),
                     quote(repr(new_name_list))))

            for i in range(len(item_id_list)):
                (id, name) = (item_id_list[i], new_name_list[i])
                self.rename(self.get_child(id), name)

        elif cancel:
            pass
        else:
            # This code should never be reached.
            raise 'FLE Error', 'Unknown button'


        REQUEST.RESPONSE.redirect(self.state_href(REQUEST, 'index_html'))

    security.declarePrivate('name_exists')
    def name_exists(self,name):
        """Checks whether a given name exists already in the folder."""
        for item in self.objectValues():
            if hasattr(item,'get_name'):
                if item.get_name()==name:
                    return 1
        return 0

    security.declarePrivate('rename')
    # Input checks are done in rename_handler.
    def rename(self,objref,new_item_name):
        """Implementation of item rename."""
        objref.set_name(new_item_name)

    security.declareProtected(perm_view, 'get_size')
    def get_size(self):
        """Return size of the object."""
        size = 0

        for o in self.objectValues(
            ('WebtopFolder', 'WebtopLink', 'WebtopMemo', 'WebtopFile')):
            size += o.get_size()

        return size

Globals.InitializeClass(WebtopFolder)
# EOF
