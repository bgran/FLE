# $Id: MaptoolInterface.py,v 1.4 2003/06/13 07:57:11 jmp Exp $
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

"""Contains class MaptoolInterface, which contains methods that the
synchronous Maptool utility calls as needed."""

__version__ = "$Revision: 1.4 $"[11:-2]
import Globals
from AccessControl import ClassSecurityInfo
from common import perm_view, perm_edit, perm_manage, perm_add_lo
from WebtopFile import WebtopFile

class MaptoolInterface:
    """Interface methods for the Maptool utility."""
    meta_type = 'MaptoolInterface'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    def __get_course(self,id):
        return getattr(self.courses,id)

    def __get_folder(self,id):
        return self.__get_course(id).gf

    def __has_access(self,id):
        if not hasattr(self.courses,id):
            return 0
        if self.get_uname() in self.__get_course(id).get_all_users_id():
            return 1
        else:
            return 0

    security.declareProtected(perm_view, 'is_in_session')
    def is_in_session(self,session,REQUEST=None):
        """Checks if a user is active in a session."""
        if not hasattr(self,"maptool_sessions"):
            return 0
        return session in self.maptool_sessions

    security.declareProtected(perm_edit, 'maptool_join')
    def maptool_join(self, session, REQUEST=None):
        """Notifies the system that this user has joined a session."""
        if not self.__has_access(session):
            return 0
        if not hasattr(self,"maptool_sessions"):
            self.maptool_sessions=[]
        if not session in self.maptool_sessions:
            self.maptool_sessions.append(session)
        return 1

    security.declareProtected(perm_edit, 'maptool_leave')
    def maptool_leave(self, session, REQUEST=None):
        """Notifies the system that this user has left a session."""
        if hasattr(self,"maptool_sessions") and session in self.maptool_sessions:
            ndx=self.maptool_sessions.index(session)
            self.maptool_sessions=self.maptool_sessions[:ndx] + \
                                   self.maptool_sessions[ndx+1:]
        return 1

    security.declareProtected(perm_edit, 'maptool_save')
    def maptool_save(self, session, txt, map, img, REQUEST=None):
        """Request to store a maptool session."""
        if not self.__has_access(session):
            return 0

	# set a fake request up
        from common import FakeRequest
	uname = self.get_uname()
        req = FakeRequest(uname)
        
	# put fake request into group folder's acquisition chain
	# because ZODB needs the SERVER_URL key for indexing objects
        from ZPublisher.BaseRequest import RequestContainer
        rc = RequestContainer(REQUEST=req)
        gf = self.__get_folder(session)
        gfr = gf.__of__(rc)

        # some info for storing the files
        obj_ids = ['maptool_chat', 'maptool_map', 'maptool_image']
        files = [txt, map, img]
        mimetypes = ['text/plain', 'application/x-maptool', 'image/jpeg']
       
        for ndx in range(3):
            id, file, mime = obj_ids[ndx], files[ndx], mimetypes[ndx]

            # create webtop file
	    f = WebtopFile(gfr, id, file)
	    # use always the same id (dirty trick! IDEA: MaptoolFile...)
	    f.id = id
	    f.content_type = mime

	    # delete file from group folder if it already exists
            try:
                gfr._delObject(f.id)
            except AttributeError:
                pass
            
	    # store file in group folder with 
	    gfr._setObject(f.id, f)

        return 1

    security.declareProtected(perm_edit, 'maptool_get')
    def maptool_get(self, session, REQUEST=None):
        """Request to retrieve a maptool session."""
        if not self.__has_access(session):
            return 0

        return self.__get_folder(session).maptool_map

    security.declareProtected(perm_edit, 'maptool_list')
    def maptool_list(self, REQUEST=None):
        """Request a list of available sessions the user has access to."""
        # TODO
        sessions=[]
        for c in self.user_courses():
            if hasattr(c,'gf') and hasattr(c.gf,'maptool_map'):
                sessions.append(c.get_id())
        return sessions

Globals.InitializeClass(MaptoolInterface)

# EOF
