# $Id: JamSessionLinear.py,v 1.2 2003/06/13 07:57:11 jmp Exp $

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

__version__ = '$Revision: 1.2 $'[11:-2]

import Globals
from AccessControl import ClassSecurityInfo

from JamSessionLinearOrTree import table
from JamSessionLinearOrTree import JamSessionLinearOrTree
from JamSession import JamSession
from common import perm_view, perm_edit, perm_manage, perm_add_lo

class JamSessionLinear(
    JamSession,
    JamSessionLinearOrTree,
    ):
    """JamSessionLinear"""

    meta_type = 'JamSession'
    security= ClassSecurityInfo()
    security.declareObjectPublic()

    security.declareProtected(perm_view, 'get_type')
    def get_type(self):
        """Return type of the JamSession."""
        return 'linear'

    security.declareProtected(perm_view, 'get_printable_type')
    def get_printable_type(self, REQUEST):
        """Return printable (localized) type of the JamSession."""
        return REQUEST['L_mutate_on_previous']

    security.declarePrivate(perm_view, 'update_drawing')
    def update_drawing(self):
        tree = self.build_tree(self.get_children('JamArtefact')[0])

        t = table(('empty',None))
        self.table_render_tree(tree, t, 1, 0)

        for y in range(t.get_height()-2):
            if t.get(0, y)[0] == '_selection':
                t.set(0, y, ('empty', None))

        self.drawing = t.get_repr()


Globals.default__class_init__(JamSessionLinear)
