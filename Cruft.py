# $Id: Cruft.py,v 1.37 2004/12/13 22:58:49 tarmo Exp $
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

"""Contains class Cruft, which is used as a placeholder for miscellaneous utility functions that many objects need."""

__version__ = "$Revision: 1.37 $"[11:-2]

import re

from AccessControl import ClassSecurityInfo
from urllib import quote
from string import rfind

import common

class Cruft:
    """Class containing miscellaneous methods that are
    historical baggage, but possible be gotten rid of, or
    at least implemented differently or somewhere else."""
    security = ClassSecurityInfo()

    def x(self):
        """..."""
        for i in self.aq_chain:
            if hasattr(i,'id'):
                print i.id
            else:
                print i

    # Make sure this method is called from the context of the original
    # object that was called with REQUEST.URL1. If you're in a dtml-with
    # or something, the URL and self are not in sync.
    security.declarePublic('find_URL_of_fle_root')
    def find_URL_of_fle_root(self, REQUEST):
        """Return URL of our FLE installation."""
        import FLE
        obj = self
        while not isinstance(obj, FLE.FLE):
            obj = obj.aq_inner.aq_parent
        return obj.absolute_url()

    def find_URL_of_user_info(self, REQUEST):
        """Return URL of UserInfo."""
        import UserInfo
        obj = self
        while not isinstance(obj, UserInfo.UserInfo):
            obj = obj.parent()
        return obj.absolute_url()


    security.declarePublic('find_URL_of_webtop')
    def find_URL_of_webtop(self, REQUEST):
        """Return URL of Webtop."""
        import Webtop
        obj = self
        while not isinstance(obj, Webtop.Webtop):
            obj = obj.parent()
        return obj.absolute_url()

    security.declarePublic('find_URL_of_group_folder')
    def find_URL_of_group_folder(self, REQUEST):
        """Return URL of toplevel group folder or group folder proxy."""
        import GroupFolder
        import GroupFolderProxy
        url = REQUEST.URL1
        obj = self
        url = self.get_url_to_object(self)[:-1]
        while 1:
            if isinstance(obj, GroupFolderProxy.GroupFolderProxy):
                return obj.absolute_url()
            if isinstance(obj, GroupFolder.GroupFolder):
                return obj.absolute_url()
            obj = obj.parent()
        return obj.absolute_url()

    security.declarePublic('find_URL_of_thread_start_node')
    def find_URL_of_thread_start_node(self, REQUEST):
        """Return URL of starting note."""
        import CourseContext
        obj = self
        while not isinstance(obj.parent(), CourseContext.CourseContext):
            obj = obj.parent()
        return obj.absolute_url()

    security.declarePublic('find_URL_of_course')
    def find_URL_of_course(self, REQUEST):
        """Return URL of starting note."""
        obj = self
        while not obj.meta_type == 'Course':
            obj = obj.parent()
        return obj.absolute_url()

    security.declarePublic('find_URL_of_course_context')
    def find_URL_of_course_context(self, REQUEST):
        """Return URL of starting note."""
        import CourseContext
        obj = self
        while not isinstance(obj, CourseContext.CourseContext):
            obj = obj.parent()
        return obj.absolute_url()

    security.declarePublic('get_current_user')
    def get_current_user(self, REQUEST):
        """Extract current user's name from the REQUEST object."""
        return str(REQUEST.AUTHENTICATED_USER)

    security.declarePublic('get_current_user_info_obj')
    def get_current_user_info_obj(self, REQUEST):
        """Extract current user's UserInfo object"""
        return self.fle_users.get_user_info(str(REQUEST.AUTHENTICATED_USER))

    security.declarePublic('uname_to_nickname')
    def uname_to_nickname(self, uname):
        return self.fle_users.get_user_info(uname).get_nickname()

    security.declarePublic('urlquote')
    def urlquote(self, text):
        """urlquote given text."""
        return quote(text)

    def get_url_to_object(self,obj):
        # Make a list of parents without the Application object
        # (from obj to FLE)
        objs = obj.aq_inner.aq_chain[:-1]
        objs.reverse()
        path='/'.join([x.getId() for x in objs])+'/'
        return path

    def get_object_of_url(self,url,base):
        path=url.split('/')
        path.pop() # remove last entry
        path.reverse()
        if path[-1]=='http:':  # remove protocol
            path.pop()
            path.pop()
        path.pop() # remove first (root) entry
        # Start locating the object starting from the current object
        obj = base
        # See if we have a course id in the URL
        try:
            course_id = path[path.index('courses') - 1]
        except ValueError:
            course_id = None
        #raise 'foo','%s, %s, %s' % (repr(obj.objectIds()), course_id, repr(path))
        try:
            first_found = 0
            while path:
                oname = path.pop()
                if obj.meta_type == 'GroupFolderProxy':
                    obj = obj.lame_getattr_emulation(oname).__of__(obj)
                else:
                    # Try to locate next object in path.
                    try:
                        obj = getattr(obj,oname).__of__(obj)
                        first_found = 1
                    except:
                        # If we fail and we haven't located the first
                        # object yet, it may be because the URL contains
                        # virtual directories that have no match in Zope.
                        # So we'll just ignore that path portion and try again.
                        if not first_found:
                            pass
                        else:
                            raise
            return obj
        except:
            
            if course_id and course_id not in [x.get_id() for x in self.courses.get_children('Course')]:
                # We think that we have a link inside course but that
                # has been removed -> fail silently.
                return None
            else:
                raise 'FLE Error', \
                      'Internal link error, object not found %s - %s' \
                      % (str(obj), oname)

    def set_undefined_page(self, message, REQUEST):
        """Set REQUEST.RESPONSE.redirect, so that we go to undefined page
        and give an explanation."""
        message = common.quote_html_hack(message)
        REQUEST.RESPONSE.redirect(self.state_href(REQUEST,
            "undefined_page?explanation=%s" % message))

    security.declarePublic('to_str_list')
    # Using eval would be simpler and more general, but
    # we want to be paranoid.
    def to_str_list(self, s):
        """Reverse str representation of list of strings back to list."""
        return [x.strip() for x in s[1:-1].replace("'", "").split(',')]


    security.declarePublic('remove_state_url')
    def remove_state_url(self, url):
        """Remove state_url from URL"""
        return re.compile('[&\?]state_url=[^\&]*').sub('', url)

    security.declarePublic('remove_duplicates_from_url')
    def remove_duplicates_from_url(self, url):
        """Remove duplicate parameteres (and state_url) from URL"""
        if '&' not in url: return url

        a = []
        try:
            retval, parameters = url.split('?')
        except:
            raise 'foo', url.split('&')

        if parameters:
            for s in parameters.split('&'):
                if not s: continue
                name, value = s.split('=')
                if name != 'state_url':
                    try:
                        # If an old value exists -> overwrite it.
                        a[[t[0] for t in a].index(name)] = (name, value)
                    except ValueError:
                        a.append((name, value))

        if len(a):
            for name, value in a:
                retval += '&' + name + '=' + value
            index = retval.index('&')
            retval = retval[:index] + '?' + retval[index+1:]

        return retval

    security.declarePublic('remove_from_url')
    def remove_from_url(self, url, paremeteres_to_remove):
        """Remove given parameters from url."""

        a = []
        try:
            retval, parameters = url.split('?')
        except ValueError:
            return url

        if parameters:
            for s in parameters.split('&'):
                name, value = s.split('=')
                if name not in paremeteres_to_remove:
                    a.append((name, value))

        if len(a):
            for name, value in a:
                retval += '&' + name + '=' + value
            index = retval.index('&')
            retval = retval[:index] + '?' + retval[index+1:]

        return retval

# EOF
