#############################################################################
#
# utility.py
# Utility functions
#
# Copyright (c) 2003-2004 Atsushi Shibata. All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and its 
# documentation for any purpose and without fee is hereby granted, provided that
# the above copyright notice appear in all copies and that both that copyright 
# notice and this permission notice appear in supporting documentation, and that
# the name of Atsushi Shibata not be used in advertising or publicity pertaining 
# to distribution of the software without specific, written prior permission. 
# 
# ATSUSHI SHIBAT DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, 
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO
# EVENT SHALL SHIBAT ATSUSHI BE LIABLE FOR ANY SPECIAL, INDIRECT OR 
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF
# USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE. 
#
##############################################################################

#Import modules from python lib.
from string import join,find,rfind,replace,split
from time import time,localtime,mktime
import re
import sys
import os
from dircache import listdir
from random import randint

from App.Common import package_home
from Products.PythonScripts.PythonScript import manage_addPythonScript
from xmlrpclib import Server,Transport

import ThreadLock

from stripogram import html2safehtml

__doc__="""Zope Blog Product 'COREBlog:utility'
$Id: utility.py,v 1.1 2004/09/02 09:54:39 tarmo Exp $"""

__version__='$Revision: 1.1 $'[11:-2]

html_tag_regex = re.compile("<.*?>")
valid_tags = ('b','a','i','img','pre','blockquote','br','p','h3','ul','li','br')

code_euc = "euc-jp"
code_sjis = "shift_jis"
code_utf8 = "utf-8"
code_jis = "iso-2022-jp"
code_us = "us-ascii"
code_none = "none"

rotorkey = "wholovesya?"

_mutex=ThreadLock.allocate_lock()

def r2i(v,default=None):
    try:
        return int(v)
    except:
	return default

def sec_to_date_int(second = 0):
    #make calendar_date(int,like 20031123) from second
    if second == 0:
        second = time()
    t = localtime(second)
    int_date = t[0]*10000 + t[1]*100 + t[2]
    return int_date


def day_to_date_int(year,month,day):
    #make calendar_date(int,like 20031123) from year,month,day
    int_date = year*10000 + month*100 + day
    return int_date


def get_yesterday(int_date):
    #return 'yesterday' of int_date
    return get_relative_int_date(int_date,-24*60*60)


def get_tomorrow(int_date):
    #return 'tomorrow' of int_date
    return get_relative_int_date(int_date,24*60*60)


def get_yesterday_t(year,month,day):
    #return 'yesterday' of int_date
    return get_relative_int_date_t(year,month,day,-(24*60*60+10))


def get_tomorrow_t(year,month,day):
    #return 'tomorrow' of int_date
    return get_relative_int_date_t(year,month,day,24*60*60+10)


def get_relative_int_date(int_date,delta):
    #return relative int_date using 'delta'
    t = list(localtime(time()))
    t[0] = int_date / 10000
    t[1] = (int_date / 100) % 100
    t[2] = int_date % 100
    s = mktime(t) + delta
    return sec_to_date_int(s)


def get_relative_int_date_t(year,month,day,delta):
    #return relative int_date using 'delta'
    t = list(localtime(time()))
    t[0] = year
    t[1] = month
    t[2] = day
    s = mktime(t) + delta
    tt = localtime(s)
    return tt[0],tt[1],tt[2]

#field validation/sanitize

def remove_html(s):
    #remove HTML tags.
    return html_tag_regex.sub("",s)


def validate_html(s,tags=valid_tags):
    #remain only valid tags
    return html2safehtml(s,list(tags) + list(valid_tags))


def getNewID(old_count,data):
    #return new id for 'data' / return None when fail to aquire lock.
    old = None
    try:
        _mutex.acquire()
        old = old_count
        while data.has_key(old):
            old = old + 1
    finally:
        _mutex.release()
        pass
    if old is not None:
        return old
    else:
        raise RuntimeError,'Cannot lock mutex.'

#calling nortification hook

def call_script(site,script_path,dic):

    hook_obj = None
    try:
        hook_obj = site.restrictedTraverse(script_path)
    except:
        pass
        #no hook object
        return

    try:
        if hook_obj:
            #call the hook
            hook_obj(dic)
    except Exception,e:
        try:
            import zLOG
            zLOG.LOG("Error occured on hook method.", zLOG.ERROR, script_path,
                  error=sys.exc_info())
        except:
            raise e


def call_addentry_hook(site,id,author,body,extend,excerpt, \
                        moderated,title,subtitle,category, \
                        format,allow_comment,receive_trackback):
    d = {}
    d["id"]		= id
    d["author"]		= author
    d["body"]		= body
    d["extend"]		= extend
    d["excerpt"]	= excerpt
    d["moderated"]	= moderated
    d["title"]		= title
    d["subtitle"]	= subtitle
    d["category"]	= category
    d["format"]		= format
    d["allow_comment"]	= allow_comment
    d["receive_trackback"]= receive_trackback

    call_script(site,"methods/addEntryHook",d)


def call_addcomment_hook(site,id,parent_id,title,author,body, \
                            moderated,email,url):
    d = {}
    d["id"]		= id
    d["parent_id"]	= parent_id
    d["title"]		= title
    d["author"]		= author
    d["body"]		= body
    d["moderated"]	= moderated
    d["email"]		= email
    d["url"]		= url

    call_script(site,"methods/addCommentHook",d)


def call_addtrackback_hook(site,id,parent_id,title,excerpt,url,blog_name):
    d = {}
    d["id"]		= id
    d["parent_id"]	= parent_id
    d["title"]		= title
    d["excerpt"]	= excerpt
    d["url"]		= url
    d["blog_name"]	= blog_name

    call_script(site,"methods/addTrackbackHook",d)

#rotorkey

def make_rotorkey():
    l = long(time() % 12 + 8)
    k = ""
    for i in range(l):
        k = k + chr(randint(ord('A'),ord('Z')))
    return k

#other utility methods

def make_unique(l):
    #Make unique items in list and return it
    d = {}
    r_l = []
    for item in l:
        if not d.has_key(item):
            r_l.append(item)
            d[item] = 0
    return r_l


def get_property_dict():
    ret_d = (
        {'id':'title', 'type':'string','mode':'w'},

        #Settings for blog
        #description
        {'id':'blog_description','type':'string','mode':'w'},
        {'id':'blog_url', 'type':'string','mode':'w'},
        {'id':'blog_long_description', 'type':'text','mode':'w'},
        {'id':'footer', 'type':'text','mode':'w'},
        {'id':'author_profile', 'type':'text','mode':'w'},
        #character code
        {'id':'management_page_charset', 'type':'string','mode':'w'},
        {'id':'trackback_char_code', 'type':'string','mode':'w'},
        #HTML tag for body,comments
        {'id':'body_tags', 'type':'string','mode':'w'},
        {'id':'comment_tags', 'type':'string','mode':'w'},
        #Optional
        #length for modules
        {'id':'module_item_count', 'type':'int','mode':'w'},
        {'id':'top_days', 'type':'int','mode':'w'},
        {'id':'category_length', 'type':'int','mode':'w'},

        #PING Servers.
        {'id':'ping_servers', 'type':'lines','mode':'w'},
        {'id':'use_permalink_on_ping', 'type':'boolean','mode':'w'},

        #comment
        {'id':'require_name', 'type':'boolean','mode':'w'},
        {'id':'anonymous_name', 'type':'string','mode':'w'},
        {'id':'require_email', 'type':'boolean','mode':'w'},

        #moderation
        {'id':'moderate_comment', 'type':'boolean','mode':'w'},
        {'id':'moderate_trackback', 'type':'boolean','mode':'w'},

        {'id':'month_names', 'type':'text','mode':'w'},

        #formats
        {'id':'default_format', 'type':'int','mode':'w'},

        {'id':'use_epoz_service', 'type':'boolean','mode':'w'},
        {'id':'epoz_width', 'type':'int','mode':'w'},
        {'id':'epoz_height', 'type':'int','mode':'w'},

        #skin
        {'id':'skin_name', 'type':'string','mode':'w'}, 

        #moblog
        {'id':'mailhost', 'type':'string','mode':'w'},
        {'id':'moblog_user', 'type':'string','mode':'w'},
        {'id':'moblog_password', 'type':'string','mode':'w'},
        {'id':'entry_password', 'type':'string','mode':'w'},
        {'id':'useapop', 'type':'boolean','mode':'w'},
        {'id':'author_for_moblog', 'type':'string','mode':'w'},
        {'id':'moblog_default_category', 'type':'int','mode':'w'},
        {'id':'moblog_email_addr', 'type':'string','mode':'w'},
        {'id':'body_separater', 'type':'string','mode':'w'},
        {'id':'image_serial', 'type':'int','mode':'w'},
        {'id':'allow_comment_moblog', 'type':'boolean','mode':'w'},
        {'id':'allow_trackback_moblog', 'type':'boolean','mode':'w'},

        #blog client
        {'id':'blogclient_char_code', 'type':'string','mode':'w'},
        {'id':'blog_client_default_category', 'type':'int','mode':'w'},

        )

    return ret_d


def required_object_list():
    ret_l = [
            "index_html", \
            "entry_html", \
            "previewcomment_html" \
            ]

    return ret_l


def get_skin_dicts(self):
    #Get dictionary for skin,id(in key),list of skin object,list of skin properties.
    skins = {}
    for obj in self.skin.objectValues(["Folder"]):
        skins[obj.id] = {}
        try:
            skins[obj.id]["skin_folder"] = obj
            #call Script(Python) to get skin specific settings.
            skins[obj.id]["skin_objects"] = obj.skin_objects()
            skins[obj.id]["skin_properties"] = []
            skins[obj.id]["skin_properties"] = obj.skin_properties()
        except:
            pass
        if not skins[obj.id].has_key("skin_objects"):
            del skins[obj.id]

    return skins


def add_skin_folder(skin_folder,skinid,path,globals,encode=""):
    #Add folder
    skin_folder.manage_addFolder(skinid)
    folder = skin_folder._getOb(skinid)
    

    #Add skin folder from File
    fullpath = os.path.join(package_home(globals),path)

    add_files_to_folder(fullpath,folder,"SKIN:%s" % (skinid),encode)


def addDTML(path,id,title,parentfolder,encode=""):
    f=open(path)
    body=f.read()
    #if encode:
    #    body=convert_charcode(body,encode,code_euc)
    f.close()
    parentfolder.manage_addDTMLMethod(id,title,body)


def addPythonScript(path,id,title,parentfolder):
    f=open(path)
    body=f.read()
    f.close()
    manage_addPythonScript(parentfolder,id)
    parentfolder._getOb(id).write(body)


def addGIF(path,id,title,parentfolder):
    f=open(path)
    body=f.read()
    f.close()
    new_id = parentfolder.manage_addImage(id,body,title=title)
    img_obj = parentfolder.__getitem__(new_id)
    img_obj.content_type = 'image/gif'


def add_files_to_folder(fullpath,folder,title,encode=""):
    l = listdir(fullpath)
    for fn in l:
        if rfind(fn,".dtml") != -1:
            #Add DTML Method
            id = replace(fn,".dtml","")
            addDTML(os.path.join(fullpath,fn),id,title,folder,encode)
        elif rfind(fn,".py") != -1:
            #Add Script(Python)
            id = replace(fn,".py","")
            addPythonScript(os.path.join(fullpath,fn),id,title,folder)


def aplly_skin(self,after,before = "",write_back = 0):
    #Aplly(copy) skin objects for COREBlog instance.

    #Get skin folder ids
    skin_ids = self.skin.objectIds(["Folder"])
    skins = get_skin_dicts(self)

    if not skins.has_key(after):
        raise KeyError,"Skin:%s does not exist." % (after)

    if before and not skins.has_key(before):
        raise KeyError,"Skin:%s does not exist." % (before)

    remain_ids = []
    #Check validations.
    if before:
        sub_object_ids = self.objectIds()
        remain_ids = sub_object_ids
        #Make list of remaining object(after removing before skin objects).
        for id in skins[before]["skin_objects"] + required_object_list():
            if id in remain_ids:
                remain_ids.remove(id)
        #Check conflicts between remaining objects,skin object
        for id in remain_ids:
            if id in skins[after]["skin_objects"]:
                raise KeyError,"Object:%s in Skin(%s) conflicts object in COREBlog root." % (str(id),after)

    for id in required_object_list():
        if not id in skins[after]["skin_objects"]:
            raise KeyError,"Object:%s required for skin." % (str(id))

    #Copy skin objects.
    objSpec = skins[after]["skin_folder"].manage_copyObjects(skins[after]["skin_objects"])

    #This function doesn't work...
    #First,if need,write back current object to skin folder.
    if before:
        #if write_back:
        #    #delete objects in before skin
        #    skins[before]["skin_folder"].manage_delObjects(skins[before]["skin_objects"])
        #    wbSpec = self.manage_copyObjects(skins[before]["skin_objects"])
        #    skins[before]["skin_folder"].manage_pasteObjects(wbSpec)
        ##delete objects in before skin
        for id in skins[before]["skin_objects"]:
            try:
                self.manage_delObjects([id])
            except:
                pass
    #Property managements.
    if before:
        #write back current property values for skin.
        fld = skins[before]["skin_folder"]
        for d in skins[before]["skin_properties"]:
            if fld.hasProperty(d["id"]):
                if self.hasProperty(d["id"]):
                    fld._updateProperty(d["id"],self.getProperty(d["id"]))
            else:
                oldval = ""
                if self.hasProperty(d["id"]):
                    oldval = self.getProperty(d["id"])
                fld.manage_addProperty(d["id"],oldval,d["type"])
            #delete properties in before skin
            if self.hasProperty(d["id"]):
                self.manage_delProperties((d["id"],))

    #Copy property values in after skin
    fld = skins[after]["skin_folder"]
    for d in skins[after]["skin_properties"]:
        value = ""
        if fld.hasProperty(d["id"]):
            value = fld.getProperty(d["id"])
        if self.hasProperty(d["id"]):
            self._updateProperty(d["id"],value)
        else:
            self.manage_addProperty(d["id"],value,d["type"])


    self.manage_pasteObjects(objSpec)


def split_in_newline(s):
    s = replace(s,"\r","")
    ret_l = []
    for line in split(s,"\n"):
        ret_l.append(line)

    return ret_l


def send_ping(serverurl,blogtitle,url,char_code = "euc_jp",
                version_str = "COREBlog",fromcode=""):
    blogtitle = convert_charcode(blogtitle,char_code,fromcode)
    svr = Server(serverurl)
    Transport.user_agent = version_str
    resp = svr.weblogUpdates.ping(blogtitle,url)
    return resp


def change_site_encode(self,tocode = "euc_jp",fromcode = ""):
    #Change Entry charset.
    count = len(self.entry_list)
    for c in range(0,count):
        id = self.entry_list[c]
        obj = self.getEntry(id)
        #convert entry charset
        if obj.title:
            obj.title = convert_charcode(obj.title,tocode,fromcode)
        if obj.subtitle:
            obj.subtitle = convert_charcode(obj.subtitle,tocode,fromcode)
        if obj.author:
            obj.author = convert_charcode(obj.author,tocode,fromcode)
        if obj.body:
            obj.body = convert_charcode(obj.body,tocode,fromcode)
        if obj.rendered_body:
            obj.rendered_body = convert_charcode(obj.rendered_body,tocode,fromcode)
        if obj.extend:
            obj.extend = convert_charcode(obj.extend,tocode,fromcode)
        if obj.excerpt:
            obj.excerpt = convert_charcode(obj.excerpt,tocode,fromcode)

        #convert comment charset
        for com in obj.comment_list(consider_moderation=0):
            if com.title:
                com.title = convert_charcode(com.title,tocode,fromcode)
            if com.author:
                com.author = convert_charcode(com.author,tocode,fromcode)
            if com.body:
                com.body = convert_charcode(com.body,tocode,fromcode)
            if com.email:
                com.email = convert_charcode(com.email,tocode,fromcode)
            if com.url:
                com.url = convert_charcode(com.url,tocode,fromcode)

        #convert trackback charset
        for tbk in obj.trackback_list(consider_moderation=0):
            if tbk.title:
                tbk.title = convert_charcode(tbk.title,tocode,fromcode)
            if tbk.excerpt:
                tbk.excerpt = convert_charcode(tbk.excerpt,tocode,fromcode)
            if tbk.url:
                tbk.url = convert_charcode(tbk.url,tocode,fromcode)
            if tbk.blog_name:
                tbk.blog_name = convert_charcode(tbk.blog_name,tocode,fromcode)

    #Change Category charset
    for cat in self.category_list():
        if cat.name:
            cat.name = convert_charcode(cat.name,tocode,fromcode)
        if cat.description:
            cat.description = convert_charcode(cat.description,tocode,fromcode)

    pmap = self.propertyMap()
    for d in pmap:
        if d["type"] in ["string","text"]:
            #change charset
            prop = self.getProperty(d["id"])
            if prop:
                self._updateProperty(d["id"],convert_charcode(prop,tocode,fromcode))



def convert_charcode(s,codestr,fromcodestr=""):
    #convert charcode (for Japanese)
    if type(s) == type(u''):
        #unicode -> str
        s = s.encode('utf-8')
        fromcodestr = code_utf8

    retstr = s

    try:
        import pykf
        pkf_fromcode = 0
        if not fromcodestr:
            #fromcode is unknown... so do 'guess'
            pkf_fromcode = pykf.guess(s)
            if pkf_fromcode == pykf.EUC:
                fromcodestr = code_euc
            elif pkf_fromcode == pykf.SJIS:
                fromcodestr = code_sjis
            elif pkf_fromcode == pykf.UTF8:
                fromcodestr = code_utf8
            elif pkf_fromcode == pykf.JIS:
                fromcodestr = code_jis
        else:
            #fromcode is known.
            if fromcodestr == code_sjis:
                pkf_fromcode = pykf.SJIS
            elif fromcodestr == code_euc:
                pkf_fromcode = pykf.EUC
            elif fromcodestr == code_utf8:
                pkf_fromcode = pykf.UTF8
            elif fromcodestr == code_jis:
                pkf_fromcode = pykf.JIS

        #Do conversion...
        if pkf_fromcode == pykf.UTF8:
            if codestr == code_sjis:
                tocode = "japanese.shift_jis"
            elif codestr == code_euc:
                tocode = "japanese.euc-jp"
            elif codestr == code_jis:
                tocode = "japanese.iso-2022-jp"
            if codestr != code_utf8:
                retstr = unicode(s,'utf-8').encode(tocode)
        elif codestr == code_euc:
            retstr = pykf.toeuc(s,pkf_fromcode)
        elif codestr == code_sjis:
            retstr = pykf.tosjis(s,pkf_fromcode)
        elif codestr == code_utf8:
            #Use JapaneseCodecs...
            fcode = ""
            if fromcodestr == code_sjis:
                fcode = "japanese.shift_jis"
            elif fromcodestr == code_euc:
                fcode = "japanese.euc-jp"
            elif fromcodestr == code_jis:
                fcode = "japanese.iso-2022-jp"
            if fromcodestr != code_utf8:
                retstr = unicode(s, fcode, "ignore").encode('utf8')
    except:
        try:
            import kconv
            to_code = kconv.EUC
            if codestr == code_euc:
                to_code = kconv.EUC
            if codestr == code_sjis:
                to_code = kconv.SJIS
            if codestr == code_utf8:
                to_code = kconv.UTF8
            if codestr != code_us:
                retstr = kconv.Kconv(to_code).convert(s)
        except:
            pass

    return retstr

def is_euc_1(buff,pos):
    st = 0 # 0:ascii 1:euc1
    for pos in range(0,pos):
        if 0xa1 <= ord(buff[pos]) <= 0xfe:
            if st == -1:
                st = 0
            st = (st + 1) % 2
        else:
            st = -1
    ret = 0
    if st == -1:
        ret = 0
    elif st == 1:
        ret = 1

    return ret


def is_sjis_1(buff,pos):
    if (ord(buff[pos]) >= 0x81 and ord(buff[pos]) <= 0x9f) or \
       (ord(buff[pos]) >= 0xe0 and ord(buff[pos]) <= 0xff):
       return 1
    return 0

def get_string_part(s,length,codestr):
    # return string in certain range(consider Japanese 2byte codes).
    ret_str = s
    if len(s) > length:
        if codestr == code_euc:
            if is_euc_1(s,length) == 1:
                length = length - 1
            ret_str = s[:length]
        elif codestr == code_sjis:
            if is_sjis_1(s,length+1):
                length = length - 1
            ret_str = str[:length]
        elif codestr == code_utf8:
            try:
                us = unicode(ret_str,'utf-8')
                ret_str = us[:length].encode('utf8')
            except:
                ret_str = ret_str[:length]
        else:
            ret_str = s[:length] + "weofije"
    return ret_str


#Empty class for initializing ZCTextIndex

class EmptyClass: pass

#Utility methods for XML-RPC

def parse_blogger_post(content):
    #Utility method to parse content from blogger API,
    #and returns tupple of (title,category(list),content area
    flags = re.DOTALL | re.IGNORECASE | re.MULTILINE
    title_pat = """<title>(.*?)</title>"""
    t_pat = re.compile(title_pat,flags)
    category_pat = """<category>(.*?)</category>"""
    c_pat = re.compile(category_pat,flags)
    t_l = t_pat.findall(content)
    if t_l:
        t = t_l[0]
    else:
	t = ""
    body = t_pat.sub("",content)
    c_l = c_pat.findall(content)
    body = c_pat.sub("",body)
    return t,c_l,body

