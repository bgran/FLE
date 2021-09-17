# $Id: ITempObjectManager.py,v 1.9 2003/06/13 07:57:11 jmp Exp $
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

"""Contains an interface for TempObjectManager."""

__version__ = "$Revision: 1.9 $"[11:-2]

from Interface import Base

class ITempObjectManager(Base):
    """Interface for TempObjectManater"""

    def add_tmp_object(self, ob_ref):
        """Store given object as a temp object."""

    def get_tmp_object(self, toid):
        """Return reference to given (id) temporary object."""

    def remove_tmp_object(self, toid):
        """Remove given (id) temporary object."""

    # retval: [toid1, toid2, toid3, ...]
    def get_tmp_object_ids(self):
        """Return list of temporary object ids."""

# EOF
