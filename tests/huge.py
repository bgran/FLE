# $Id: huge.py,v 1.6 2003/06/13 07:57:13 jmp Exp $

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

import sys, os, re, time
sys.path.insert(0,'.')
#sys.path.insert(0,'../')
#print sys.path
import tests
from random import random
from tests import *

def makeHugeInstall():
    """Makes a bitching huge test installation and exports into a zip file."""
    print "HUGE: Searching for data..."
    path = '/usr/share/games/fortunes'
    files = os.listdir(path)
    files = ['art','humorists','songs-poems','science','magic','definitions']
    fortunes = []
    for file in files:
        if file[-4:]!='.dat':
            fortunes.append(file)

    people = open(os.path.join(path,'people'))
    quote = open(os.path.join(path,'wisdom'))
    pro = open(os.path.join(path,'work'))

    print "HUGE: Creating 100 users..."
    for i in range(100):
        makeUser(str(i),people,quote,pro)

    count=0
    for fortune in fortunes:
        count+=1
        print "Starting to process file/course "+str(count)+"/"+str(len(fortunes))+": "+fortune,
        file = open(os.path.join(path,fortune))

        teachernum=int(random()*100)
        course = makeCourse(str(count),fortune,teachernum,file)
        usercount = 4+int(random()*80)
        for x in range(usercount):
            u = fle.fle_users.get_users()[int(random()*100)].get_id()
            if u not in course.get_all_users_id():
                course.add_student(u)
        print " with "+str(usercount)+" users",
        ctxcount = int(random()*9)-1
        if ctxcount<1:
            ctxcount=1
        print " into "+str(ctxcount)+" contexts",
        for i in range(ctxcount):
            makeContext(course,str(i),teachernum,file)
        commit()

        notecount=0
        while 1:
            lines = readFortune(file)
            if not lines:
                break
            ctx = course.get_course_contexts()[int(random()*ctxcount)]
            par = findParent(ctx)
            notecount+=1
            makeNote(par,str(notecount),lines)
            print ".",
            sys.stdout.flush()

        file.close()
        print ""

    print ""
    print "HUGE: Exporting..."
    commit()
    from ImportExport import Exporter

    exported = Exporter("FLE")
    exported.exportData(fle.typesets,exported.exportGlobalTypes)
    exported.exportData(fle.courses,exported.exportKB)
    exported.exportData(fle.fle_users,exported.exportUsers)
    exported.createZip("export_huge.zip")

    print "HUGE: Done!"


def readFortune(file):
    lines=""
    while 1:
        line = file.readline()
        if line=='' or line[0]=='%':
            if lines.find('\b')==-1 and \
               lines.find('\a')==-1 and \
               lines.find('<')==-1 and \
               lines.find('>')==-1:
                return lines
            lines=""
            if line=='':
                return None
        else:
            lines+=line

def readName(file):
    while 1:
        lines = readFortune(file)
        # Try #1
        res = re.search('\W{2,}-- (\w{3,}) (\w{3,})',lines)
        if not res:
            res = re.search('\W{2,}-- (\w{3,}) [\w.]+ (\w{3,})',lines)
        if res:
            return (res.group(1),res.group(2),)


def findParent(parent):
    """Locate a parent by descending into a note tree and stopping
    at a random location."""

    widen_factor = 35

    children = parent.objectValues('Note')
    selection = int(random()*(len(children)*100+widen_factor))
    if selection>=len(children)*100:
        return parent
    else:
        return findParent(children[int(selection/100)])

def makeUser(suffix,people,quote,pro):
    (first,last) = readName(people)
    uname = first+suffix
    print "User: "+first+" "+last
    fle.fle_users.add_user_form_handler(
        uname=uname,                     # uname
        password1='passwd'+suffix,                  # password
        password2='passwd'+suffix,                  # password 2
        first_name=first,                     # first_name
        last_name=last,                   # last_name
        email=first+'@foo.fi',             # email
        homepage='http://www.foo'+suffix+'.fi', # homepage
        organization='Testers Inc.',
        language='fi',                     # language,
        add='submit',
        REQUEST=FakeRequest())
    user = fle.fle_users.get_user_info(uname)
    for (id,img) in fle.images.objectItems():
        if id == 'round_bl0'+suffix:
            break
    user.edit_info(
        photo_upload=FakeUpload(id,img.data,'image/gif'),
        #'',                        # photo_url
        group='Group'+suffix,                        # group
        address1='Address'+suffix,              # address
        address2='Address2_'+suffix,
        country='Country'+suffix,                 # country
        phone='09-'+suffix,                     # phone
        gsm='050-'+suffix,                     # gsm
        quote=readFortune(quote), # quote
        background=readFortune(quote),                      # background
        personal_interests=readFortune(quote),                      # personal_interests
        professional_interests=readFortune(pro),                      # professional_interests
        )

def makeCourse(suffix,name,teachernum,file):
    cid = fle.courses.add_course_impl(fle.fle_users.get_users()[teachernum].get_id())
    course = fle.courses.get_child(cid)
    course.update(
        name,
        'Course '+suffix+' for FLE testing\n\n'+readFortune(file),
        'MediaLab',
        '-stress testing',
        time.time(),
        time.time())
    return course

def makeContext(course,suffix,teachernum,file):
    name =  'Context '+suffix
    course.add_course_context(
        name,
        readFortune(file),
        'coi',
        readFortune(file),
        FakeRequest(fle.fle_users.get_users()[teachernum].get_id()),
        'publish')

    for x in course.get_course_contexts():
        if x.get_name()==name:
            return x

def makeNote(parent,suffix,body):
    types = parent.get_thinking_type_set().get_thinking_types()
    type = types[int(random()*len(types))]

    users = parent.get_all_users_id()
    uid = users[int(random()*len(users))]

    length = 24
    if len(body)<24:
        length=len(body)

    (id,note) = parent.add_note(
        type.get_id(),
        uid,
        suffix+' '+body[:length],
        body)
    note.do_publish()

if __name__=='__main__':
    makeHugeInstall()


