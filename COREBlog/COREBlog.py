##############################################################################
#
# COREBlog.py
# Classes for COREBlog Site
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
#
# This software uses stripogram,Copyright (c) 2001 Chris Withers
#
##############################################################################

#Import modules from Python lib.
from copy import copy
from string import join,split,find,replace
from time import time,mktime,localtime,strftime
from calendar import calendar,monthrange,setfirstweekday,weekday,monthcalendar
from calendar import SUNDAY,MONDAY,SATURDAY
from types import IntType,ListType
from poplib import POP3
from StringIO import StringIO
from rotor import newrotor
from base64 import decodestring,encodestring
import os


#Import modules,classes from Zope.
#from zLOG import LOG,ERROR
from Globals import PersistentMapping,HTMLFile,MessageDialog,InitializeClass
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from BTrees.IOBTree import IOBTree,IOSet
from BTrees.IIBTree import IISet
from App.Common import package_home
from DateTime import DateTime

from Products.ZCatalog import ZCatalog

from stripogram import html2safehtml,html2text

#Import modules,classes from COREBlog.
from Entry import Entry,excerpt_length,\
                     comment_none,comment_open,comment_closed,\
                     trackback_none,trackback_open,trackback_closed,format_html,format_plain, \
		     get_rendered_body
from ObjectBase import Comment,Trackback
from Category import Category
from AuthBridge import AuthBridge
from utility import r2i,sec_to_date_int,day_to_date_int,get_yesterday,get_tomorrow, \
                    get_yesterday_t,get_tomorrow_t, \
                    remove_html,validate_html,getNewID,make_unique, \
                    call_addentry_hook, \
                    get_property_dict,required_object_list, \
                    get_skin_dicts,aplly_skin,addDTML,addGIF, \
                    convert_charcode, \
                    get_string_part,change_site_encode, \
                    add_skin_folder,add_files_to_folder, \
                    EmptyClass,split_in_newline, \
                    make_rotorkey, \
                    code_euc,code_sjis,code_utf8,code_jis,code_us, \
                    parse_blogger_post
from jmimetool import Message
from MailHolder import MailHolder
from permissions import View,ManageCOREBlog,AddCOREBlogEntries,\
                        AddCOREBlogComments,ModerateCOREBlogEntries

from Products.PythonScripts import PythonScript


__doc__="""Zope Blog Product 'COREBlog:COREBlog'
$Id: COREBlog.py,v 1.2 2004/11/22 15:02:37 tarmo Exp $"""

__version__='$Revision: 1.2 $'[11:-2]
__product_version__ = "COREBlog 0.73b"


manage_addCOREBlogForm=HTMLFile('dtml/manage_addCOREBlogForm',globals())


class COREBlog(ZCatalog.ZCatalog):
    """COREBlog - A Weblog Product for Zope"""

    meta_type = 'COREBlog'
    description = 'A Weblog Product for Zope'

    #Interfaces

    #Set default security settings
    security = ClassSecurityInfo()
    security.setPermissionDefault(ManageCOREBlog, ('Manager',))
    security.setPermissionDefault(AddCOREBlogEntries,('Manager',))
    security.setPermissionDefault(AddCOREBlogComments,('Anonymous','Manager',))
    security.setPermissionDefault(ManageCOREBlog,('Manager',))
    security.setPermissionDefault(View,('Anonymous','Manager',))

    icon = 'misc_/COREBlog/coreblog_img'

    #allowing tags
    body_tags_id = "body_tags"
    comment_tags_id = "comment_tags"

    manage_options=( \
                {'label':'Entries', 'icon':'', 'action':'manage_entryForm', 'target':'manage_main'},     
                {'label':'Categories', 'icon':'', 'action':'manage_categoryForm', 'target':'manage_main'},     
                {'label':'Settings', 'icon':'', 'action':'manage_editSettingForm', 'target':'manage_main'},     
                {'label':'Skins', 'icon':'', 'action':'manage_editSkinsettingForm', 'target':'manage_main'},     
                {'label':'Contents', 'icon':icon, 'action':'manage_main', 'target':'manage_main'},     
                {'label':'View', 'icon':'', 'action':'index_html', 'target':'manage_main'},     
                {'label':'Properties', 'icon':'', 'action':'manage_propertiesForm', 'target':'manage_main'},
                {'label':'Security', 'icon':'', 'action':'manage_access', 'target':'manage_main'},

                #{'label': 'Indexes',            # TAB: Indexes
                # 'action': 'manage_catalogIndexes',
                # 'help': ('ZCatalog','ZCatalog_Indexes.stx')},
                #{'label': 'Metadata',           # TAB: Metadata
                # 'action': 'manage_catalogSchema',
                # 'help':('ZCatalog','ZCatalog_MetaData-Table.stx')},
                #{'label': 'Find Objects',       # TAB: Find Objects
                # 'action': 'manage_catalogFind',
                # 'help':('ZCatalog','ZCatalog_Find-Items-to-ZCatalog.stx')},
                #{'label': 'Advanced',           # TAB: Advanced
                # 'action': 'manage_catalogAdvanced',
                # 'help':('ZCatalog','ZCatalog_Advanced.stx')},
                
                {'label':'Undo', 'icon':'', 'action':'manage_UndoForm', 'target':'manage_main'}
                )

    #Entry
    security.declareProtected(ManageCOREBlog, 'manage_entryForm')
    manage_entryForm = HTMLFile('dtml/manage_listEntryForm',globals())
    security.declareProtected(ManageCOREBlog, 'manage_addEntryForm')
    manage_addEntryForm = HTMLFile('dtml/manage_addEntryForm',globals())

    #Category
    security.declareProtected(ManageCOREBlog, 'manage_categoryForm')
    manage_categoryForm = HTMLFile('dtml/manage_listCategoryForm',globals())
    security.declareProtected(ManageCOREBlog, 'manage_addCategoryForm')
    manage_addCategoryForm = HTMLFile('dtml/manage_addCategoryForm',globals())
    security.declareProtected(ManageCOREBlog, 'manage_editCategoryForm')
    manage_editCategoryForm = HTMLFile('dtml/manage_editCategoryForm',globals())

    #Settings
    security.declareProtected(ManageCOREBlog, 'manage_editSettingForm')
    manage_editSettingForm = HTMLFile('dtml/manage_editSettingForm',globals())
    security.declareProtected(ManageCOREBlog, 'manage_editSkinsettingForm')
    manage_editSkinsettingForm = HTMLFile('dtml/manage_editSkinsettingForm',globals())

    security.declareProtected(View, 'cb_script_widget')
    cb_script_widget = HTMLFile('dtml/coreblog_script_widget.js',globals())


    #methods mapping for XML-RPC
    #method name : [index of username,index of passwoed,remapped_method(optional)]

    #mapping dictionaries
    blogger_map = {
                    "newPost"		:[2,3],
                    "editPost"		:[2,3],
                    "deletePost"	:[2,3],
                    "getRecentPosts"	:[2,3],
                    "getUsersBlogs"	:[1,2],
                    "getUserInfo"	:[1,2],
                      }

    metaweblog_map = { 
                    "newPost"		:[1,2,'newPostMW'],
                    "editPost"		:[1,2,'editPostMW'],
                    "getPost"		:[1,2],
                    "getRecentPosts"	:[1,2,'getRecentPostsMW'],
                    #"newMediaObject"	:[1,2],
                      }

    mt_map = {
                    "getRecentPostTitles":[1,2],
                    "getCategoryList"	:[1,2],
                    "getPostCategories"	:[1,2],
                    "setPostCategories"	:[1,2],
                    "editPost"		:[1,2],
                    "getPost"		:[1,2],
                    "supportedMethods"	:[],
                    #"supportedTextFilters":[],
                    "getTrackbackPings"	:[],
                    "publishPost"	:[1,2],
                      }

    #Blogger API
    security.declareProtected(View, 'blogger')
    blogger = AuthBridge("blogger")
    blogger.set_proc_map(blogger_map)

    #metaWeblog API
    security.declareProtected(View, 'metaWeblog')
    metaWeblog = AuthBridge("metaWeblog")
    metaWeblog.set_proc_map(metaweblog_map)

    #mt API
    security.declareProtected(View, 'mt')
    mt = AuthBridge("mt")
    mt.set_proc_map(mt_map)

    security.declarePrivate('__init__')
    def __init__(self,id,title='COREBlog',encode="",elements=[]):
        #Creater Function of COREBlog

        self.id = id

        #BTrees for sub objects & reference count
        #Entries
        self.entries = IOBTree()
        self.entry_count = 1
        self.entry_list = IISet()
        #Comments
        self.comments = IOBTree()
        self.comment_count = 1
        self.comment_list = IISet()
        #Trackbacks
        self.trackbacks = IOBTree()
        self.trackback_count = 1
        self.trackback_list = IISet()

        #Entry list for date
        self.datemap = IOBTree()

        #Categories
        self.categories = IOBTree()
        self.category_count = 1

        #folders
        self.manage_addFolder('methods','Folder for Hook methods')
        self.manage_addFolder('skin','Folder for Skin')
        self.manage_addFolder('modules','Folder for Modules')
        self.manage_addFolder('images','Folder for Images')

        #rdf/rss
        fullpath = os.path.join(package_home(globals()),"dtml/")
        addDTML(os.path.join(fullpath,"rdf10_xml.dtml"),"rdf10_xml","RDF 1.0",self)
        addDTML(os.path.join(fullpath,"rdf91_xml.dtml"),"rdf91_xml","RDF 0.91",self)
        addDTML(os.path.join(fullpath,"rsd_xml.dtml"),"rsd_xml","RSD 1.0",self)

        #bannar
        imagepath = os.path.join(package_home(globals()),"www/")
        addGIF(os.path.join(imagepath,"corebloglogo_gray.gif"),"corebloglogo","COREBlog",self.images)

        #Add default skin
        add_skin_folder(self.skin,"default","dtml/skin/default/",globals(),encode)

        #properties
        self._properties = (get_property_dict())

        #initialize properties
        dics = get_property_dict()
        for d in dics:
            key = d["id"]
            if d["type"] in ("string","text"):
                self._updateProperty(key,"")
            elif d["type"] in ("int","long"):
                self._updateProperty(key,0)
            elif d["type"] in ("boolean",):
                self._updateProperty(key,0)

        #set defaults
        self._updateProperty("blog_url","")
        self._updateProperty("module_item_count",10)
        self._updateProperty("top_days",4)
        self._updateProperty("category_length",20)
        self._updateProperty("skin_name","default")
        self._updateProperty("require_name",1)
        self._updateProperty("use_epoz_service",0)
        self._updateProperty("epoz_width",500)
        self._updateProperty("epoz_height",250)
        self._updateProperty("ping_servers","")

        self.title = title

        #add default modules
        fullpath = os.path.join(package_home(globals()),"dtml/modules/")
        add_files_to_folder(fullpath,self.modules,"")

        #apply default skin
        fullpath = os.path.join(package_home(globals()),"dtml/skin/default/")
        add_files_to_folder(fullpath,self,"SKIN:default",encode)

        #set property for default skin
        skf = self.skin.default
        prop_dict = [ {"id":"body_font",	"type":"string","value":"verdana,georgia,arial,sans-serif"},
                      {"id":"background_color",	"type":"string","value":"FFF"},
                      {"id":"font_color",	"type":"string","value":"000"},
                      {"id":"banner_font",	"type":"string","value":"arial,verdana,georgia, sans-serif"},
                      {"id":"banner_color",	"type":"string","value":"FFF"},
                      {"id":"banner_font_color","type":"string","value":"000"},
                      {"id":"color1",		"type":"string","value":"fff"},
                      {"id":"color2",		"type":"string","value":"C0C0C0"},
                      {"id":"color3",		"type":"string","value":"808080"},
                      {"id":"color4",		"type":"string","value":"606060"},
                      {"id":"sidebox_background","type":"string","value":"FFF"}
                    ]
        for d in prop_dict:
           skf.manage_addProperty(d["id"],d["value"],d["type"])
           skf._updateProperty(d["id"],d["value"])
           self.manage_addProperty(d["id"],d["value"],d["type"])
           self._updateProperty(d["id"],d["value"])
        #try to add lexicon...
        try:
            from Products.ZCTextIndex.ZCTextIndex import manage_addLexicon

            if elements:
                manage_addLexicon(self,id='lexicon',elements = elements)
        except:
            pass

        #Build ZCatalog index
        try:
            self.buildIndex(self.id, self.title)
        except:
            pass

    def blog(self):
        return self

    security.declareProtected(View, 'get_product_version')
    def get_product_version(self):
        return __product_version__ + "(Rev. %s)" % __version__


    security.declareProtected(View, 'blog_title')
    def blog_title(self):
        """ return title of blog """
        return self.title


    security.declareProtected(View, 'blogurl')
    def blogurl(self):
        """ url of the COREBlog """
        prop_url = self.getProperty("blog_url")
        url = self.absolute_url()
        if prop_url:
            url = prop_url
        return url


    security.declarePublic('__len__')
    def __len__(self):
        return 1


    security.declareProtected(View, '__getitem__')
    def __getitem__(self,id):
        """ return sub objects """
        #raise 'BOBO','COREBlog: %s <p> %s ' % (id,str(self.REQUEST))

        # Get rid of first character
        id = id[1:]

        # Cast id to 'int'
        try:
            if not isinstance(id,IntType):
                id=int(id)
        except ValueError:
            raise KeyError,id

        if not self.entries.has_key(id):
            raise KeyError,id

        try:
            obj = self.entries[id].__of__(self)
        except:
            pass
        return self.entries[id].__of__(self)

    #
    # Methods for Entry Handling
    #


    security.declareProtected(AddCOREBlogEntries, 'manage_addEntry')
    def manage_addEntry(self,author,body,extend,excerpt, \
                        main_category,moderated,sub_category=[], \
                        title="",subtitle="", entry_date="", \
                        format=0,allow_comment=0,receive_trackback=0,
                        trackback_url="",sendnow=0,REQUEST=None,
                        sendping = 1,**kw):
        """Add a Entry object"""

        #validaters
        v_h = self.removeHTML
        v_b = self.validateEntryBody
        v_c = self.validateCommentBody

        if REQUEST and (REQUEST.form.has_key('preview') or not title):
            if not entry_date:
                entry_date = str(DateTime())
            cats = []
            try:
                cats.append(self.getCategory(main_category)[0])
                for ct in sub_category:
                    cats.append(self.getCategory(int(ct))[0])
            except:
                pass

            if not title:
                kw['worning_message'] = "Title is required."

            kw['date_created'] = lambda x=entry_date : DateTime(x)
            kw['year_created'] = lambda x=entry_date: DateTime(x).year()
            kw['day_created'] = lambda x=entry_date: DateTime(x).day()
            kw['month_created'] = lambda x=entry_date: DateTime(x).month()
            kw['entry_category_list'] = lambda x=cats: x
            kw['tbpingurl'] = lambda : "not defined on pewview"
            kw['entry_title'] = lambda x=v_h(title) : x
	    kw['title'] = v_h(title)
            kw['subtitle'] = v_h(subtitle)
            kw['count_comment'] = lambda : 0
            kw['count_trackback'] = lambda : 0
            kw['rendered_body'] = v_b(body)
            kw['body'] = v_b(body)
            #Set control values
            kw['noheader'] = 1
            kw['nocomment'] = 1
            kw['nocommentform'] = 1

            #Returns addEntryForm
            return self.manage_addEntryForm(self,REQUEST,**kw)

        new_id = self.getNewEntryID()
        #remove category duplications
        cats_s = [main_category] + sub_category
        cats = []
        for id in cats_s:
            if not self.categories.has_key(int(id)):
                raise ValueError,"Category of ID(%s) does not exist." % (str(id))
            cats.append(int(id))
        cats = make_unique(cats)

        if not excerpt:
            prebody = html2text(v_h(get_rendered_body(body,format)))
            excerpt = get_string_part(prebody,excerpt_length,self.get_charcode())
            if len(excerpt) < len(prebody):
                excerpt = excerpt + "..."

        tburls = split_in_newline(trackback_url)

        crsec = time()
        if entry_date:
            crsec = int(DateTime(entry_date).millis()/1000)

        obj = Entry(new_id, \
                        v_h(author),v_b(body),v_c(extend),v_c(excerpt), \
                        moderated,title,subtitle,cats, \
                        format,allow_comment,receive_trackback, \
                        tburls,crsec)
        obj.__of__(self)
        self.setEntry(new_id,obj)
        self.entry_list.insert(new_id)

        #add category count
        if moderated:
            self.addCategoryCount(cats[0],1)

        self._p_changed = 1

        #Catalogging...
        obj.index(self)

        call_addentry_hook(self,new_id,v_h(author),v_b(body),v_c(extend),v_c(excerpt), \
                        moderated,title,subtitle,cats, \
                        format,allow_comment,receive_trackback)

        pingservers_prop = self.getProperty("ping_servers")
        pingservers = []
        if pingservers_prop:
            for srv in pingservers_prop:
                if srv:
                    pingservers.append(srv)

        if moderated:
            if REQUEST:
                if sendnow and obj.count_sending_trackback() > 0:
                    return REQUEST.RESPONSE.redirect('./' + str(new_id) + "/manage_sendPINGTrackback")
                elif pingservers and len(pingservers) > 0:
                    return REQUEST.RESPONSE.redirect('./' + str(new_id) + "/manage_sendPINGTrackback")
                else:
                    return REQUEST.RESPONSE.redirect('manage_entryForm')
            elif sendping:
                #Entry might add via mail....
                obj.aq_parent = self
                obj.sendPING()
        else:
            if REQUEST:
                return REQUEST.RESPONSE.redirect('manage_entryForm')

        return new_id


    security.declareProtected(ManageCOREBlog, 'manage_deleteEntries')
    def manage_deleteEntries(self,ids,REQUEST=None):
        """Delete Entries in list(ids)"""
        if type(ids) != ListType:
            raise TypeError,"Paramater 'ids' must be a ListType."
        for id in ids:
            int_id = int(id)
            if not self.entries.has_key(int_id):
                raise ValueError,"A entry(ID:%s) does not exist." % (str(int_id))
            self.deleteEntry(int_id)
        if REQUEST:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    security.declarePrivate('setEntry')
    def setEntry(self,id,obj):
        #Append a Entry object to self.entries
        self.entries[id] = obj

        #Append Entry to date_map,considering moderation
        self.setDatemap(obj)

        self._p_changed = 1


    security.declarePrivate('deleteEntry')
    def deleteEntry(self,id):
        int_id = int(id)
        #delete entry
        obj = self.getEntry(int_id)

        #remove from entry_list
        self.entry_list.remove(int_id)

        #remove from date_map
        self.removeIDFromDatemap(obj.year_created(), \
                obj.month_created(),obj.day_created(),int_id)

        #delete comments of entry
        obj.deleteAllComments()

        #delete trackback of entry
        obj.deleteAllTrackbacks()

        #decrement category count
        if obj.category:
            self.addCategoryCount(obj.category[0],-1)

        #delete from IOBtree entries
        del self.entries[int_id]

        self._p_changed = 1


    security.declarePrivate('getEntry')
    def getEntry(self,id):
        #Return a Entry object
        int_id = int(id)
        if not self.entries.has_key(int_id):
            return None
        else:
            obj = self.entries[int_id].__of__(self)
            return obj

    security.declareProtected(View, 'get_entry')
    def get_entry(self,id):
        """puglic interface for getting entry object from id"""
        return self.getEntry(id)

    #Indexing

    security.declarePrivate('buildIndex')
    def buildIndex(self,id,title):
        if not hasattr(self,'_catalog'):
            ZCatalog.ZCatalog.__init__(self,id,title)

        for name in self.indexes():
            self.delIndex(name)

        index_dict = [ {"key":"author","type":"FieldIndex"},
                       {"key":"search_text","type":"ZCTextIndex"},
                       {"key":"title","type":"ZCTextIndex"},
                       {"key":"created","type":"FieldIndex"}
                     ]

        for d in index_dict:
            if d["type"] != "ZCTextIndex":
                self.addIndex(d["key"],d["type"])
            else:
                extras = EmptyClass()
                extras.doc_attr = d["key"]
                extras.index_type = 'Okapi BM25 Rank'
                extras.lexicon_id = 'lexicon'
                self.addIndex(d["key"],d["type"],extra=extras)
        for name in self.schema():
            self.delColumn(name)

        catalog_columns = ['id','title','author','created']

        for name in catalog_columns:
            self.addColumn(name,'')


    security.declareProtected(ManageCOREBlog, 'recatalogEntries')
    def recatalogEntries(self,REQUEST=None):
        """ Recatalog all Entries """
        self.buildIndex(self.id, self.title)
        self._catalog.clear()

        for obj in self.entry_items():
            obj.index(self)
        if REQUEST is not None:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    #Listing

    security.declareProtected(View, 'entry_items')
    def entry_items(self,start=0,count=-1,consider_moderation = 1):
        """Return list of Entry."""
	start = r2i(start,0)
	count = r2i(count,-1)
	consider_moderation = r2i(consider_moderation,1)
        l = []
        list_c = len(self.entry_list)
        if count == -1:
            count = list_c
        for c in range(start,count):
            if list_c <= c:
                #index out of range
                break
            id = self.entry_list[c]
            obj = self.getEntry(id)
            if not consider_moderation or obj.moderated:
                l.append(obj)
        return l


    security.declareProtected(View, 'rev_entry_items')
    def rev_entry_items(self,start=0,count=-1,consider_moderation = 1):
        """Return list of Entry(reversed indexing)."""
	start = r2i(start,0)
	count = r2i(count,-1)
	consider_moderation = r2i(consider_moderation,1)
        l = []
        if count == -1:
            count = len(self.entry_list)
        l_e = len(self.entry_list) - 1
        for c in range(start,start+count):
            if l_e < c:
                #index out of range
                break
            id = self.entry_list[l_e - c]
            obj = self.getEntry(id)
            if (not consider_moderation) or obj.moderated:
                l.append(obj)
        return l


    security.declareProtected(View, 'day_entry_items')
    def day_entry_items(self,year,month,day):
        """Return entries of the day"""
        try:
            int_year = int(year)
            int_month = int(month)
            int_day = int(day)
        except:
            return []

        d_set = self.getExistingDateSet(int_year,int_month,int_day)

        if not d_set:
            return []

        ent_list = []
        for entry_id in d_set:
            obj = self.getEntry(entry_id)
            obj.__of__(self)
            ent_list.append(obj)
        return ent_list


    security.declareProtected(View, 'rev_day_entry_items')
    def rev_day_entry_items(self,count=1,start_year=0,start_month=0,start_day=0):
        """Return list of Entry,based on date(reversed indexing)."""
	count = r2i(count,0)
	start_year = r2i(start_year,0)
	start_month = r2i(start_month,0)
	start_day = r2i(start_day,0)
        if start_year == 0 or start_month == 0 or start_day == 0:
            #Base date is today
            t = localtime(time())
            year = t[0]
            month = t[1]
            day = t[2]
        else:
            year = start_year
            month = start_month
            day = start_day

        ent_l = []
        if not self.datemap:
            #No entry...
            return ent_l
        c = 0
        day_l = []
        year_list = list(self.datemap.keys())
        year_list.sort()
        year_list.reverse()
        #start from 'year'
        if year != year_list[0]:
            for key in year_list:
                if key > year:
                    year_list.remove(key)

        for y_key in year_list:
            month_set = self.datemap[y_key]
            month_list = list(self.datemap[y_key].keys())
            month_list.sort()
            month_list.reverse()
            if year == y_key and month_list:
                #start from 'month'
                for m_key in month_list:
                    if m_key > month:
                        month_list.remove(m_key)
            for m_key in month_list:
                day_set = month_set[m_key]
                day_list = list(month_set[m_key].keys())
                day_list.sort()
                day_list.reverse()
                if year == y_key and month == m_key and day_list:
                    #start from 'day'
                    for d_key in day_list:
                        if d_key > day:
                            day_list.remove(d_key)
                for d_key in day_list:
                    day_l = list(day_set[d_key])
                    day_l.reverse()
                    for id in day_l:
                        obj = self.getEntry(id)
                        obj.__of__(self)
                        ent_l.append(obj)
                    c = c + 1
                    if c >= count:
                        break
                if c >= count:
                    break
            if c >= count:
                break

        return ent_l


    security.declareProtected(View, 'month_entry_items')
    def month_entry_items(self,count=1,year=0,month=0):
        """Return list of Entry on the month."""
	count = r2i(count,1)
        year = r2i(year,0)
        month = r2i(month,0)
        if year == 0 or month == 0:
            #Base date is today
            t = localtime(time())
            show_year = t[0]
            show_month = t[1]
        else:
            show_year = int(year)
            show_month = int(month)
        show_day = 1
        ent_l = []
        if not self.datemap:
            #No entry...
            return ent_l

        if not self.getExistingDateSet(show_year,show_month,show_day):
            #There is no entry on the date.
            #So we are going to find date has some entry.
            while not self.getExistingDateSet(show_year,show_month,show_day) and \
                year == show_year and month == show_month:
                show_year,show_month,show_day = get_tomorrow_t(show_year,show_month,show_day)
        if show_year != year or show_month != month:
            return []

        c_year = show_year
        c_month = show_month
        while c_year == show_year and c_month == show_month:
            day_l = list(self.getExistingDateSet(show_year,show_month,show_day))
            for id in day_l:
                obj = self.getEntry(id)
                ent_l.append(obj)
            c_year = show_year
            c_month = show_month
            #get 'tomorrow'
            show_year,show_month,show_day = get_tomorrow_t(show_year,show_month,show_day)
            while not self.getExistingDateSet(show_year,show_month,show_day) and \
                c_year == show_year and c_month == show_month:
                show_year,show_month,show_day = get_tomorrow_t(show_year,show_month,show_day)
        return ent_l


    security.declareProtected(View, 'month_archive_items')
    def show_date(self,date,format):
        """Returns a pretty date."""
        return strftime(format,localtime(date))

    security.declareProtected(View, 'month_archive_items')
    def month_archive_items(self,count=1,start_year=0,start_month=0):
        """ Return list of month archive. """
	count = r2i(count,1)
	start_year = r2i(start_year,0)
	start_month = r2i(start_month,0)
        if start_year == 0 or start_month == 0 or start_day == 0:
            #Base date is today
            t = localtime(time())
            year = t[0]
            month = t[1]
        else:
            year = year
            month = month

        ret_l = []
        cnt = 100   #limitter
        while cnt > 0 and count > 0:
            if not self.datemap.has_key(year):
                break;
            year_s = self.datemap[year]
            if year_s.has_key(month):
                ret_l.append({"year":year,"month":month})
                count = count - 1
            month = month - 1
            if month < 1:
                month = 12
                year = year - 1
            cnt = cnt - 1

        return ret_l


    security.declareProtected(View, 'getMonthName')
    def getMonthName(self,month):
	""" Return month name. """
        m_list = ["January","February","March","April", \
                  "May","June","July","August", \
                  "September","October","November","December"]
        if self.hasProperty("month_names"):
            tmp_mlist = split(self.getProperty("month_names"),",")
            if len(tmp_mlist) == 12:
                m_list = tmp_mlist
        month = int(month)
        if month < 1 or month > 12:
            return ""
        self.get_lang(('common',),self.REQUEST)
        return self.REQUEST['L_'+m_list[month-1]]


    security.declareProtected(View, 'rev_category_entry_items')
    def rev_category_entry_items(self,category_id,start=0,count=-1,consider_moderation = 1):
        """Return list of Entry."""
	category_id = r2i(category_id)
	start = r2i(start,0)
	count = r2i(count,1)
	consider_moderation = r2i(consider_moderation,1)
        l = []
        try:
            int_cat = int(category_id)
        except:
            return []
        list_c = len(self.entry_list)
        if count == -1:
            count = list_c
        for c in range(start,start+count):
            if list_c <= c:
                #index out of range
                break
            id = self.entry_list[c]
            obj = self.getEntry(id)
            if obj.category and obj.category[0] == int_cat:
                if not consider_moderation or obj.moderated:
                    l.append(obj)
        return l


    security.declareProtected(View, 'count_entry')
    def count_entry(self):
        """Return count of Entry."""
        return len(self.entries)


    security.declarePrivate('getNewEntryID')
    def getNewEntryID(self):
        #return new id for entry
        new_id = getNewID(self.entry_count,self.entries)
        self.entry_count = new_id
        return new_id

    #
    # datemap Handling
    #


    security.declarePrivate('getDateSet')
    def getDateSet(self,year,month,day):
        if self.datemap.has_key(year):
            y_set = self.datemap[year]
        else:
            y_set = IOBTree()
            self.datemap[year] = y_set
        if y_set.has_key(month):
            m_set = y_set[month]
        else:
            m_set = IOBTree()
            y_set[month] = m_set
        if m_set.has_key(day):
            d_set = m_set[day]
        else:
            d_set = IOSet()
            m_set[day] = d_set

        return d_set


    security.declarePrivate('getExistingDateSet')
    def getExistingDateSet(self,year,month,day):
        if self.datemap.has_key(year):
            y_set = self.datemap[year]
        else:
            return None
        if y_set.has_key(month):
            m_set = y_set[month]
        else:
            return None
        if m_set.has_key(day):
            d_set = m_set[day]
        else:
            return None

        return d_set


    security.declarePrivate('getExistingMonthSet')
    def getExistingMonthSet(self,year,month):
        if self.datemap.has_key(year):
            y_set = self.datemap[year]
        else:
            return None
        if y_set.has_key(month):
            m_set = y_set[month]
        else:
            return None

        return m_set


    security.declarePrivate('getExistingMonthSet')
    def getExistingMonthSet(self,year,month):
        if self.datemap.has_key(year):
            y_set = self.datemap[year]
        else:
            return None
        if y_set.has_key(month):
            m_set = y_set[month]
        else:
            return None
        return d_set


    security.declarePrivate('setIDToDatemap')
    def setIDToDatemap(self,year,month,day,id):
        d_set = self.getDateSet(year,month,day)
        int_id = int(id)
        d_set.insert(int_id)


    security.declarePrivate('removeIDFromDatemap')
    def removeIDFromDatemap(self,year,month,day,id):
        d_set = self.getDateSet(year,month,day)
        int_id = int(id)
        if d_set.has_key(int_id):
            d_set.remove(int_id)

        #remove year,date
        if self.datemap.has_key(year):
            y_set = self.datemap[year]
            if y_set.has_key(month):
                m_set = y_set[month]
                if not m_set[day]:
                    del m_set[day]
                    if not y_set[month]:
                        del y_set[month]


    security.declarePrivate('setDatemap')
    def setDatemap(self,obj):
        #Consider moderation...
        if obj.moderated:
            self.setIDToDatemap(obj.year_created(),obj.month_created(),obj.day_created(),int(obj.id))
        else:
            self.removeIDFromDatemap(obj.year_created(),obj.month_created(),obj.day_created(),int(obj.id))


    #
    # Methods for Comment Handling
    #

    security.declarePrivate('setComment')
    def setComment(self,id,obj):
        #Append a Comment object to self.comments
        if not self.comments.has_key(id):
            self.comment_list.insert(id)
        self.comments[id] = obj


    security.declarePrivate('deleteComment')
    def deleteComment(self,id):
        #Delete a Comment object from self.comments
        if self.comments.has_key(id):
            del self.comments[id]
            self.comment_list.remove(id)

        self._p_changed = 1


    security.declarePrivate('getComment')
    def getComment(self,id):
        if not self.comments.has_key(id):
            raise KeyError,id
        return self.comments[id]


    #security.declarePrivate('getNewCommentID')
    def getNewCommentID(self):
        #return new id for comments
        new_id = getNewID(self.comment_count,self.comments)
        self.comment_count = new_id
        return new_id


    security.declareProtected(View, 'rev_comment_items')
    def rev_comment_items(self,start=0,count=-1):
        """Return list of Comment(reversed indexing)."""
	start = r2i(start,0)
	count = r2i(count,-1)
        l = []
        if count == -1:
            count = len(self.comment_list)
        l_e = len(self.comment_list) - 1
        while count > 0:
            if l_e < 0:
                #index out of range
                break
            id = self.comment_list[l_e]
            obj = self.getComment(id)
            l_e = l_e - 1
            if obj.moderated:
                l.append(obj)
                count = count - 1
        return l


    security.declareProtected(View, 'count_blog_comment')
    def count_blog_comment(self):
        """return count of Comment."""
        return len(self.comment_list)

    #
    # Methods for Trackback Handling
    #

    security.declarePrivate('setTrackback')
    def setTrackback(self,id,obj):
        #Append a Comment object to self.entries
        if not self.trackbacks.has_key(id):
            self.trackback_list.insert(id)
        self.trackbacks[id] = obj


    security.declarePrivate('deleteTrackback')
    def deleteTrackback(self,id):
        #Delete a Trackback object from self.trackbacks
        if self.trackbacks.has_key(id):
            del self.trackbacks[id]
            self.trackback_list.remove(id)

        self._p_changed = 1


    security.declarePrivate('getTrackback')
    def getTrackback(self,id):
        if not self.trackbacks.has_key(id):
            raise KeyError,id
        return self.trackbacks[id]


    def getNewTrackbackID(self):
        #return new id for trackback
        new_id = getNewID(self.trackback_count,self.trackbacks)
        self.trackback_count = new_id
        return new_id


    security.declareProtected(View, 'rev_trackback_items')
    def rev_trackback_items(self,start=0,count=-1):
        """Return list of Trackback(reversed indexing)."""
	start = r2i(start,0)
	count = r2i(count,-1)
        l = []
        if count == -1:
            count = len(self.trackback_list)
        l_e = len(self.trackback_list) - 1
        while count > 0:
            if l_e < 0:
                #index out of range
                break
            id = self.trackback_list[l_e]
            obj = self.getTrackback(id)
            l_e = l_e - 1
            if obj.moderated:
                l.append(obj)
                count = count - 1
        return l


    security.declareProtected(View, 'count_blog_trackback')
    def count_blog_trackback(self):
        """Return count of Trackback."""
        return len(self.trackback_list)

    #
    # Methods for calendar handling
    #


    security.declareProtected(View, 'get_calendar')
    def get_calendar(self,year=0,month=0,firstweekday=SUNDAY):
        """Reutrn list of days for the month"""
        if year == 0 or month == 0:
            #return calendar of 'now'
            t = localtime(time())
            year = t[0]
            month = t[1]
        else:
            year = int(year)
            month = int(month)

        setfirstweekday(firstweekday)
        days = monthcalendar(year,month)
        week_list = []
        for week in days:
            d_l = []
            for day in week:
                d_l.append({"day":day,"entry_count":self.countEntryOfTheDay(year,month,day)})
            week_list.append(d_l)

        return week_list


    security.declareProtected(View, 'countEntryOfTheDay')
    def countEntryOfTheDay(self,year,month,day):
        """Return count of entry of the day"""

        d_set = self.getExistingDateSet(year,month,day)
        if d_set:
            return len(d_set)
        else:
            return 0

    #
    # Methods for Category Handling
    #


    security.declareProtected(ManageCOREBlog, 'addCategory')
    def addCategory(self,name,description,icon_path="",sec = -1):
        """Add a Category"""
        new_id = self.getNewCategoryID()
        obj = Category(new_id,name,description,icon_path,sec)
        obj.__of__(self)
        self.setCategory(new_id,obj)
        return new_id


    security.declareProtected(ManageCOREBlog, 'manage_addCategory')
    def manage_addCategory(self,name,description,icon_path="",REQUEST=None):
        """Add a Category"""
        self.addCategory(name,description,icon_path)
        #call_script(self,"",{})
        if REQUEST:
            return REQUEST.RESPONSE.redirect('manage_categoryForm')


    security.declareProtected(ManageCOREBlog, 'manage_deleteCategories')
    def manage_deleteCategories(self,ids,REQUEST=None):
        """Delete Category in list(ids)"""
        if type(ids) != ListType:
            raise TypeError,"Paramater 'ids' must be a ListType."
        for id in ids:
            id_s = int(id)
            if not self.categories.has_key(id_s):
                raise ValueError,"A category(ID:%s) does not exist." % (str(id_s))
            obj = self.categories[id_s]
            del self.categories[id_s]
            del obj
        if REQUEST:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    security.declarePrivate('setCategory')
    def setCategory(self,id,obj):
        #Append a Category object to self.entries
        self.categories[id] = obj


    security.declarePrivate('addCategoryCount')
    def addCategoryCount(self,cat_id,delta):
        #add category count
        cat = self.categories[cat_id]
        cat.set_count(cat.get_count()+delta)


    security.declareProtected(View, 'getCategory')
    def getCategory(self,id):
	""" Reruth specific category. """
        id_i = r2i(id)
        if not self.categories.has_key(id_i):
            raise KeyError,id_i
        return (self.categories[id_i],)


    security.declarePrivate('getNewCategoryID')
    def getNewCategoryID(self):
        #return new id for category
        new_id = getNewID(self.category_count,self.categories)
        self.category_count = new_id
        return new_id


    security.declareProtected(ManageCOREBlog, 'count_category')
    def count_category(self):
        return len(self.categories)


    security.declareProtected(View, 'category_list')
    def category_list(self):
	""" return all category list. """
        cats = []
        for id in self.categories.keys():
            obj = self.categories[id]
            #obj.__of__(self)
            cats.append(obj)
        return cats


    security.declareProtected(ManageCOREBlog, 'manage_editCategory')
    def manage_editCategory(self,id,name,description,icon_path,REQUEST=None):
        """edit category"""
        obj = self.getCategory(id)
        obj[0].edit(name,description,icon_path)
        if REQUEST:
            return REQUEST.RESPONSE.redirect('manage_categoryForm')


    security.declareProtected(ManageCOREBlog, 'manage_calculateCategory')
    def manage_calculateCategory(self,REQUEST=None):
        """recalculate category counts"""
        for key in self.categories.keys():
            cat = self.categories[key]
            cat.set_count(0)
        for id in self.entry_list:
            ent = self.getEntry(id)
            if ent.category:
                cat = self.categories[ent.category[0]]
                cat.set_count(cat.get_count()+1)

        #reset datemap
        self.datemap = IOBTree()
        objs = self.entry_items()
        for obj in objs:
            self.setIDToDatemap(obj.year_created(),obj.month_created(),obj.day_created(),obj.id)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    #
    # Methods for settings
    #

    security.declareProtected(ManageCOREBlog, 'manage_editSettings')
    def manage_editSettings(self,REQUEST=None):
        """set the setting values"""
        if REQUEST:
            pre_charcode = ""
            if self.hasProperty("management_page_charset"):
                pre_charcode = self.getProperty("management_page_charset")
            dics = get_property_dict()
            for d in dics:
                key = d["id"]
                if key in ["moblog_password","entry_password"]:
                    if not hasattr(self,'_rotorkey'):
                        self._rotorkey = make_rotorkey()
                    if not REQUEST.form[key] == "password":
                        #value changed.
                        rt = newrotor(self._rotorkey)
                        setattr(self,'_' + key,encodestring(rt.encrypt(REQUEST.form[key])))
                    REQUEST.form[key] = ""
                if REQUEST.form.has_key(key):
                    if self.hasProperty(key):
                        self._updateProperty(key,REQUEST.form[key])
                    else:
                        self.manage_addProperty(key,REQUEST.form[key],d["type"])
                elif d["type"] == "boolean" and self.hasProperty(key):
                    self._updateProperty(key,0)
            #Change objects charset if need...
            if self.hasProperty("management_page_charset"):
                post_charcode = self.getProperty("management_page_charset")
                if REQUEST.has_key("change_charcode") and pre_charcode != post_charcode:
                    change_site_encode(self,post_charcode,pre_charcode)

            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(ManageCOREBlog, 'decrypt')
    def decrypt(self,src):
        rt = newrotor(self._rotorkey)
        return rt.decrypt(src)


    #
    # Methods for skin settings
    #


    security.declareProtected(ManageCOREBlog, 'manage_editSkinsettings')
    def manage_editSkinsettings(self,REQUEST=None):
        """set the skin setting values"""
        if REQUEST:
            l = get_skin_dicts(self)
            if l[self.getProperty("skin_name")].has_key("skin_properties"):
                dics = l[self.getProperty("skin_name")]["skin_properties"]
                for d in dics:
                    key = d["id"]
                    if REQUEST.form.has_key(key):
                        if self.hasProperty(key):
                            self._updateProperty(key,REQUEST.form[key])
                        else:
                            self.manage_addProperty(key,REQUEST.form[key],d["type"])
                    elif d["type"] == "boolean" and self.hasProperty(key):
                        self._updateProperty(key,0)

            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    security.declareProtected(ManageCOREBlog, 'manage_changeSkin')
    def manage_changeSkin(self,after,before,REQUEST=None):
        """change the skin"""
        aplly_skin(self,after,before)
        self._updateProperty("skin_name",after)
        if REQUEST:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    security.declareProtected(ManageCOREBlog, 'skin_items')
    def skin_items(self):
        """return list of skin"""
        l = get_skin_dicts(self)
        ol = []
        for key in l.keys():
            ol.append(l[key]["skin_folder"])

        return ol


    #
    # Moblog
    #


    security.declareProtected(AddCOREBlogEntries,'receive')
    def receive(self):
        """Receive mails"""
        #create a POP3 client instance
        m = POP3(self.getProperty("mailhost"))
        #Authenticate
        rt = newrotor(self._rotorkey)
        passwd = rt.decrypt(decodestring(self._moblog_password))
        if self.getProperty("useapop"):
            m.apop(self.getProperty("moblog_user"),passwd)
        else:
            m.user(self.getProperty("moblog_user"))
            m.pass_(passwd)

        #get number of total message.
        total = len(m.list()[1])

        #get uid list
        l = m.uidl()[1]
        #make valid uid list
        suidls = []
        for uidline in l:
            ut = split(uidline," ")
            if len(ut) > 0:
                suidls.append(ut[len(ut)-1])
            else:
                suidls.append(uidline)

        if not hasattr(self,"uidls"):
            self.uidls = []
            self._p_changed = 1

        cnt = 1
        uidl_changed = 0
        for uid in suidls:
            if uid not in self.uidls:
                #New mail arrive...
                ml = m.retr(cnt)[1]
                buf = StringIO(join(ml,"\n"))
                mail = Message(buf,self.getProperty("management_page_charset"))
                self.add_mail_entry(mail)
                uidl_changed = 1
            cnt = cnt + 1
        if uidl_changed:
            self.uidls = suidls
            self._p_changed = 1

        m.quit()


    security.declarePrivate('add_mail_entry')
    def add_mail_entry(self,mail):
        #add entry from mail
        #If image was attached, 
        ret = ""

        mh = MailHolder(mail)
        maild = mail.get_parts()
        bd = ""
        pd = []
        mainpart = 0
        bdbuf = None
        for d in maild:
            if mainpart == 0 and find(d["type"],"text") != -1:
                #main part found
                mainpart = 1
                bdbuf = d["data"]
            else:
                pd.append(d)
        if not bdbuf:
            return
        #check sender
        sender_list = mh.getSenderList()
        allowed_email = self.getProperty("moblog_email_addr")
        if allowed_email:
            #check sender.
            go = 0
            ae_list = split(allowed_email,",")
            for addr in ae_list:
                for sndr in sender_list:
                    if find(sndr,addr) != -1:
                        go = 1
                        break;
                if go:
                    break
            if not go:
                #sender was mismatched....
                return
        #check password
        bdbuf.seek(0)
        pwline = replace(bdbuf.readline(),"\n","")
        rt = newrotor(self._rotorkey)
        passwd = rt.decrypt(decodestring(self._entry_password))
        if pwline == passwd:
            #password matched
            body_l = []
            separater = self.getProperty("body_separater")
            cnt = 0
            lines = bdbuf.readlines()
            for line in lines:
                line = replace(line,"\n","")
                line = replace(line,"\r","")
                if line and ord(line[0]) == 32:
                    #remove first space
                    line = line[1:]
                if len(separater) > 0 and line == separater:
                    break
                body_l.append(line)
                cnt = cnt + 1
            #add entry...

            #find a category
            in_cats = split(body_l[0]," ")
            adding_cats = []
            cats = self.category_list()
            for cat in in_cats:
                for scat in cats:
                    if scat.name == cat or scat.id == cat:
                        adding_cats.append(int(scat.id))

            img_folder = self.images
            pict_attached = 0
            pictid = ""
            if len(pd) > 0:
                #try adding a image
                serial = self.getProperty("image_serial") + 1
                pictid = "img_" + str(serial)
                img_folder.manage_addImage(pictid,\
                                pd[0]["data"],"","",pd[0]["type"])
                self._updateProperty("image_serial",serial)
                pict_attached = 1

            #add entry body
            if len(body_l) > 1:
                blog_charcode = self.getProperty("management_page_charset")
                posting_title = mh.getSubject()
                posting_body = join(body_l[1:],"\n")
                if pict_attached:
                    posting_body = """<img src="./images/%s" border="0">\n""" % (pictid) + posting_body
                main_category = self.getProperty("moblog_default_category")
                sub_category = []
                if adding_cats:
                    main_category = adding_cats[0]
                    if len(adding_cats) > 1:
                        sub_category = adding_cats[1:]
                comment_status = comment_open
                trackback_status = trackback_open
                if not self.getProperty("allow_comment_moblog"):
                    comment_status = comment_none
                if not self.getProperty("allow_trackback_moblog"): 
                    trackback_status = trackback_none
                new_id = self.manage_addEntry(self.getProperty("author_for_moblog"),\
                                     posting_body,"","",\
                                     main_category,1,sub_category,\
                                     posting_title,"","",0,comment_status,trackback_status)
                if pict_attached:
                    try:
                        #set metadata(title,permalink) to added image
                        img_folder = self.images
                        img_obj = img_folder[pictid]
                        img_obj.manage_addProperty("entrytitle",posting_title,"string")
                        img_obj.manage_addProperty("entryid",str(new_id),"string")
                    except:
                        pass


    #
    # Validation/Sanitize
    #


    security.declareProtected(View, 'removeHTML')
    def removeHTML(self,s):
        """Remove HTML tags."""
        return remove_html(str(s))


    security.declareProtected(View, 'validateHTML')
    def validateHTML(self,s):
        """Remove HTML tags."""
        return validate_html(str(s),tags)


    security.declareProtected(View, 'validateEntryBody')
    def validateEntryBody(self,s):
        """Remove HTML tags for Entry."""
        tags = []
        try:
            tag_prop = self.getProperty(COREBlog.body_tags_id)
            tags = split(tag_prop,",")
        except:
            pass
        return validate_html(str(s),tags)


    security.declareProtected(View, 'validateCommentBody')
    def validateCommentBody(self,s):
        """Remove HTML tags for Comment."""
        tags = []
        try:
            tag_prop = self.getProperty(COREBlog.comment_tags_id)
            tags = split(tag_prop,",")
        except:
            pass
        return validate_html(str(s),tags)


    #
    # misc. methods
    #

    security.declareProtected(View, 'convertCharcode')
    def convertCharcode(self,s,tocode):
	""" Converting charcode """
        return convert_charcode(s,tocode)


    security.declareProtected(View, 'get_charcode')
    def get_charcode(self):
        """ return charcode setting """
        prop = self.getProperty("management_page_charset")
        return prop

    security.declareProtected(View, 'get_blogclient_charcode')
    def get_blogclient_charcode(self):
        """ return charcode setting for blogclient """
        prop = self.getProperty("blogclient_char_code")
        return prop


    security.declareProtected(View, 'get_trackback_charcode')
    def get_trackback_charcode(self):
        """ return charcode setting """
        prop = self.getProperty("trackback_char_code")
        return prop

    #
    # XML-RPC Interfaces
    #


    #Blogger API

    security.declarePrivate('name2category_id')
    def name2category_id(self,cats):
        """ Utility method to convert category name to category id """
        c = convert_charcode
        bc = self.get_blogclient_charcode()
        cd = {}
        #First, make category dictionary (name:id)
        for cat in self.category_list():
            cd[cat.name] = cat.id
        ret_cl = []
        for cname in cats:
            if cd.has_key(cname):
                ret_cl.append(cd[cname])
        return ret_cl


    security.declareProtected(ManageCOREBlog, 'newPost')
    def newPost(self,appkey,blogid,username,password,
                 content,publish,REQUEST=None):
        """ post new entry"""
        #get entry
        c = convert_charcode
        bc = self.get_blogclient_charcode()
        title,cats,body = parse_blogger_post(content)
        cl = self.name2category_id(cats)
        if not cl:
            cl = [self.getProperty("blog_client_default_category")]

        comment_status = comment_open
        trackback_status = trackback_open
        if not self.getProperty("allow_comment_moblog"):
            comment_status = comment_none
        if not self.getProperty("allow_trackback_moblog"): 
            trackback_status = trackback_none

        #Post for MT compatibles
        new_id = self.manage_addEntry(author=username,
                             body=c(body,self.get_charcode(),bc),
                             extend='',
                             excerpt='',moderated=publish,
                             main_category=cl[0],sub_category=cl[1:],
                             title=c(title,self.get_charcode(),bc),
                             subtitle='',format=format_html,
                             allow_comment=comment_status,
                             receive_trackback=trackback_status,
                             sendnow=1)

        return str(new_id)


    security.declareProtected(ManageCOREBlog, 'editPost')
    def editPost(self,appkey,postid,username,password,
                 content,publish,REQUEST=None):
        """ set entry informations (remapped from editPost)"""
        import xmlrpclib
        try:
            int_id = int(postid)
            #get entry
            ent = self.getEntry(int_id)
            c = convert_charcode
            bc = self.get_blogclient_charcode()
            ct = {}
            title,cats,body = parse_blogger_post(content)
            cl = self.name2category_id(cats)
            if not cl:
                cl = ent.entry_category_list()

            #Post for MT compatibles
            ent.manage_editEntry(author=ent.author,
                                 body=c(body,self.get_charcode(),bc),
                                 extend='',format=ent.format,
                                 excerpt='',moderated=publish,
                                 main_category=cl[0],sub_category=cl[1:],
                                 title=c(title,self.get_charcode(),bc),
                                 subtitle=ent.subtitle)
            return xmlrpclib.True
        except:
            return xmlrpclib.False

    security.declareProtected(ManageCOREBlog, 'deletePost')
    def deletePost(self,appkey,postid,username,password,
                   publish,REQUEST=None):
        """ delete entry """
        import xmlrpclib
        try:
            int_id = int(postid)
            #delete entry
            self.deleteEntry(int_id)
            return xmlrpclib.True
        except:
            return xmlrpclib.False


    security.declareProtected(ManageCOREBlog, 'getRecentPosts')
    def getRecentPosts(self,appkey,blogid,username,password,
                 numberOfPosts,REQUEST=None):
        """ return recent posts """
        import xmlrpclib
        c = convert_charcode
        bc = self.get_blogclient_charcode()
        rl = []
        for ent in self.rev_entry_items(count=numberOfPosts):
            body = """<title>%s</title>%s""" % \
                    (c(ent.title,bc,self.get_charcode()),
                     c(ent.body,bc,self.get_charcode()))
            cl = ent.entry_category_list()
            for cat in cl:
                body = body + "<category>" + c(cat.name,bc,self.get_charcode()) + "</category>"
            d = {'dateCreated':xmlrpclib.DateTime(ent.date_created()),
                'userid':c(ent.author,bc,self.get_charcode()),
                'postid':str(ent.id),
                'content':body}

            rl.append(d)
        return rl


    security.declareProtected(ManageCOREBlog, 'getUsersBlogs')
    def getUsersBlogs(self,apkey,username,password,REQUEST=None):
        """ Get users blogs """
        return [{'url':self.blogurl(),'blogid':str(self.id),'blogName':self.title}]


    security.declareProtected(ManageCOREBlog, 'getUserInfo')
    def getUserInfo(self,apkey,username,password,REQUEST=None):
        """ Get users informations """
        return {'userid':username,'firstname':'','lastname':'',
                 'nickname':username,'email':'','url':self.blogurl()}


    #metaWeblog API

    security.declarePrivate('name2category_id')
    def map_content(self,content):
        d_d = {'description':'',
               'mt_text_more':'',
               'mt_allow_comments':comment_open,
               'mt_allow_pings':trackback_open,
               'title':'',
               'mt_excerpt':'',
	       'mt_convert_breaks':'0',
               'mt_tb_ping_urls':[] }
        #Map all the requred keys...
        c_d = {}
        for key in d_d.keys():
            if content.has_key(key):
                c_d[key] = content[key]
            else:
                c_d[key] = d_d[key]
        return c_d


    security.declareProtected(ManageCOREBlog, 'newPostMW')
    def newPostMW(self,postid,username,password,
                 content,publish,REQUEST=None):
        """ post new entry (remapped from newPost) """
        import xmlrpclib
        #get entry
        c = convert_charcode
        bc = self.get_blogclient_charcode()

        c_d = self.map_content(content)

	fmt = format_html
	if c_d['mt_convert_breaks'] == '1':
	    fmt = format_plain
        new_id = self.manage_addEntry(author=username,
                             body=c(c_d['description'],self.get_charcode(),bc),
                             extend=c(c_d['mt_text_more'],self.get_charcode(),bc),
                             excerpt=c(c_d['mt_excerpt'],self.get_charcode(),bc),moderated=1,
                             main_category=self.getProperty("blog_client_default_category"),
                             allow_comment=c_d['mt_allow_comments'],
                             receive_trackback=c_d['mt_allow_pings'],
                             title=c(c_d['title'],self.get_charcode(),bc),
                             subtitle='',format=fmt,
                             trackback_url=join(c_d['mt_tb_ping_urls'],'\n'),
                             sendnow=1)
        #sending trackbacks
        if len(c_d['mt_tb_ping_urls']) > 0:
            int_id = int(new_id)
            ent = self.getEntry(int_id)
            ent.sendTrackback()

        return str(new_id)



    security.declareProtected(ManageCOREBlog, 'editPostMW')
    def editPostMW(self,postid,username,password,
                 content,publish,REQUEST=None):
        """ set entry informations (remapped from editPost) """
        import xmlrpclib
        try:
            int_id = int(postid)
            #get entry
            ent = self.getEntry(int_id)
            c = convert_charcode
            bc = self.get_blogclient_charcode()
            cl = ent.entry_category_list()
            ct = {}

            c_d = self.map_content(content)
	    fmt = format_html
	    if c_d['mt_convert_breaks'] == '1':
		fmt = format_plain

            ent.manage_editEntry(author=ent.author,
                                 body=c(c_d['description'],self.get_charcode(),bc),
                                 extend=c(c_d['mt_text_more'],self.get_charcode(),bc),
                                 excerpt=c(c_d['mt_excerpt'],self.get_charcode(),bc),moderated=1,
                                 main_category=cl[0].id,
                                 allow_comment=c_d['mt_allow_comments'],
                                 receive_trackback=c_d['mt_allow_pings'],
                                 title=c(c_d['title'],self.get_charcode(),bc),
                                 subtitle=ent.subtitle,format=fmt,
                                 trackback_url=join(c_d['mt_tb_ping_urls'],'\n'))
            return xmlrpclib.True
        except:
            return xmlrpclib.False


    security.declareProtected(ManageCOREBlog, 'getPost')
    def getPost(self,postid,username,password,REQUEST=None):
        """ Return entry informations """
        import xmlrpclib
        try:
            int_id = int(postid)
            #get entry
            ent = self.getEntry(int_id)
            c = convert_charcode
            bc = self.get_blogclient_charcode()
	    cnv_brk = '0'
	    if ent.format == format_plain:
		cnv_brk = '1'
            return {'userid':c(ent.author,bc,self.get_charcode()),
                    'dateCreated':xmlrpclib.DateTime(ent.date_created()),
                    'postid':str(ent.id),
                    'description':c(ent.body,bc,self.get_charcode()),
                    'title':c(ent.title,bc,self.get_charcode()),
                    'link':self.blog_url + '/' + str(ent.id),
                    'permaLink':self.blog_url + '/' + str(ent.id),
                    'mt_text_more':c(ent.extend,bc,self.get_charcode()),
                    'mt_excerpt':c(ent.excerpt,bc,self.get_charcode()),
                    'mt_allow_comments':ent.allow_comment,
                    'mt_allow_pings':ent.receive_trackback,
                    'mt_convert_breaks':cnv_brk,
                    'mt_keywords':''}
            return xmlrpclib.True
        except:
            return xmlrpclib.False

    security.declareProtected(ManageCOREBlog, 'getRecentPostsMW')
    def getRecentPostsMW(self,blogid,username,password,numberOfPosts,REQUEST=None):
        """ Return multiple entry informations """
        el = []
        for ent in self.rev_entry_items(count=numberOfPosts):
            el.append(self.getPost(ent.id,username,password))
        return el

    #mt API

    security.declareProtected(ManageCOREBlog, 'getRecentPostTitles')
    def getRecentPostTitles(self,blogid,username,password,numposts,REQUEST=None):
        """ Return recent entry titles """
        import xmlrpclib
        el = []
        c = convert_charcode
        bc = self.get_blogclient_charcode()
        for ent in self.rev_entry_items(count=numposts):
            ed = {'dateCreated':xmlrpclib.DateTime(ent.date_created()),
                  'userid':c(ent.author,bc,self.get_charcode()),
                  'postid':str(ent.id),
                  'title':c(ent.title,bc,self.get_charcode())}
            el.append(ed)
        return el

    security.declareProtected(ManageCOREBlog, 'getCategoryList')
    def getCategoryList(self,blogid,username,password,REQUEST=None):
        """ Return category list """
        c = convert_charcode
        bc = self.get_blogclient_charcode()
        cl = []
        for cat in self.category_list():
            cd = {'categoryId':str(cat.id),
                  'categoryName':c(cat.name,bc,self.get_charcode())}
            cl.append(cd)
        return cl

    security.declareProtected(ManageCOREBlog, 'getPostCategories')
    def getPostCategories(self,postid,username,password,REQUEST=None):
        """ Return entry's categories """
        import xmlrpclib
        int_id = int(postid)
        #get entry
        ent = self.getEntry(int_id)
        c = convert_charcode
        bc = self.get_blogclient_charcode()
        cl = ent.entry_category_list()
        rl = []
        if len(cl) > 0:
            #Add primary category
            rl = rl + [ {'categoryName':c(cl[0].name,bc,self.get_charcode()),
                         'categoryId':str(cl[0].id),
                         'isPrimary':1} ]
            #Add sub categories
            if len(cl) > 1:
                for cat in cl[1:]:
                    rl = rl + [ {'categoryName':c(cat.name,bc,self.get_charcode()),
                                 'categoryId':str(cat.id),
                                 'isPrimary':0} ]
        return rl

    security.declareProtected(ManageCOREBlog, 'setPostCategories')
    def setPostCategories(self,postid,username,password,categories,REQUEST=None):
        """ Set entry's categories """
        import xmlrpclib
        try:
            int_id = int(postid)
            #get entry
            ent = self.getEntry(int_id)
            main_cat = None
            sub_cats = []
            for cat in categories:
                if cat.has_key('isPrimary') and cat['isPrimary']:
                    main_cat = cat['categoryId']
                else:
                    sub_cats.append(cat['categoryId'])
            cat = []
            if main_cat:
                cat = [main_cat]
            cat = cat + sub_cats
            if len(cat) == 0:
                return
            ent.set_category(cat)
            return xmlrpclib.True
        except:
            return xmlrpclib.False

    security.declareProtected(View, 'getTrackbackPings')
    def getTrackbackPings(self,postid,REQUEST=None):
        """ Return entry's trackback """
        int_id = r2i(postid)
        #get entry
        ent = self.getEntry(int_id)
        c = convert_charcode
        bc = self.get_blogclient_charcode()
        rl = []
        for tb in ent.trackback_list():
            rl.append({'pingTitle':tb.title,'pingURL':tb.url,'pingIP':''})
        return rl

    security.declareProtected(View, 'supportedMethods')
    def supportedMethods(REQUEST=None):
        """ Return list of suppoted methods """
        ml = []
        for key in blogger_map.keys():
            ml.append("blogger." + key)
        for key in metaweblog_map.keys():
            ml.append("metaWeblog." + key)
        for key in mt_map.keys():
            ml.append("mt." + key)
        
        return ml

    #security.declareProtected(View, 'supportedTextfilters')
    #def supportedTextFilters(REQUEST=None):
    #    """ Return list of suppoted text filters """
    #
    #    return [ {'key':'1','label':'Newline to br'},{'key':'2','label':'StructuredText'} ]

    security.declareProtected(View, 'publishPost')
    def publishPost(self,postid,username,password,REQUEST=None):
        """ Method to publish entry if it closed. """
        import xmlrpclib
        try:
            int_id = int(postid)
            #get entry
            ent = self.getEntry(int_id)
	    if not ent.moderated:
		ent.setModeration(1)
            return xmlrpclib.True
        except:
            return xmlrpclib.False

#
# Factory method for COREBlog instance.
#


def manage_addCOREBlog(parent,REQUEST=None,RESPONSE=None):
    """Add a COREBlog to a container."""
    if REQUEST['id'] <> None:
            id = REQUEST['id']
    charset = ""
    if REQUEST['management_page_charset'] <> None:
            charset = REQUEST['management_page_charset']
    if REQUEST['title'] <> None:
            title = convert_charcode(REQUEST['title'],charset)
    elm = []
    if REQUEST.form.has_key('createlexicon'):
        elm = REQUEST.form["elements"]

    obj = COREBlog(id,title,charset,elm)
    parent._setObject(obj.id, obj)
    obj._updateProperty("management_page_charset",charset)
    obj._updateProperty("trackback_char_code",charset)



    if RESPONSE is not None:
        RESPONSE.redirect(parent.DestinationURL() +
                            '/manage_main?manage_tabs_message=COREBlog+Added.' )



