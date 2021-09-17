# $Id: TraversableWrapper.py,v 1.59 2003/06/13 07:57:11 jmp Exp $
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

"""Contains classes to facilitate traversing the acquisition tree.
Class TraversableWrapper is the old implementation used in
knowledge building and class Traversable is the new implementation
used in webtop. Also contains the utility class TWFolder."""

__version__ = "$Revision: 1.59 $"[11:-2]

import time
import common

from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from Globals import Acquisition
import Globals, OFS
#import FLE
from types import NoneType, ClassType,\
     ListType, TupleType, StringType

# Don't subclass Acquisition.Implicit, but rather TraversableWrapper.
#
# - find_class_obj traverses the object hierarchy from down upwards (i.e.
# from child to parent), and returns the first object that is an instance
# of the argument given to find_class_obj.
#
# [FooClass]
#    |
#   [BarClass]
#      |
#     [BarClass] ------------------------------------.
#        |                                           |
#       [SpamClass]                                  |
#          |                                         |
#         [SpamClass]                                |
#          -call to self.find_class_obj(BarClass) <--'
#
# This way you will not have to bind any references to parent classes
# you might want to use later. On a sidenote, this is actually only
# usefull to fetch some of the manager stuff (because there usually is
# only *one* UserManager/CourseManager, etc.).
# And as always, if you have a note object hierarchy that is deeper than
# some 999 messages, you are in trouble due to the recursive nature of
# parent traversal, and pythons lack of tail-recursion removal.
#
# - parent returns the parent object of self. This way you will not have
# to bind the parent object to self.
#
# This class is abstract! This is not supposed to work without
# security thing in a child class.
class TraversableWrapper(Acquisition.Implicit):
    """TraversableWrapper is a helper class that should be inherited
    into all objects in a subtree where this functionality is needed.
    This class mainly facilitates traversing up or down the
    containment hierarchy, but contains some miscellaneous methods as well."""
    security = ClassSecurityInfo()

    security.declarePublic('parent')
    def parent(self):
        return self.aq_inner.aq_parent

    security.declarePublic('find_class_obj')
    def find_class_obj(self, c_type):
        if isinstance(self, c_type):
            return self
        return self.parent().find_class_obj(c_type)

    security.declarePublic('fle_root')
    def fle_root(self):
        import FLE
        return self.find_class_obj(FLE.FLE)

    security.declarePublic('find_thread')
    def find_thread(self):
        import Thread
        return self.find_class_obj(Thread.Thread)

    security.declarePublic('find_course_context')
    def find_course_context(self):
        """Return CourseContext object."""
        import CourseContext
        return self.find_class_obj(CourseContext.CourseContext)

    # NOTE: This method must be called from some Note object
    # NOTE: _under_ CourseContext object.
    security.declarePublic('find_thread_start_node')
    def find_thread_start_node(self):
        """Return Note object."""
        import CourseContext

        obj = self
        while 1:
            parent = obj.parent()
            if isinstance(parent, CourseContext.CourseContext):
                return obj
            else:
                obj = parent
        raise 'FLE Error', 'Notreached'

    security.declarePublic('find_course')
    def find_course(self):
        """Return Course object."""
        import Course
        try:
            return self.find_class_obj(Course.Course)
        except AttributeError:
            # Hopefully this happened because we are inside
            # GroupFolderProxy inside user's Webtop: figure
            # out the course it is proxy for.
            return self.get_course_this_belongs_to()

    security.declarePublic('find_coursemanager')
    def find_coursemanager(self):
        """Return Course Manager object from downstream."""
        from CourseManager import CourseManager
        return self.find_class_obj(CourseManager)

    security.declarePublic('is_course_context')
    def is_course_context(self):
        """Return whether self is an instance of CourseContext."""
        import CourseContext
        return isinstance(self, CourseContext.CourseContext)

    security.declarePublic('obj_path')
    def obj_path(self, class_type):
        """Returns the path as a list from object down to the first
        class_type object that comes in sight.
        Ex. ['courses', '1', '45', '778']"""
        rv = []
        if isinstance(self, class_type):
            return []
        return self.parent().obj_path(class_type) + [self.id]

    security.declarePublic('obj_path_course_context')
    def obj_path_course_context(self):
        """Returns a list path thingy to the next course context downstream."""
        from CourseContext import CourseContext
        return self.obj_path(CourseContext)

    security.declarePublic('ret_self')
    def ret_self(self):
        """Return self object."""
        return self

    # Added code to handle the propable cause of ZCatalog stuff.
    def __get_children(self, _meta_t):
        """Returns a list of children (object references). If _meta_t
        is described, then only such things are returned."""
        _type_t = type(_meta_t)
        if _type_t is NoneType:
            return apply(self.objectValues, ())
        elif _type_t in (ListType, TupleType, StringType):
            return apply(self.objectValues, (_meta_t,))
        elif _type_t is ClassType:
            """Special case of classtype."""
            rv = []
            for child in self.__get_children():
                if isinstance(child, _meta_t): rv.append(child)
            return rv
        else:
            raise 'FLE Error', 'Unknown type to get_children! (%s)' % str(_meta_t)[1:-1]

    security.declarePublic('get_children')
    def get_children(self, _meta_t):
        """Wrapper around ObjectManager.objectValues."""
        return self.objectValues(_meta_t)

    #def get_children(self, _meta_t=None):
    #    """Wrap __get_children. This is to make usage of ZCatalog, or
    #    something like that."""
    #    return self.__get_children(_meta_t)

    def __get_child(self, _id):
        """Returns child with id _id."""
        return self._getOb(_id)

    security.declarePublic('get_child')
    def get_child(self, _id):
        """Wraps __get_child. So that if we want to do some magic with
        those ZCatalogs, then this might be a good idea."""
        return self.__get_child(_id)

    def get_id(self):
        """Return object id."""
        return self.id

    security.declarePublic('get_meta_type')
    def get_meta_type(self):
        """Return objects meta type"""
        return self.meta_type

    # Identical to Zope's standard absolute_url() excepts
    # that this handles our temporary objetcs as well (but
    # not objects inside objects inside tmp_objects!)
    def hack_absolute_url(self):
        """Return absolute url."""
        id_real = self.get_id()
        url = self.absolute_url()

        for id_parent in self.parent().objectIds():
            if self.parent().get_child(id_parent).get_id() == id_real:
                if id_real == id_parent:
                    return url
                else:
                    url_parts = url.split('/')
                    url_parts[-1] = id_parent
                    return '/'.join(url_parts)


    # Keep public, because all dtmls call this and some need to be
    # publicly available.
    def update_user_state(self, REQUEST):
        """Update active member list, on users active course."""

        fle_users = self.fle_users
        try:
            user = str(REQUEST.AUTHENTICATED_USER)
            u_obj = fle_users.get_user_info(user)
        except:
            # If the logged in user is not an FLE user, just bail out.
            return

        try:
            crs_id = self.find_course().get_id()
            course = self.courses.get_child(crs_id)
        except AttributeError: # User is currenly on a page outside any course
            return

        act_list = course.active_memb_cache
        nlist = []

        # Update user activity.
        u_obj.update_active(crs_id)

        # Timeout inactive members.
        # FIXME: write test that puts invalid user entries in act_list.
        time_now = time.time()
        for u in [fle_users.get_user_info(x) for x in act_list]:
            # Check if user has timeouted. NB hardcoded timeout value.
            if (time_now - u.last_active(crs_id)) < common.user_timeout_delay:
                # Nope. No timeout.
                nlist.append(u.get_id())
        # Finally add user to active list if she is not already there.
        if user not in nlist:
            nlist.append(user)
        course.active_memb_cache = nlist
        course._p_changed = 1

Globals.InitializeClass(TraversableWrapper)

class Traversable(TraversableWrapper):
    """This is a stripped down version of TraversableWrapper, with
    many miscellaneous methods removed and some new ones added.
    This is used in the webtops."""
    # This is the wrong place to add this in! -granbo
    security = ClassSecurityInfo()

    def ret_self(self):
        """Returns a reference to self. Useful in dtml when a
        specific reference is needed."""
        return self

    def __build_path_upwards(self, count):
        """Returns a url portion representing an upwards
        traverse of a certain number of levels. Append to this
        the """
        if count == 0:
            return './'
        else:
            return count * '../'

    security.declarePublic('list_parents')
    def list_parents(self, top_id,count=0):
        """List parents of current item. Returns a list containing
        pairs of (object,relative_path)."""
        if self.id==top_id:
            return [ (self, self.__build_path_upwards(count)), ]
        return self.parent().list_parents(top_id, count+1) + \
               [ (self, self.__build_path_upwards(count)), ]

    security.declarePublic('list_parents_to_top')
    def list_parents_to_top(self, count=0):
        """List parents of current item. Returns a list containing
        pairs of (object,relative_path)."""
        if hasattr(self.aq_base,'toplevel'):
            return [ (self, self.__build_path_upwards(count)), ]
        return self.parent().list_parents_to_top(count+1) + \
               [ (self, self.__build_path_upwards(count)), ]

    def delete_me(self):
        """Removes this object. This method works even if the ID
        stored in this object differs from the object ID used
        in the parent folder (as is the case in webtop)."""
        self.aq_parent._delObject(self.find_id_used_in_parent(self))

    def find_id_used_in_parent(self,objref):
        """Returns the ID the parent folder uses for this object."""
        contents = objref.aq_parent.objectItems()
        for i in contents:
            if i[1]==objref:
                return i[0]

    def map_ids_to_objects(self,item_ids):
        """Returns a list of object references for the given
        id list. Does not recurse into subfolders."""
        objs = []
        for item_id in item_ids:
            objs.append(self._getOb(item_id))
        return objs

    # This is a recursive method that descends the entire
    # subtree in depth-first, in-order traverse. Only
    # branches that have this method are traversed, so effectively
    # only Traversable branches are checked.
    def find_object_by_id(self,item_id):
        """Locate an object from the containment subtree
        by its id (not the id stored in the container, but its
        own id attribute)."""
        if self.id==item_id:
            return self

        for item in self.objectValues():
            # Check that 'item' _really_ has the method
            # find_object_by_id. Using 'aq_base' strips all the
            # containers from the object's namespace.
            if hasattr(item.aq_base,'find_object_by_id'):
                # DON'T USE aq_base HERE! It won't just limit
                # the namespace, but the resulting object found
                # will also be without its containers. And we
                # need the containers for object identity.
                retval = item.find_object_by_id(item_id)
                if retval:
                    return retval


    def get_printable_day(self, timestamp,REQUEST):
        """Return date in a human readable format."""
        from common import convert_to_days
        import time
        current_day = convert_to_days(time.time())
        day = convert_to_days(timestamp)
        if current_day == day:
            return REQUEST["L_today"]
        elif current_day-1 == day:
            return REQUEST["L_yesterday"]
        else:
            return time.strftime(
                REQUEST["L_short_date_format"],
                #"%a, %d %b %Y",
                time.localtime(day*86400))

    def get_printable_time(self, timestamp,REQUEST):
        """Return time specified in the parameter
        in a human readable format."""
        from time import localtime, strftime
        return strftime(
            REQUEST['L_timestamp_format'],
            #"%H:%M:%S %a, %d %b %Y",
            localtime(timestamp))

    def get_printable_current_time(self,REQUEST):
        """Return current time in a human readable format."""
        from time import time
        return self.get_printable_time(time(),REQUEST)

    # See get_printable_day() for exact format in which date is returned.
    def get_printable_current_date(self, REQUEST):
        """Return current date in a human readable format."""
        from time import time
        return self.get_printable_day(time(),REQUEST)

    def check_permission(self, permission):
        """Check whether the security context allows the given
        permission on self."""
        return getSecurityManager().checkPermission(permission, self)

Globals.InitializeClass(Traversable)

class TWFolder(
    OFS.Folder.Folder,
    Traversable):
    """A simple class that inherits from Traversable and Folder.
    This is used in Webtop when we need folders that are Traversable,
    but aren't WebtopItems (and thus visible in the webtop).
    For example: tmp_objects folders containing trashed items."""
    pass

Globals.InitializeClass(TWFolder)

# EOF
