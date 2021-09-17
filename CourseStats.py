# $Id: CourseStats.py,v 1.7 2004/07/07 17:27:03 tarmo Exp $
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

"""Contains auxiliary classes for collecting statistics from a course."""

__version__ = '$Revision: 1.7 $'[11:-2]

from AccessControl import ClassSecurityInfo
from common import perm_view, perm_edit, perm_manage, perm_add_lo

class Stats:
    def __init__(self,fields,records):
        self.stat={}
        self.fields=fields[:]
        for rec in records:
            self.stat[rec]=len(fields)*[0]

    def add(self,field,record):
        try:
            ndx = self.fields.index(field)
            self.stat[record][ndx] = self.stat[record][ndx]+1
        except KeyError:
            # The specified record doesn't exist.
            # TODO: A bit dangerous to just skip the exception
            pass
        except ValueError:
            # The specified field doesn't exist.
            # TODO: A bit dangerous to just skip the exception
            pass

    def printout(self):
        res = ""
        recs = self.stat.keys()
        recs.sort()
        for rec in recs:
            data=self.stat[rec]
            res = res + "%s" % rec
            for d in data:
                res = res + "\t%s" % d
            res = res + "\n"
        return res

class CourseStats:
    def collect_stats(self,REQUEST):
        """Collects statistics about the course."""
        res = "Statistics\t%s\t%s\n\n" % (self.get_id(),self.get_name())
        # FIXME: Assumes that all contexts have the same thinking type set!
        types = {}
        for ctx in self.get_children('CourseContext'):
            ttset = ctx.get_thinking_type_set()
            for (id,type) in ttset.objectItems('ThinkingType'):
                if id not in types.keys():
                    types[id]=type.get_name()

        # Get all participants
        users = self.get_all_users_id()
        # Alternative method: Collects users from notes
        users = []
        for ctx in self.get_children('CourseContext'):
            for note in ctx.get_children('Note'):
                users=self.__do_note_authors(note,users)
        users.sort()

        stat=Stats(['w','r','s'] + types.keys() + ['m','l','d'], users)

        # Collect stats from course contexts
        for ctx in self.get_children('CourseContext'):
            for note in ctx.get_children('Note'):
                self.__do_note_stats(note,stat)

        # Collect stats from users' webtops
        for user in self.get_all_users():
            webtop = user.get_webtop()
            self.__do_webtop_stats(webtop,stat)

        # Collect stats from group folder
        if self.has_group_folder():
            for folder in self.objectValues('GroupFolder'):
                self.__do_webtop_stats(folder,stat)

        res=res+"Participant\tWritten notes\tRead notes\tStarting notes\t" + \
             '\t'.join(types.values())+ \
             "\tMemos\tLinks\tDocuments\n"
        res = res + stat.printout() + "\n\n"

        num_threads=0
        for ctx in self.objectValues('CourseContext'):
            for note in ctx.objectValues('Note'):
                num_threads+=1
        thread_lengths = num_threads*[0]
        ndx = 0
        for ctx in self.objectValues('CourseContext'):
            for note in ctx.objectValues('Note'):
                len = self.__do_note_stat_count(note,0)
                thread_lengths[ndx]=len
                ndx=ndx+1

        min=thread_lengths[0]
        max=thread_lengths[0]
        sum=0
        isolated=0
        for t in thread_lengths:
            if t<min: min=t
            if t>max: max=t
            if t==1: isolated+=1
            sum += t
        mean = sum*1.0/num_threads

        res = res + "Number of threads\t%s\n" % num_threads
        res = res + "Length of threads, mean\t%s\n" % mean
        res = res + "Length of threads, min\t%s\n" % min
        res = res + "Length of threads, max\t%s\n" % max
        res = res + "Number of isolated notes\t%s\n\n\n" % isolated

        # Social interaction table
        statw = Stats(users,users)
        statr = Stats(users,users)
        threadCount=0
        for ctx in self.objectValues('CourseContext'):
            for note in ctx.objectValues('Note'):
                threadCount+=1
                self.__do_note_stat_replies(note,statw,statr)

        res = res + "Replier\tWriter of the note that has been replied to\n"
        res = res + "\t" + "\t".join(users) + "\n"
        res = res + statw.printout() + "\n\n"
        res = res + "Reader\tWriter of the note that has been read\n"
        res = res + "\t" + "\t".join(users) + "\n"
        res = res + statr.printout() + "\n\n"

        # Thread involvement stats
        threads=[]
        for i in range(1,threadCount+1):
            threads.append(str(i))
        statt = Stats(threads,users)
        count=0
        for ctx in self.objectValues('CourseContext'):
            for note in ctx.objectValues('Note'):
                count+=1
                self.__do_thread_stat(str(count),note,statt)

        res = res + "Replier\tThread number\n"
        res = res + "\t" + "\t".join(threads) + "\n"
        res = res + statt.printout() + "\n\n"

        # Group folder stats.

        return res

    def __do_note_authors(self,note,list):
        author=note.get_author()
        if not author in list:
            list.append(author)
        for note2 in note.get_children('Note'):
            self.__do_note_authors(note2,list)
        return list

    def __do_note_stats(self,note,stat):
        author=note.get_author()
        stat.add('w',author)
        stat.add(note.get_tt_id(),author)
        if note.is_starting_note():
            stat.add('s',author)
        for reader in note.readers.keys():
            stat.add('r',reader)
        for note2 in note.get_children('Note'):
            self.__do_note_stats(note2,stat)
        return stat

    def __do_webtop_stats(self,folder,stat):
        for item in folder.list_contents():
            if item.meta_type=='WebtopLink':
                stat.add('l',item.get_author_name())
            elif item.meta_type=='WebtopFile':
                stat.add('d',item.get_author_name())
            elif item.meta_type=='WebtopMemo':
                stat.add('m',item.get_author_name())
            elif item.meta_type=='WebtopFolder':
                self.__do_webtop_stats(item,stat)

    def __do_note_stat_count(self,note,count):
        count+=1
        for note2 in note.objectValues('Note'):
            count=self.__do_note_stat_count(note2,count)
        return count

    def __do_note_stat_replies(self,parent,statw,statr):
        pauthor = parent.get_author()
        for reader in parent.readers.keys():
            # column=field =1st param
            # row   =record=2nd param
            # reader reads a note from pauthor
            # row=reader
            # column=writer of the note that has been read
            # thus: row=reader, column=pauthor
            statr.add(pauthor,reader)
        for note in parent.objectValues('Note'):
            nauthor = note.get_author()
            # nauthor replies to a message from pauthor
            # row=replier
            # column=writer of the note that has been replied to
            # thus: row=nauthor, column=pauthor
            statw.add(pauthor,nauthor)
            self.__do_note_stat_replies(note,statw,statr)

    def __do_thread_stat(self,thread,parent,statt):
        for note in parent.objectValues('Note'):
            nauthor = note.get_author()
            # nauthor replies to a message from pauthor
            # row=replier
            # column=writer of the note that has been replied to
            # thus: row=nauthor, column=pauthor
            statt.add(thread,nauthor)
            self.__do_thread_stat(thread,note,statt)
