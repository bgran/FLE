# $Id: JamSessionLinearOrTree.py,v 1.3 2003/06/13 07:57:11 jmp Exp $

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

__version__ = '$Revision: 1.3 $'[11:-2]

import Globals

"""Simple two dimensional table."""
class table:
    def __init__(self, empty_val):
        self._t = []
        self._w = 0
        self._h = 0
        self._empty_val = empty_val

    def get_repr(self):
        return self._t

    def get_width(self):
        return self._w

    def get_height(self):
        return self._h

    def set(self, x, y, data):
        if y >= self._h:
            for i in range(y - self._h + 1):
                self._t.append([self._empty_val] * self._w)
            self._h = y + 1

        if x >= self._w:
            for i in range(self._h):
                for j in range(x - self._w + 1):
                    self._t[i].append(self._empty_val)
            self._w = x + 1

        self._t[y][x] = data

    def get(self, x, y):
        return self._t[y][x]

    def debug_print(self):
        for row in self._t:
            for data in row:
                print data,
            print

class JamSessionLinearOrTree:
    """JamSessionLinearOrTree"""

    def build_tree(self, root_artefact):
        return {'artefact_id': root_artefact.get_id(),
                'children': [self.build_tree(x) for x in \
                             root_artefact.get_children_artefacts()]
                }

    # Render tree depth first, from left to right.
    # The letters in 'ns', 'nes', 'esw', 'ew', 'sw' correspond
    # to north, east, south, and west.
    def table_render_tree(self, tree, table, x, y):
        """Render table into table"""

        # Render this node...
        table.set(x-1, y, ('_selection', tree['artefact_id']))
        table.set(x, y, ('artefact', tree['artefact_id']))
        ret_dim_info = [x]

        # .. and then all of its children, from left to right.
        if len(tree['children']) > 0:
            table.set(x, y+1, ('ns', None)) # may be modified later

            # leftmost child
            dim_info = \
                     self.table_render_tree(tree['children'][0], table, x, y+2)

            for d in dim_info:
                ret_dim_info.append(d)

            # the rest of children
            for node in tree['children'][1:]:

                # Figure out horizontal position for this node.
                m = x
                for i in range(self.left_depth(node)):
                    try: m = max(m, dim_info[i])
                    except IndexError: break # current branch deeper

                # Draw stuff between left sibling (of this node) and this node.
                sx = ret_dim_info[1]
                if sx == x:
                    table.set(sx, y+1, ('nes', None))
                else:
                    table.set(sx, y+1, ('esw', None))
                for i in range(sx+1, m+2):
                    table.set(i, y+1, ('ew', None))
                table.set(m+2, y+1, ('sw', None))

                # Draw recursively this node.
                dim_info = self.table_render_tree(node, table, m+2, y+2)

                # Update red_dim_info.
                for i in range(len(dim_info)):
                    try:
                        ret_dim_info[i+1] = max(ret_dim_info[i+1], dim_info[i])
                    except IndexError:
                        ret_dim_info.append(dim_info[i])

        return ret_dim_info

    def left_depth(self, node):
        if len(node['children']) > 0:
            return self.left_depth(node['children'][0]) + 1
        else:
            return 1


Globals.default__class_init__(JamSessionLinearOrTree)
