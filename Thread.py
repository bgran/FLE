# $Id: Thread.py,v 1.60 2003/06/13 07:57:11 jmp Exp $
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

"""Contains class Thread, which is a superclass for all knowledge building objects, and some utility comparison functions."""

__version__ = "$Revision: 1.60 $"[11:-2]

import time, string

import re
import OFS
from Globals import Persistent, Acquisition, PersistentMapping
import Globals

from State import State
from TraversableWrapper import TraversableWrapper
from Cruft import Cruft
from AccessControl import ClassSecurityInfo
from common import reload_dtml, add_dtml, str_cmp

# A Thread represents a thread in a conversation.
# The subclasses provide concrete examples.
#
# Contains methods that are needed in conversation threads.

def _sort_func(d1, d2):
    t1 = d1['obj'].get_creation_time()
    t2 = d2['obj'].get_creation_time()
    if t1 < t2:    return -1
    elif t1 == t2: return 0
    else:          return 1

class Thread(
    TraversableWrapper,
    Cruft,
    Persistent,
    OFS.Folder.Folder,
    OFS.SimpleItem.Item
    ):
    """Thread -- a base class for Course, CourseContext, and Note classes."""
    meta_type = 'Thread'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    #Make sure to call this in the constuctors of the subclasses.
    #
    #Parameters:
    #
    #- self = The object itself.
    #
    #- parent =  The parent object of self. It must be given as argument
    #because self is not an acquisition wrapper yet.
    #
    #Note that TempObjectManager does not need unique id!
    # (and does not have parent)
    def __init__(self, parent):
        """Construct Thread object."""
        if parent == None: self.id = '0'
        else: self.id = parent.generate_id()
        self.title = ''

    # Called by Zope after creation of the object.
    def manage_afterAdd(self, item, container):
        """Set default permissions for different roles."""
        self.manage_permission(
            'View',
            ['Manager', 'FLEAdmin', 'Teacher', 'Tutor', 'Student',], 0)

    security.declareProtected('View', 'get_root')
    # Implemented using TraversableWrapper's find_class_obj method.
    def get_root(self):
        """Return CourseContext root of the whole thread."""
        return self.find_class_obj(CourseContext)

    security.declarePrivate('walk')
    def walk(self, path):
        """Recursively walks through the Thread child hierarchy,
        returning a list of tuples (object,path). Does a depth-first
        descend."""
        l = []
        path = string.join([path, self.get_id()], '/')
        for e in self.get_children('Note'):
            for e2 in e.walk(path):
                l.append(e2)

        if path[-1] != '/': path += '/'
        l.insert(0, {'obj': self, 'path': path})
        return l

    security.declareProtected('View', 'get_data_by_tt')
    #Return something like:
    #[(ThinkingType1, [{'obj':Note1,  'path': path1},
    #                  {'obj':Note2,  'path': path2}, .. ]),
    # (ThinkingType2, [{'obj':NoteN,  'path': pathN},
    #                  {'obj':NoteN+1,'path': pathN+1},..]),
    #                  ..]
    #
    #Each note in the inner lists have the same thinkingtype.
    def get_data_by_tt(self):
        """Returns a listing of the thread grouped by thinking type."""
        lnotes = self.walk('')

        r = []
        d = self.__separate_tt(lnotes)
        tts = self.get_thinking_type_set()
        for tt in tts.get_children('ThinkingType'):
            try:
                sorted_list = d[tt.get_id()]
                sorted_list.sort(_sort_func)
                r.append((tt, sorted_list))
            except KeyError:
                pass
        return r

    security.declareProtected('View', 'get_data_by_author')
    #Return something like:
    # [(author1, [{'obj':Note1,  'path': path1},
    #             {'obj':Note2,  'path': path2}, .. ]),
    #  (author2, [{'obj':NoteN,  'path': pathN},
    #             {'obj':NoteN+1,'path': pathN+1},..]),
    #             ..]
    #
    #Each note in the inner lists have the same author.
    def get_data_by_author(self):
        """Returns a listing of the thread grouped by author."""
        lnotes = self.walk('')

        r = []
        d = self.__separate_author(lnotes)
        authors = d.keys()
        authors.sort()
        for a in authors:
            sorted_list = d[a]
            sorted_list.sort(_sort_func)
            r.append((a, sorted_list))
        return r

    security.declareProtected('View', 'get_data_by_date')
    #Return something like:
    #[(date1, [{'obj':Note1,  'path': path1},
    #          {'obj':Note2,  'path': path2}, .. ]),
    # (date2, [{'obj':NoteN,  'path': pathN},
    #          {'obj':NoteN+1,'path': pathN+1},..]),
    #          ..]
    #
    #Each note in the inner lists have the same date..."""
    def get_data_by_date(self):
        """Returns a listing of the thread grouped by date."""
        lnotes = self.walk('')

        r = []
        d = self.__separate_date(lnotes)
        dates = d.keys()
        dates.sort()
        dates.reverse()
        for date in dates:
            r.append((date, d[date]))
        return r

    # No input checking -> do not call for the first note.
    security.declareProtected('View', 'get_path_to_previous')
    def get_path_to_previous(self, printer='trivial_tree_printer'):
        """Return URL to previous note in the thread (if thread is
        sorted by given printer)."""
        (index, d_list) = self.get_notes_in_sorted_list(printer)
        current_path = d_list[index]['path']
        new_path = d_list[index-1]['path']
        return self.absolute_url()[:-(len(current_path) - 1)] + new_path

    # No input checking -> do not call for the last note.
    security.declareProtected('View', 'get_path_to_next')
    def get_path_to_next(self, printer='trivial_tree_printer'):
        """Return URL to next note in the thread (if thread is
        sorted by given printer)."""
        (index, d_list) = self.get_notes_in_sorted_list(printer)
        current_path = d_list[index]['path']
        new_path = d_list[index+1]['path']
        return self.absolute_url()[:-(len(current_path) - 1)] + new_path

    security.declareProtected('View', 'is_first_note')
    def is_first_note(self, printer='trivial_tree_printer'):
        """Is this the first note in the thread (if thread is
        sorted by given printer)."""
        (index, d_list) = self.get_notes_in_sorted_list(printer)
        if index == 0: return 1
        else: return 0

    security.declareProtected('View', 'is_last_note')
    def is_last_note(self, printer='trivial_tree_printer'):
        """Is this the last note in the thread (if thread is
        sorted by given printer)."""
        (index, d_list) = self.get_notes_in_sorted_list(printer)
        if index == len(d_list)-1 : return 1
        else: return 0

    security.declareProtected('View', 'get_id_of_first_unread_note')
    def get_id_of_first_unread_note(self, REQUEST):
        """Return id of first (first as sorted by current printer)
        unread (by current user) note."""

        uname = str(REQUEST.AUTHENTICATED_USER)
        printer = State().state_get_string(REQUEST, 'printer')
        if not printer:
            printer = 'trivial_tree_printer'
        #print printer
        notes = [d['obj'] for d in self.get_notes_in_sorted_list(printer)[1]]
        for note in notes:
            if not note.is_reader(uname):
                return note.get_id()
        return '-1'

    security.declarePrivate('get_notes_in_sorted_list')
    # If there are N notes in the thread, we return something like:
    #
    # (index, [{'obj': Note1, 'path: path1},
    #          {'obj': Note2, 'path: path2},
    #          ...
    #          {'obj': NoteN, 'path: pathN}])
    #
    # where index is index to current (self) obj/path in the list.
    def get_notes_in_sorted_list(self, printer='trivial_tree_printer'):
        """Return notes in a thread sorted by given printer."""
        other_printers = {'tt_printer'    : 'get_data_by_tt',
                          'author_printer': 'get_data_by_author',
                          'date_printer'  : 'get_data_by_date',
                          }

        if printer == 'trivial_tree_printer':
            l = self.find_thread_start_node().walk('')
        elif printer in other_printers.keys():
            l = []
            for t in eval('self.find_thread_start_node().' + \
                          other_printers[printer] + '()' ):
                for x in t[1]:
                    l.append(x)
        else:
            raise 'FLE Error', 'Unknown printer'

        my_id = self.get_id()
        for i in range(len(l)):
            obj = l[i]['obj']
            path = l[i]['path']
            if obj.get_id() == my_id:
                return (i,l)

        raise 'FLE Error', 'I am not in the list' # Should never happen.

    def __get_day(self, time):
        """Converts a time (in seconds) into days."""
        return int(time/86400) # 24 hours * 60 minutes * 60 seconds

    def __separate_date(self, l):
        rv = {}
        for e in l:
           try:
               rv[self.__get_day(e['obj'].get_creation_time())].append(e)
           except KeyError:
               rv[self.__get_day(e['obj'].get_creation_time())] = [e]
        return rv

    def __separate_author(self, l):
        rv = {}
        for e in l:
           try:
               rv[e['obj'].get_author()].append(e)
           except KeyError:
               rv[e['obj'].get_author()] = [e]
        return rv

    def __separate_tt(self, l):
        rv = {}
        for e in l:
           try:
               rv[e['obj'].get_tt_id()].append(e)
           except KeyError:
               rv[e['obj'].get_tt_id()] = [e]
        return rv

    # Returns a list of tuples (object,path,level)
    def get_threaded_children(self):
        """Returns the children of the Thread in threaded order."""
        if self.meta_type == 'CourseContext':
            return self.__get_data()[1:]
        else:
            return self.__get_data()

    # Traverses recursively self and children of type Note;
    # return a list of tuples where each tuple contains: object, relative
    # path, and level (Level of self is 0, its children have level 1,
    # and so on...)
    #
    # This is used to render a threaded note list in dtml.
    def __get_data(self, path='', level=0):
        """Return a list of notes in a thread."""
        retval = []

        # Construct the first tuple and append it to retval.
        if len(path) > 0 and path[-1] != '/':
            retval.append((self, path + '/', level))
        else:
            retval.append((self, path, level))

        # Handle the children recursively.
        for e in self.get_children(['CourseContext','Note']):
            for ee in e.__get_data(self.__join(path, e.get_id()),
                                   level + 1):
                retval.append(ee)
        return retval

    # No additional comments.
    def __join(self, path1, path2):
        """Combine two paths together with a forward slash.
        If first parameter is empty, then just return second parameter
        (to get relative path)."""
        if path1 == '': return path2
        else: return path1 + '/' + path2

    security.declarePrivate('generate_id')
    # No additional comments.
    def generate_id(self):
        """Returns a unique id by passing the call recursively up
        the parent tree until it reaches CourseManager, which overrides
        this method (by being an IDManager)."""
        parent = self.parent()
        if not isinstance(parent, Thread):
            raise 'FLE Error', 'Thread.parent() is not Thread class-type (it can\'t generate id)'
        return parent.generate_id()

Globals.InitializeClass(Thread)

# Currently only a Read event is handled. This class is inherited into
# Note so that each note will store information on who has read the note
# and can retrieve that information as needed.
class EventManager(
    Persistent,):
    """EventManager Handles different events that can happen to an object."""

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    def __init__(self):
        """Construct EventManager."""
        self.readers = PersistentMapping()
        self._p_changed = 1

    def manage_afterAdd(self, item, container):
        """Set default permissions for different roles."""
        self.manage_permission(
            'View',
            ['Manager', 'FLEAdmin', 'Tutor', 'Student',], 0)

    security.declarePrivate('update_reader')
    def update_reader(self, reader_nam):
        """Updates reader state. If there is no reader thingy yet, create
        one for self."""
        reader_nam=str(reader_nam)
        if self.readers.has_key(reader_nam):
            self.readers[reader_nam]['count'] += 1
            self.readers[reader_nam]['when'].append(time.time())
        else:
            self.readers[reader_nam] = {'count':1, 'when':[time.time()]}
        self._p_changed = 1

    security.declarePrivate('set_exported_reader')
    def set_exported_reader(self, reader_name, dates):
        """Update reader's dates from export."""
        self.readers[reader_name] = {'count': len(dates), 'when': dates}

    security.declareProtected('View', 'is_reader')
    def is_reader(self, reader_nam):
        """Return boolean depending on whether reader_nam has read
        the note or not."""
        reader_nam=str(reader_nam)
        return (
            (self.readers.has_key(reader_nam)) and \
            [self.readers[reader_nam]['count']] or [0])[0]

    security.declarePrivate('map_to_user')
    def map_to_user(self, user_name):
        """@user_name - string representing the user name that we want to map.
        Return: UserInfo object."""
        um = self.fle_users
        return um.get_user_info(user_name)

    security.declareProtected('View', 'ev_get_readers')
    def ev_get_readers(self):
        """Return a tuple of people who've read this Thread entry, and when:
         ({"obj":Bob, "when":234234234234.234234, "count":69},
          {"obj":Alice, "when":31415231234234234.234234, "count":42},
          {"obj":Mallory, "when":31337123454234234.23423, "count":13}) """
        rv = [{"obj":self.map_to_user(key), "when":val['when'][-1], \
           "count":val['count']} \
           for (key, val) in self.readers.items()]
        return tuple(rv)

    security.declareProtected('View', 'get_readers_with_all_dates')
    def get_readers_with_all_dates(self):
        """Return something like:
        {"Bob": {"count":52, "when":234234234234.234234},
         "Alice": {"count":69, "when":313377350.666} }
        """
        return self.readers

    security.declareProtected('View', 'is_reader_req')
    def is_reader_req(self, REQUEST):
        """To be called from dtml. This might be duplicated functionality."""
        return self.is_reader(str(REQUEST.AUTHENTICATED_USER))

Globals.InitializeClass(EventManager)

# EOF
