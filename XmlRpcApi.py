# $Id: XmlRpcApi.py,v 1.4 2003/06/13 07:57:12 jmp Exp $
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

"""API for XML-RPC. Current version is just a draft for doing some
client side tests. Suppose that everything will change."""

import Globals

class XmlRpcApi:
    """A very simple XML-RPC API."""
    def xmlrpc_get_children_ids(self, types=None):
        """Return ids of children of given type."""
        if types:
            return self.objectIds(types)
        else:
            return self.objectIds()

    # Please override.
    def xmlrpc_get_data(self):
        """Return all data in a dictionary."""
        return {}


Globals.default__class_init__(XmlRpcApi)

class CourseManagerXMLRPC(XmlRpcApi):
    """A very simple XML-RPC API."""

Globals.default__class_init__(CourseManagerXMLRPC)

class CourseXMLRPC(XmlRpcApi):
    """A very simple XML-RPC API."""
    def xmlrpc_get_data(self):
        """Return all data in a dictionary."""

        retval = {}
        for x in ('name', 'organisation', 'description', 'methods',
                  'starting_date', 'ending_date'):
            retval[x] = \
                      getattr(self, '_' + self.__class__.__name__+ '__%s' % x)

        return retval

Globals.default__class_init__(CourseXMLRPC)

class CourseContextXMLRPC(XmlRpcApi):
    """A very simple XML-RPC API."""
    def xmlrpc_get_data(self):
        """Return all data in a dictionary."""

        retval = {}
        for x in ('name', 'description', 'author', 'tt_set_id'):
            retval[x] = getattr(self, x)

        return retval

Globals.default__class_init__(CourseContextXMLRPC)

class NoteXMLRPC(XmlRpcApi):
    """A very simple XML-RPC API."""
    def xmlrpc_get_data(self):
        """Return all data in a dictionary."""

        retval = {}
        for x in ('creation_time','body', 'subject', 'author',
                  'url', 'url_name'):
            retval[x] = eval('self.get_%s()' % x)

        return retval

Globals.default__class_init__(NoteXMLRPC)

class UserManagerXMLRPC(XmlRpcApi):
    """A very simple XML-RPC API."""
    def xmlrpc_get_data(self):
        """Return all data in a dictionary."""

        retval = {}
        return retval

Globals.default__class_init__(UserManagerXMLRPC)

class UserInfoXMLRPC(XmlRpcApi):
    """A very simple XML-RPC API."""
    def xmlrpc_get_data(self):
        """Return all data in a dictionary."""

        retval = {}
        for x in ('language', 'uname', 'first_name', 'last_name',
                  'email', 'group', 'address1', 'address2', 'homepage',
                  'phone', 'gsm', 'quote', 'background',
                  'personal_interests', 'professional_interests',
                  'organization', 'city'):
            retval[x] = eval('self.get_%s()' % x)

        return retval

Globals.default__class_init__(UserInfoXMLRPC)
