# $Id: Timer.py,v 1.15 2003/06/13 07:57:11 jmp Exp $
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

__version__ = "$Revision: 1.15 $"[11:-2]

from time import time

class Timer:
    """Timer functionality."""
    def setup_timer(self):
        """Construct timer."""
        self.__callbacks = []
    def add_timer(self, when, func_path, args):
        """Add an timer."""
        import types
        e = {}
        #func_path = list(func_path)
        if not func_path is types.ListType:
            return
            raise 'debug'
        e['func'] = func_path
        e['args'] = args
        e['when'] = when
#        self.__callbacks.append(e)
    def update(self, REQUEST=None):
        """Update the timer state."""
        curr_time = time()
        # This could be optimized so that we have a boolean telling us
        # if there is need to iterate over self.__callbacks. However
        # it would imho hard to produce, so I won't bother yet.
        ilen = len(self.__callbacks)
        for c in self.__callbacks:
            if c['when'] <= curr_time:
                try:
                    # See jack hack, hack jack hack
                    to = self
                    for attr in c['func']:
                        if not hasattr(to, attr):
                            raise 'DEBUG baybee!', 'hasattr(%s, %s)' % (to, attr)
                        to = getattr(to, attr)
                    # Hopefully to is now something clever
                    apply(to, c['args'])
                finally:
                    self.__callbacks.remove(c)
                # On exception we just have to wait until the next update
                # update call.
        if REQUEST:
            # TODO: i18n
            return self.message_dialog(
                self, REQUEST,
                title='Update called',
                message='Update called (%d %d)' % (ilen, len(self.__callbacks)),
                action='index_html')

# EOF
