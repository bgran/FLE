# $Id: State.py,v 1.30 2003/06/13 07:57:11 jmp Exp $

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

"""This module contains the State class, which is responsible for storing state information in the URL.


Currently the format is something like:

4,11spamhello world3,3foo1,2

meaning:
spam = 'hello world' (string)
foo = ['1','2'] (list)

Note that string does not contain any information which
variable are strings and which are lists... it depends
which functions you use to access them.
"""

import types
import re
from string import atoi
from string import join
import urllib

# Note: Class State does not have any state ;-) (just methods...)
# TODO: More documentation for this class.
class State:
    """State"""

    # This is the only method that modifies REQUEST.
    def state_set_state_in_request(self, REQUEST, state):
        """Set state in REQUEST."""
        REQUEST.set('state_url', state)

    # This is the only method that returns state string.
    # (At the moment there is no state_set_string() as
    #  we don't need it.)
    def state_set_list(self, REQUEST, name, value):
        """Set list in a state, return new state string."""
        state = self.__state_from_request(REQUEST)
        d = self.__state_string_to_dict(state)
        d[name] = join(value, ',')
        return self.__dict_to_state_string(d)

    def state_get_string(self, REQUEST, name):
        """Return value for given string variable."""
        state = self.__state_from_request(REQUEST)
        try:
            d = self.__state_string_to_dict(state)
            return d[name]
        except:
            return ''

    def state_get_list(self, REQUEST, name):
        """Return value for given string variable."""
        state = self.__state_from_request(REQUEST)
        try:
            d = self.__state_string_to_dict(state)
            return d[name].split(',')
        except:
            return []

    def state_form(self, REQUEST, action, method,
                   enctype='application/x-www-form-urlencoded',
                   accept_charset='utf-8'):
        """Return HTML form and input tags."""
        state = self.__state_from_request(REQUEST)
        return '<form action="%s" method="%s" enctype="%s" accept-charset="%s"><input type="hidden" name="state_url" value="%s">' % \
               (action, method, enctype, accept_charset, state)


    # The rest of the functions are named state_href_*
    # and return URL (they are typically called from
    # DTML something like:
    # <a href="<dtml-var expr="state_href_*(REQUEST, ...)>">

    def state_href_swap_in_list(self, REQUEST, href, name, item):
        """Return URL after swapping item in a given list."""
        state = self.__state_from_request(REQUEST)
        l = self.__state_get_list_with_swap(state, name, item)
        d = self.__state_string_to_dict(state)
        d[name] = join(l,',')
        return self.__state_href(self.__dict_to_state_string(d), href)

    def state_href_remove_from_list(self, REQUEST, href, name, item):
        """Return URL after removing item from a given list."""
        l = self.state_get_list(REQUEST, name)
        if item in l:
            l.remove(item)
        state = self.__state_from_request(REQUEST)
        d = self.__state_string_to_dict(state)
        d[name] = join(l,',')
        return self.__state_href(self.__dict_to_state_string(d), href)

    def state_href_move_left_in_list(self, REQUEST, href, name, item):
        """Return URL after after moving item left in a given list."""
        state = self.__state_from_request(REQUEST)
        l = self.__state_get_list_with_move_left(state, name, item)
        d = self.__state_string_to_dict(state)
        d[name] = join(l,',')
        return self.__state_href(self.__dict_to_state_string(d), href)

    def state_href_move_right_in_list(self, REQUEST, href, name, item):
        """Return URL after after moving item right in a given list."""
        state = self.__state_from_request(REQUEST)
        l = self.__state_get_list_with_move_right(state, name, item)
        d = self.__state_string_to_dict(state)
        d[name] = join(l,',')
        return self.__state_href(self.__dict_to_state_string(d), href)

    def state_href_set_string(self, REQUEST, href, name, value):
        """Return URL after setting a new value to string."""
        state = self.__state_from_request(REQUEST)
        d = self.__state_string_to_dict(state)
        d[name] = value
        return self.__state_href(self.__dict_to_state_string(d), href)

    def state_href_set_list(self, REQUEST, href, name, value):
        """Return URL after setting a new value to list."""
        state = self.__state_from_request(REQUEST)
        d = self.__state_string_to_dict(state)
        d[name] = str(value)[1:-1]
        return self.__state_href(self.__dict_to_state_string(d), href)

    def state_href(self, REQUEST, href):
        """Return URL."""
        state = self.__state_from_request(REQUEST)
        return self.__state_href(state, href)

    # The rest are 'private' functions...

    def __state_from_request(self, REQUEST):
        uname = str(REQUEST.AUTHENTICATED_USER)
        if REQUEST.has_key('state_url'):
            try:
                old_state = self.fle_users.get_user_info(uname).get_state()

                try:
                    # Just called to check if state_url is invalid.
                    self.__state_string_to_dict(REQUEST.state_url)
                except:
                    print 'Invalid state url: ' + REQUEST.state_url
                    return old_state

                 # Let's try to avoid unnecessary write operations.
                if old_state != REQUEST.state_url:
                    self.fle_users.get_user_info(uname).set_state(REQUEST.state_url)
            except:
                # For some unknown reason when using Mozilla after redirect
                # in message_dialog_handler the AUTHENTICATED_USER inside
                # REQUEST has a value 'Anonymous User' and the get_user_info()
                # call raises an exception above...
                pass

            return REQUEST.state_url
        else:
            # hack for self registration page
            try:
                return self.fle_users.get_user_info(uname).get_state()
            except:
                return ''


    def __state_get_list_with_swap(self, state, name, item):
        d = self.__state_string_to_dict(state)

        if d.has_key(name):
            l = d[name].split(',')
        else:
            l = []

        if item in l:
            l.remove(item)
        else:
            l.append(item)
        return l

    def __state_get_list_with_move_left(self, state, name, item):
        d = self.__state_string_to_dict(state)

        try:
            l = d[name].split(',')
            index = l.index(item)
        except KeyError:
            raise 'FLE error (KeyError)', \
                  '__state_get_list_with_move_left(): invalid parameters' + \
                  '(state = %s, name = %s, item = %s)' % (state, name, item)
        except ValueError:
            raise 'FLE error (ValueError)', \
                  '__state_get_list_with_move_left(): invalid parameters' + \
                  '(state = %s, name = %s, item = %s)' % (state, name, item)

        if index == 0: # move first item to last and shift other items left.
            length = len(l)
            tmp = l[0]
            for i in range(0, length-1):
                l[i] = l[i+1]
            l[length-1] = tmp
        else: # normal case
            self.__swap_in_list(l, index-1, index)
        return l

    def __state_get_list_with_move_right(self, state, name, item):
        d = self.__state_string_to_dict(state)

        try:
            l = d[name].split(',')
            index = l.index(item)
        except KeyError:
            raise 'FLE error (KeyError)', \
                  '__state_get_list_with_move_right(): invalid parameters' + \
                  '(state = %s, name = %s, item = %s)' % (state, name, item)
        except ValueError:
            raise 'FLE error (ValueError)', \
                  '__state_get_list_with_move_right(): invalid parameters' + \
                  '(state = %s, name = %s, item = %s)' % (state, name, item)

        if index == len(l)-1: # move last item to first and shift other
            length = len(l)   # items right.
            tmp = l[length-1]
            r = range(1, length)
            r.reverse()
            for i in r:
                l[i] = l[i-1]
            l[0] = tmp
        else: # normal case
            self.__swap_in_list(l, index, index+1)
        return l

    def __swap_in_list(self, l, index1, index2):
        tmp = l[index1]
        l[index1] = l[index2]
        l[index2] = tmp

    def __state_href(self, state, href):
        try:
            i = href.index('#')
            uri = href[:i]
            fragment_identifier = href[i:]
        except ValueError:
            uri = href
            fragment_identifier = ''

        if '?' in href:
            return uri + "&state_url=" + state + fragment_identifier
        else:
            return uri + "?state_url=" + state + fragment_identifier

    def __state_string_to_dict(self, state):
        d = {}
        while len(state) > 0:
            m = re.match("(\d+),(\d+)(.*)", state)
            if m:
                len_1 = atoi(m.group(1))
                len_2 = len_1 + atoi(m.group(2))
                state = m.group(3)
                d[state[:len_1]] = state[len_1:len_2]
                state = state[len_2:]
            else:
                raise 'Invalid state string'

        return d

    def __dict_to_state_string(self, d):
        state = ""
        for k in d.keys():
            len_1 = str(len(k))
            len_2 = str(len(d[k]))
            state = state + len_1 + ',' + len_2 + k + d[k]
        return state

#EOF

