# $Id: common.py,v 1.88 2004/09/02 09:55:50 tarmo Exp $

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

"""Contains miscellaneous utility functions that are needed often in FLE."""

__version__ = "$Revision: 1.88 $"[11:-2]
__doc__ = """Holds some common global defintions/functions used in Fle."""

import os
import string
from urllib import quote_plus

# The path to stuff, duh
if __name__ != '__main__':
    file_path = __import__('Globals').package_home(globals())
    import os.path
    image_file_path = os.path.join(file_path, 'ui', 'images')
    styles_path = os.path.join(file_path, 'ui', 'styles')
    ui_path = os.path.join(file_path, 'ui')

###########################################################
# user_info_folder_name
# Holds the name of the folder in where the UserInfo objects
# are put in the Fle root folder.
user_info_folder_name = 'fle_users'
user_timeout_delay = 300        # 5 minutes.

# For Webtop backrounds
bg_stuff = {
    'bgcolor_rd': ('rd', 'cc3333'),
    'wt_bg_bl': ('bl','3f82b5'),
    'wt_bg_gray1': ('gray', 'c0c0c0'),
    'wt_bg_gray2': ('gray', '99af73'),
    'wt_bg_tq': ('tq', '93bdb6'),
    'wt_bg_yl': ('yl', 'c2c32e'),
    }

###########################################################
# fle_roles
# The zope roles Fle will use. It is important that these are sorted
# so that a lower indexnumber will yield a lower priviledged role.
# NOTE: Why? --jmp 2001-10-10 I don't know/remember ;) --granbo

# Please *NOTE* that if these are changed, the fle object needs to
# be reinstalled.
# FIXME: replace these with config hooks.
fle_roles = ('User', 'Staff', 'FLEAdmin')

roles_admin = ('Manager','FLEAdmin')
roles_staff = ('Manager','FLEAdmin','Staff')
roles_user = ('Manager','FLEAdmin','Staff','User')

perm_view = 'View'
perm_edit = 'Edit'
perm_manage = 'Manage FLE'
perm_add_lo = 'Add FLE LO'

course_level_roles = ('Student', 'Tutor', 'Teacher')
roles_teacher = ('Manager','FLEAdmin','Teacher',)
roles_tutor = ('Manager','FLEAdmin','Teacher','Tutor')
roles_student = ('Manager','FLEAdmin','Teacher','Tutor','Student')

# ('dd', 'mm', 'yyyy')
def convert_date(dd, mm, yyyy):
    """Take date, month and year in string format and
       return date in time.time() format."""
    import time
    from string import atoi
    date = 0
    try:
        year = atoi(yyyy)
        month = atoi(mm)
        day = atoi(dd)
    except:
        raise 'Dates not in a string format.'
    if not (1 <= month <= 12):
        raise 'Month value must be in 1-12'
    if not (1 <= day <= 31):
        raise 'Day value must be in 1-31'
    try:
        date_tuple = (atoi(yyyy), atoi(mm), atoi(dd), 0,0,0,0,0,0)
        date = time.mktime(date_tuple)
    except:
        raise 'Date conversion failed'
    return date

# Traverses the whole Zope tree under given object
# calling reload_dtml() for each object -> potentially _very_ expensive.
def tree_reload_dtml(obj):
    if 0 and hasattr(obj, 'dtml_files'):
        #reload_dtml(obj)
        for tup in obj.dtml_files:
            add_dtml(obj,tup)
    if hasattr(obj, 'reload_dtml'):
        obj.reload_dtml()

    for e in obj.objectValues():
        tree_reload_dtml(e)

def add_dtml(obj, tup):
    """Adds one dtml-objects to obj. Eat an argument like:
    ('index_html', 'Index Page', 'ui/Course/index_html')"""
    apply(add_dtml_obj, (obj,)+tup)

def reload_dtml(obj, tuple_of_tuples, raise_exc_on_error=0):
    """Eat an object, and reload the dtmls in it. Will raise Exception if
    there is an error."""

    for tup in tuple_of_tuples:
        (id, title, file) = tup

        try:
            obj.manage_delObjects(id)
        except: pass
        add_dtml(obj, tup)

template_code = '''
def %(function_name)s(self, REQUEST, **args):
    """..."""
    for key in args.keys():
        if not key in REQUEST.keys():
            REQUEST[key] = args[key]

    return self.fle_root().%(the_rest)s(self, REQUEST)
'''
template_code = '''
def %(function_name)s(self, REQUEST):
    """..."""
    return self.fle_root().%(method_path)s(self, REQUEST)
'''

def new_reload_dtml(obj, tuple_of_tuples):
    """..."""
    raise "Don't use this error", "Don't use this yet."
    for tup in tuple_of_tuples:
        (_id, title, file) = tup
        tc = \
           template_code % {
               'function_name':_id,
               'method_path': string.join(file.split('/'), '.') }
        #raise 'Excer', str("<pre>"+tc+"</pre>")
        try:
           exec(tc)
        except SyntaxError:
           raise 'Excer', str("<pre>"+tc+"</pre>")
        obj.__class__.__dict__[_id] = eval(_id)
        del _id
        obj._p_changed = 1 # Do we really need this?

def make_action(action, *args):
    if action.find('?') == -1:
        retval = action + '?'
    else:
        retval = action + '&'
    for arg in args:
        if arg[1]: value = arg[1]
        else: value = ''
        retval += arg[0] + '=' + quote_plus(value) + '&'
    return retval[:-1]

###########################################################
# Randomness stuff.
# strong_random()
# Returns a strong pseudorandom signed integer.
# FIXME: check if zope seeds random again on each new request.
# FIXME: If it does, we need to think things over. I neither
# FIXME: think this is thread-safe, blah blah.
def _strong_random():
    from random import random
    from sys import maxint
    rv = 0
    seed = 0
    b = maxint
    for shift in range(0, 32, 8):
        # we use only the least significant byte, so ..
        seed = seed ^ int(round(random() * b))
        rv = rv ^ ((seed&0xff) << shift)
    return rv

# random()
random = _strong_random

##################################################
# a_char()
# Returns a printable character, duh.
#_printable_char = __import__('string').letters
_printable_char = [chr(x) for x in range(ord('a'), ord('z') + 1)] + \
                  [chr(x) for x in range(ord('A'), ord('Z') + 1)]
def a_char(idx, _7bit_only=0):
    if type(idx) != type(1):
        raise TypeError, 'a_char requires int argument'
    char_tbl = _printable_char
    return char_tbl[idx%len(char_tbl)]

def add_image_obj(obj, id, title, file):
    f = open(file,"rb")
    content = f.read()
    f.close()
    obj.manage_addImage(id, content, title)

# This returns all roles the person has in the given object
# and acquired from above.
def get_roles(obj, person):
    try:
        roles = list(obj.acl_users.getUser(person).getRoles()) # global roles
    except AttributeError:
        return ()

    for o in obj.aq_chain[:-1]:
        o=o.aq_base
        if hasattr(o,'get_local_roles'):
            for tuples in o.get_local_roles():
                if tuples[0] == person:
                    roles = roles + list(tuples[1])
    return tuple(roles)

# This returns the local roles for the given object exactly.
# (no acquired roles)
def get_local_roles(obj, person):
    roles = []
    o=obj.aq_base
    if hasattr(o,'get_local_roles'):
        for tuples in o.get_local_roles():
            if tuples[0] == person:
                roles = roles + list(tuples[1])
    return tuple(roles)


##################################################
# Adds an zope manageable dtml object to obj
def add_dtml_obj(obj, id, title, file):
    join = __import__("os").path.join
    f = open(join(file_path, file+'.dtml'))
    file = f.read()
    f.close()
    obj.manage_addDTMLMethod(id, title, file)

    # Currently we give View permission for every authenticated
    # user for all dtml files, but when they try to access data
    # from Zope, access restrictions apply.
    getattr(obj, id).manage_permission(
        'View',
        ['Authenticated',], 0)

    return getattr(obj, id)

def new_add_dtml_obj(obj, id, title, file_path):
    #raise 'DONT USE', "Don't user this just yet."
    f = open(file_path)
    file = f.read()
    f.close()
    obj.manage_addDTMLMethod(id, title, file)

    getattr(obj, id).manage_permission(
        'View',
        ['Authenticated',], 0)


##################################################
# get_url()
# Generalization of reading the contents of an url.
def get_url(url):
    import urllib
    try:
        rv = urllib.urlopen(url).read()
    except IOError:
        return None
    return rv

# HTML Conversion table
def _get_all_conv_table():
    from string import upper
    rv = {}
    my_range = range(1,256)
    char_tbl = [chr(x) for x in my_range]
    conv = [upper(hex(x)[2:]) for x in my_range]
    for (char, con) in map(None, char_tbl, conv):
        rv[char] = '%%%s' % con
    return rv
def _get_conv_table(sc=None):
    rv = {}

    if sc is None:
        for char in range(1, 128):
            rv[chr(char)] = chr(char)
        for char in range(128, 256):
            rv[chr(char)] = '&#%d;' % char

    else:
        # There is a special case thingy.
        for char in range(1, 256):
            if chr(char) in sc.keys():
                # This is freaking slow.
                rv[chr(char)] = sc[chr(char)]
            else:
                rv[chr(char)] = chr(char)
    return rv


# Convert normal text to html quoted html text. This only applies on the
# 8-bit char set, not 7-bit.
def quote_html(str, special_case=None):
    """This function converts string html to html quotes faster than
    a lightning."""
    import string

    conv_tbl = _get_conv_table(special_case)
    rv = []
    for char in str:
        rv.append(conv_tbl[char])
    return string.join(rv, '')

def quote_html_hack(str):
    from string import join
    conv_tbl = _get_all_conv_table()
    rv = []
    return join([conv_tbl[c] for c in str], '')

def iterate_fs_files(dir, suffix, func):
    """Calls func(filename) for each file in dir ending with suffix."""
    for file in filter(lambda x,s=suffix:x[-(len(s)):]==s,
                       os.listdir(dir)):
        apply(func, (file,))
def iterate_fle_path(dir, suffix, func):
    """Same as iterate_fs_files, but in fle fs directory."""
    iterate_fs_files(os.path.join(file_path, dir), suffix, func)

# Compare two strings.
def str_cmp(x, y):
    from types import StringType
    if (not type(x) is StringType) or (not type(y) is StringType):
        raise 'FLE Error', 'common.str_cmp called with non string arguments: x="%s" y="%s"' % (str(x), str(y))
    x_buf = map(ord, x.lower())
    y_buf = map(ord, y.lower())
    x_len = len(x_buf)
    y_len = len(y_buf)
    tot_len = max(x_len, y_len)
    if x_len < y_len:
        x_buf = x_buf + [0]*tot_len
    elif x_len > y_len:
        y_buf = y_buf + [0]*tot_len
    for (xval, yval) in map(None, x_buf, y_buf):
        if xval < yval: return -1
        elif xval > yval: return 1
    return 0

def convert_to_days(time):
   """Converts a time (in seconds) into days."""
   return int(time/86400) # 24 hours * 60 minutes * 60 seconds

# Intersect two lists, and if there is one equal in both lists,
# return true.
def intersect_bool(seq1, seq2):
    if not seq1 or not seq2:
        return 0
    for x in seq1:
        if x in seq2: return 1
    return 0


# FLE color specs
colours = {
    'red': "#ff0000",
    'green': "#00ff00",
    'blue': "#0000ff",
    'yellow': "#ffff00",
    'black': "#000000",
    'pink': "pink", # WTF is the code for pink?
    'dark_blue': "#0000aa",
    'dark_red': "#aa0000",
    'brown': "brown", # WTF is the code for brown?
    'white': "#ffffff",
}

def week_number(secs):
    """Return the week number (as defined in ISO 8601) for given
    secs (seconds since the epoch)."""
    import strptime
    import time
    from math import ceil

    tuple_current = time.localtime(secs)
    b = time.mktime(strptime.strptime('%d %d %d' % tuple_current[:3],
                                      '%Y %m %d'))

    tuple_year_start = strptime.strptime('%d 1 1' % tuple_current[0],
                                         '%Y %m %d')
    n_days = tuple_year_start[6] + 1
    a = time.mktime(tuple_year_start) - n_days * 24 * 60 * 60

    return int(ceil((b-a) / (7*24*60*60)))

class FakeUpload:
    """A class to mimic an http upload."""
    def __init__(self,name,data,content_type):
        self.filename=name
        self.data=data
        self.headers={}
        if content_type:
            self.headers['content-type']=content_type
        else:
            self.headers['content-type']=None
    def getContentType(self):
        try:
            return self.headers['content-type']
        except KeyError:
            return None
    def read(self,size=-1):
        if size==-1:
            return self.data
        else:
            return self.data[self.offset:(self.offset+size)]
    def seek(self,offset,base=0):
        if base==0:
            self.offset=offset
        elif base==2:
            self.offset=len(self.data)+offset
        elif base==1:
            self.offset=self.offset+offset
    def tell(self):
        return self.offset

import UserDict
class FakeRequest(UserDict.UserDict):
    """A class to mimic an http request."""
    def __init__(self,user='user1'):
        self.AUTHENTICATED_USER = user
        self.RESPONSE=FakeResponse()
        self.data={}
        self.data['SERVER_URL']='http://localhost/'
        self.data['SCRIPT_NAME']='foobar'
        self._script=['foo','bar']
        self.form={}
    def has_key(self,value):
        return 0

class FakeResponse:
    """A class to mimic an http reply."""
    def redirect(self,*args):
        pass


if __name__ == '__main__':
    pass

# EOF

