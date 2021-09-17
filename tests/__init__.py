# $Id: __init__.py,v 1.63 2003/06/13 07:57:13 jmp Exp $

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

def www_fetch(url,user='user1:passwd1',follow=1):
    """Load the url specified by the url and user credentials."""

    f = open("fletest.tmp","w")
    orig_out = sys.stdout
    try:
        sys.stdout = f
        Zope.debug(url,u=user)
        f.close()
        f=open("fletest.tmp","r")
        res = f.read()
        #if www_get_status(res)==302:
        #    return www_fetch(os.path.join(url,
        #                     re.search('Location: (.*)',res,re.M).group(1)))
        #
        return res
    finally:
        f.close()
        sys.stdout=orig_out

def www_get_status(result):
    """Extract the http status code from an http reply."""

    match = re.search('Status: ([0-9][0-9][0-9]) .*',result,re.M)
    if match is None:
        return -1
    return string.atoi(match.group(1))

def www_get_error_info(result):
    """Extract bobo-error information from an http reply."""

    info=[]
    match = re.search('Bobo-Exception-File: (.*)',result,re.M)
    if match is None:
        return ['unknown file','???','unknown error']
    info.append(match.group(1))
    match = re.search('Bobo-Exception-Line: (.*)',result,re.M)
    info.append(match.group(1))
    match = re.search('Bobo-Exception-Type: (.*)',result,re.M)
    info.append(match.group(1))

    return info

def wwwtest(url,user='user1:passwd1',expected=None):
    """Load a web page specified by url, using the given credentials.
    If an 'expected' value is given, that status code must be received
    or an assert failure is raised. If no status code is specified,
    an erroneous status code (not between 100 and 399) will raise
    an assert failure."""

    res = www_fetch(url,user)
    status = www_get_status(res)

    if status>=500:
        errinfo = www_get_error_info(res)
        raise 'Error publishing page:\n' + \
              errinfo[0]+', '+errinfo[1]+': '+errinfo[2]

    if expected is None:
        assert status >= 100 and status < 400, \
               "Returned error status: " + str(status)
        if status==302 and expected!=302:
            print "*** WARNING: "+url+" returned a http-redirect!"
    else:
        assert status == expected, \
               "Got status "+str(status)+", expected to receive "+ \
               str(expected)+"."
    return res

# Here are the utility functions to start and stop the test installation
# and to access several often needed objects.
def getApp():
    return _start()

def getFle():
    return fle

def getCourse():
    return course

def getContext():
    return ctx

sent_emails=[]
def dummy_send(headers,body):
    global sent_emails
    sent_emails.append((headers,body))

def dummify_mail_host(fle):
    host = fle.MailHost
    host._send=dummy_send

def _start():
    global app, fle
    if app:
        return app
    else:
        app=Zope.app()

        # Add an emulated REQUEST into app's acquisition chain.
        # This is needed for ZCatalog code to work in python access
        # (as opposed to http access).
        from ZPublisher.BaseRequest import RequestContainer
        from common import FakeRequest
        rc=RequestContainer(REQUEST=FakeRequest())
        app = app.__of__(rc)

        if 'testfle' in app.objectIds():
            print "Removing old FLE installation..."
            app._delObject('testfle')
        if 'imported' in app.objectIds():
            print "Removing old FLE imported installation..."
            app._delObject('imported')
        print "Installing new FLE..."
        app.manage_addProduct['FLE'].manage_addFLE(
            'testfle', 'Test FLE', 'fleadmin', 'ni', 'ni', 'Foo', 'Bar',
            'create', 'smtp', '25')
        commit()
        for install in app.objectValues('FLE'):
            if install.get_id()=='testfle':
                fle=install
                dummify_mail_host(fle)
                fle.fle_users.fleadmin.set_email('fleadmin@foo.fi')
                return app

def _stop():
    print "Removing FLE and closing connection..."
    app._delObject('testfle')
    try:
        commit()
    except:
        pass
    app._p_jar.close()

def commit():
    """Just a convenience function for committing a transaction."""
    try:
        get_transaction().commit()
    except:
        print "[commit failed]"
        get_transaction().commit()
        print "[recovered]"

def abort():
    """Just a convenience function for aborting a transaction."""
    get_transaction().abort()

# Here's the initialization code.
print "Setting up environment..."
import sys, os, re, string
if os.environ.has_key("ZOPE_PATH"):
    zope_path = os.environ["ZOPE_PATH"]
elif os.path.exists("zope_path"):
    f=open('zope_path','r')
    zope_path = f.read().strip()
    f.close()
else:
    print """ERROR: The environmental variable ZOPE_PATH not the file zope_path was found. Please set either of them to point to the directory that contains Zope's python libraries. (example: export ZOPE_PATH=/usr/local/zope/lib/python - or - echo "/usr/local/zope/lib/python" > zope_path)."""
    sys.exit(1)
sys.path.insert(0,zope_path)

_dbdir=os.path.join(os.getcwd(),'tests/workdb')
if not os.path.exists(_dbdir):
    print "Creating new temporary Zope DB directory: "+_dbdir
    os.makedirs(_dbdir)
    os.makedirs(os.path.join(_dbdir,'var'))
os.environ['INSTANCE_HOME']=_dbdir

print "Loading Zope..."
import Zope
print "Loading unit testing framework..."
import unittest
from common import FakeRequest, FakeUpload
app=None
app=_start()
import atexit
atexit.register(_stop)
print "Initialization done."

# End of initialization code

users_loaded=0
def withUsers():
    global users_loaded
    if users_loaded:
        return
    print "[creating users]"
    # Users:
    # 1: Teacher in course 1
    # 2: Teacher in course 2
    # 3: Tutor in course 2. Has content in webtop.
    #    Active user, use to read notes.
    # 4: Student in course 2. Incative user, should not be used to read notes.
    # 5: Student in course 2. Frozen user.
    # 6: Student in course 2.
    for i in range(1,7):
        ii=repr(i)
##         wwwtest(
##             '/testfle/fle_users/add_user_form_handler?uname=user'+ii+\
##             '&password1=passwd'+ii+\
##             '&password2=passwd'+ii+\
##             '&first_name=First'+ii+\
##             '&last_name=Last'+ii+\
##             '&email=joe'+ii+'@foo.fi'+\
##             '&homepage=http://www.foo'+ii+'.fi'+\
##             '&organization=Testers Inc.'+\
##             '&language=fi'+\
##             '&add=submit',
##            user='fleadmin:ni')

        fle.fle_users.add_user(
            uname='user'+ii,                     # uname
            password='passwd'+ii,                  # password
            roles=('User',))
        user = fle.fle_users.get_user_info('user'+ii)
        user.set_nickname('user'+ii,)
        user.set_first_name('First'+ii)
        user.set_last_name('Last'+ii)
        user.set_email('joe'+ii+'@foo.fi')
        user.set_homepage('http://www.foo'+ii+'.fi')
        user.set_organization('Testers Inc.')
        user.set_language('fi')

##        fle.fle_users.add_user_form_handler(
##            uname='user'+ii,                     # uname
##            nickname='user'+ii,
##            pwd='passwd'+ii,                  # password
##            pwd_confirm='passwd'+ii,                  # password 2
##            first_name='First'+ii,                     # first_name
##            last_name='Last'+ii,                   # last_name
##            email='joe'+ii+'@foo.fi',             # email
##            homepage='http://www.foo'+ii+'.fi', # homepage
##            organization='Testers Inc.',
##            language='fi',                     # language,
##            commit='submit',
##            REQUEST=FakeRequest())
##        user = fle.fle_users.get_user_info('user'+ii)
        upload=None
        for (id,img) in fle.images.objectItems():
            if id == 'round_bl0'+ii:
                upload=FakeUpload(id,img.data,'image/gif')
                break
        user.edit_info(
            photo_upload=upload,
            #'',                        # photo_url
            #group='Group'+ii,                        # group
            group_ids = [],
            address1='Address'+ii,              # address
            address2='Address2_'+ii,
            country='Country'+ii,                 # country
            phone='09-'+ii,                     # phone
            gsm='050-'+ii,                     # gsm
            quote='Quote'+ii, # quote
            background='Back\nground'+ii,                      # background
            personal_interests='Per\nsonal'+ii,                      # personal_interests
            professional_interests='Pro\nfessional'+ii,                      # professional_interests
            )

        if i < 3:
            # Webtops of user1 and user2 use default background images.
            user.set_webtop_bg_from_default_image(('bgcolor_rd',
                                                   'wt_bg_bl')[i-1])
        else:
            # user3 uses her own personal image.
            f = open(os.path.join(os.getcwd(), 'ui/images/arrow_down.gif'))
            user.set_webtop_bg_from_image_data(f.read())
            f.close()

    # Create webtop for user3
    wt = fle.fle_users.user3.webtop
    wt.add_folder_handler(FakeRequest(),"folder1",submit='ok')
    wt.wt1.add_file_handler(FakeRequest(),"MyFile",FakeUpload("image.gif",fle.images.image.data,'image/gif'),submit='ok')
    wt.wt1.add_link_handler(FakeRequest(),"CheckMeOut","http://fle3.uiah.fi/",submit='ok')

    wt.wt1.add_memo_handler(FakeRequest(),"MyMemo",unicode("This memo contains\na few lines of text in Finnish.\nOsa on suomeksi, jotta voimme\ntestata ääkkösten toimintaa.",'iso-8859-1').encode('utf-8'),submit='ok')

    fle.fle_users.freeze_user('user5')
    commit()
    users_loaded=1


course=None
course_loaded=0
def withCourse():
    global course_loaded
    global course
    if course_loaded:
        return
    withUsers()
    print "[creating courses]"
    #print fle.fle_users.get_child('user1')
    fle.courses.add_course_form_handler(
        FakeRequest('user1'),
        '',
        'Test Course',
        'Course for\nFLE testing',
        'MediaLab',
        '-unit testing\n\n-stress testing',
        '1.2.1970',
        '31.12.2005',
        creating_new_course='1',
        do_groupfolder='',
        cancel='',
        add='ok',
        )
    commit()

    fle.courses.add_course_form_handler(
        FakeRequest('user2'),
        '',
        'Test Course 2',
        'Course 2 for FLE testing',
        'MediaLab',
        'UnitTesting',
        '2.3.1972',
        '30.11.2008',
        creating_new_course='1',
        do_groupfolder='1',
        cancel='',
        add='ok',
        )
    commit()

    course=fle.courses.get_courses()[1]
    course.add_student('user3')
    course.add_student('user4')
    course.add_student('user5')
    course.add_student('user6')
    course.set_roles('user3',('Tutor',))
    commit()
    course_loaded=1

tts_loaded=0
def withTTSs():
    global tts_loaded
    fle.typesets.start_edit_from_existing(FakeRequest(),tts_id='pitt')
    tts=fle.typesets.tmp_objects.objectValues('ThinkingTypeSet')[0]
    tts.set_name('A new TTS not yet ready')
    commit()
    tts_loaded=1

ctx=None
notes_loaded=0
def withNotes():
    global ctx, notes_loaded
    if notes_loaded:
        return
    withCourse()
    print '[creating notes]'
    c=fle.courses.get_courses()[1]
    commit()
    c.add_course_context('Context1','Description','pitt','Long description',
                         FakeRequest('user2'),publish='publish')
    commit()
    c.add_course_context('Context2','Description 2\nof several\nlines','pitt','Long description 2\n\nContains several\n line feeds and whitespace.',
                         FakeRequest('user3'),publish='publish')
    commit()
    ctx = c.get_course_contexts()[1]
    tts = ctx.get_thinking_type_set().get_thinking_types()
    (id,note) = ctx.add_note(tts[0].get_id(),'user2','Discussion 1','Body 1\nsecond line')
    note.do_publish()
    (id,note) = ctx.add_note(tts[0].get_id(),'user3','Discussion 2','Body 2')
    note.do_publish()

    # Add reply with a URL and an image
    from common import FakeUpload
    (id,note) = ctx.get_children('Note')[0].add_note(
        tts[1].get_id(),
        'user3',
        'Reply 1 to D1',
        'Body r1d1',
        'http://fle3.uiah.fi/',
        'FLE3 homepage',
        FakeUpload("wastef.gif",
                   fle.images.wastef.data,
                   fle.images.wastef.getContentType()),
        'Image of a waste basket',
        None,
        )
    note.do_publish()
    (id,note) = ctx.get_children('Note')[0].add_note(
        tts[2].get_id(),
        'user2',
        'Reply 2 to D1',
        'Body r2d1')
    note.do_publish()
    (id,note) = ctx.get_children('Note')[0].get_children('Note')[0].add_note(
        tts[3].get_id(),
        'user2',
        'Reply to R1/D1',
        'Body r1r1d1')
    note.do_publish()

    # Create links to notes in user3's webtop
    wt = fle.fle_users.user3.webtop
    wt.wt1.add_link("LinkToNote1","http://localhost:80/testfle/courses/2/4/5/",1)
    wt.wt1.add_link("LinkToNote2","http://localhost:80/testfle/courses/2/4/5/7/9/",1)

    commit()
    notes_loaded=1

jamming_loaded=0
def withJamming():
    global jamming_loaded
    if jamming_loaded:
        return
    withCourse()
    print '[creating jamming]'
    jamming=fle.courses.get_courses()[1].get_child('jamming')

    from common import FakeRequest, FakeUpload
    jamming.form_handler(
        REQUEST=FakeRequest(),
        my_name='jamming session 1',
        type='linear',
        description='This is linear blah blah',
        artefact_name='invite',
        artefact_upload=FakeUpload('invite',
                                   fle.images.invite_user.data,
                                   fle.images.invite_user.getContentType()),
        submit=1)
    commit()

    js1 = jamming.get_children('JamSession')[0]
    js1.add_artefact('waste icon',
                     fle.images.wastef.data,
                     fle.images.wastef.getContentType(),
                     'user1',
                     (js1.get_children('JamArtefact')[0].get_id(),))
    commit()

    jamming.form_handler(
        REQUEST=FakeRequest(),
        my_name='jamming session 2',
        type='tree',
        description='This is tree structured blah blah',
        artefact_name='invite',
        artefact_upload=FakeUpload('invite',
                                   fle.images.invite_user.data,
                                   fle.images.invite_user.getContentType()),
        submit=1)



    jamming_loaded=1


# EOF
