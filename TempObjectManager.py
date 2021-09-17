# $Id: TempObjectManager.py,v 1.42 2003/06/13 07:57:11 jmp Exp $
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

"""Contains class TempObjectManager, which is subclassed by classes
that need to be able to store temporary objects inside them."""

__version__ = "$Revision: 1.42 $"[11:-2]

from Globals import Persistent, Acquisition
import OFS, AccessControl

from TraversableWrapper import TraversableWrapper, TWFolder
from common import reload_dtml, add_dtml
from ITempObjectManager import ITempObjectManager

# This is a new, improved version of the TempObjectManager.
# It has more powerful methods, so using it is easier.
#
# This class is used by inheriting in into the objects that
# should be able to handle temporary objects.
#
# When objects are stored in the tmp_objects subfolder, the
# folder creates unique temporary IDs to reference them.
# The objects' real ids (accessible through their "id" attribute
# stay intact.
class TempObjectManager(OFS.SimpleItem.Item):
    """Temp object manager."""

    __implements__ = ITempObjectManager
    security = AccessControl.ClassSecurityInfo()

    def __init__(self):
        """Create TempObjectManager."""
        pass

    def __has_tmp(self):
        return hasattr(self.aq_base,'tmp_objects')

    # Access method to the temporary object storage. Will create
    # the storage on the fly if necessary.
    def __get_tmp(self):
        """Creates the tmp_objects subfolder (of type TWFolder)
        if it does not already exist."""
        if not self.__has_tmp():
            f = TWFolder()
            f.id = 'tmp_objects'
            f.title = 'Temporary objects'
            self._setObject('tmp_objects', f)
        return self.tmp_objects

    def get_tmp_items(self):
        if not self.__has_tmp():
            return ()
        return self.__get_tmp().objectItems()

    security.declarePrivate('get_tmp_objects')
    def get_tmp_objects(self):
        """Return list of temporary objects."""
        if not self.__has_tmp():
            return ()
        return self.__get_tmp().objectValues()

    security.declarePrivate('get_tmp_object_ids')
    # retval: [toid1, toid2, toid3, ...]
    def get_tmp_object_ids(self):
        """Return list of temporary object ids."""
        if not self.__has_tmp():
            return ()
        return self.__get_tmp().objectIds()

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        pass

    security.declarePrivate('is_in_tmp')
    def is_in_tmp(self,ob_ref):
        """Return whether the given object is a temporary object
        under this TempObjectManager or not."""
        if not self.__has_tmp():
            return 0
        return ob_ref in self.__get_tmp().objectValues()

    def get_path_to(self,ob_ref):
        if self.is_in_tmp(ob_ref):
            return "tmp_objects/" + self.get_tmp_id(ob_ref)
        else:
            return ob_ref.get_id()

    security.declarePrivate('move_to_tmp')
    def move_to_tmp(self, ob_ref):
        """Move given object from this folder into the tmp_objects
        subfolder."""
        self._delObject(ob_ref.get_id())
        return self.add_tmp_object(ob_ref)

    security.declarePrivate('move_from_tmp')
    def move_from_tmp(self, ob_ref):
        """Move given object from the tmp_objects subfolder
        into this folder."""
        items = self.get_tmp_items()
        for item in items:
            if item[1]==ob_ref:
                self.remove_tmp_object(item[0])
                self._setObject(ob_ref.id, ob_ref)
                return

    security.declarePrivate('delete_from_tmp')
    def delete_from_tmp(self, ob_ref):
        """Remove given object from the tmp_object subfolder."""
        items = self.get_tmp_items()
        for item in items:
            if item[1]==ob_ref:
                self.remove_tmp_object(item[0])
                return

    security.declarePrivate('add_tmp_object')
    def add_tmp_object(self, ob_ref):
        """Store given object as a temp object and return temporary
        object id."""

        if not hasattr(self,'_tmp_oid'):
            self._tmp_oid = 0     # for unique temporary object id
        # get new oid
        toid = 'tmp' + str(self._tmp_oid)
        self._tmp_oid += 1

        self.__get_tmp()._setObject(toid, ob_ref)
        return toid

    security.declarePrivate('get_tmp_object')
    def get_tmp_object(self, toid):
        """Return reference to given (id) temporary object."""
        if not self.__has_tmp(): return None
        return self.__get_tmp()._getOb(toid)

    security.declarePrivate('get_object_even_if_tmp')
    def get_object_even_if_tmp(self, realid):
        """Return reference to given object, which is located by its real id.
        First check current folder, then tmp_objects."""
        try:
            return self.get_child(realid)
        except AttributeError:
            for (id,obj) in self.get_tmp_items():
                if realid == obj.get_id():
                    return obj
        raise AttributeError(realid)


    security.declarePrivate('get_tmp_id')
    def get_tmp_id(self,ob_ref):
        """Returns the temporary ID that the TempObjectManager has
        for the given object. If the object is not this manager's
        temp object, returns None."""
        for tid in self.get_tmp_object_ids():
            if self.get_tmp_object(tid) == ob_ref:
                return tid

    security.declarePrivate('remove_tmp_object')
    def remove_tmp_object(self, toid):
        """Remove given (id) temporary object entirely."""
        retval = self.get_tmp_object(toid)
        if retval:
            self.tmp_objects._delObject(toid)

        return retval

    security.declarePrivate('get_tmp_object_real_ids')
    # These are the ids the objects themselves have, not
    # the ids by which they can be accesses from the
    # tmp_objects folder.
    def get_tmp_object_real_ids(self):
        """Return list of temporary object real ids."""
        if not self.__has_tmp():
            return ()
        return [e.get_id() for e in self.tmp_objects.objectValues()]

# EOF


