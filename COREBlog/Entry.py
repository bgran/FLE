##############################################################################
#
# Entry.py
# Classes for Entriy
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
from string import join,replace,find,lower
from time import time,gmtime,strftime
from types import ListType
from re import sub

from Globals import HTMLFile
import Globals

from permissions import View,ManageCOREBlog,AddCOREBlogEntries,AddCOREBlogComments,ModerateCOREBlogEntries
from App import Management, Undo
from AccessControl import ClassSecurityInfo
from DateTime import DateTime
from BTrees.IIBTree import IISet
from BTrees.IOBTree import IOBTree

from stripogram import html2text

from ObjectBase import ObjectBase,Trackback,Comment,SendingTrackback
from utility import make_unique, \
                    call_addcomment_hook,call_addtrackback_hook, \
                    send_ping, \
                    convert_charcode, \
                    get_string_part,split_in_newline

__doc__="""Zope Blog Product 'COREBlog:Entry'
$Id: Entry.py,v 1.2 2004/11/22 15:02:37 tarmo Exp $"""

__version__='$Revision: 1.2 $'[11:-2]

#Statics

#Formats

format_plain = 0
format_stx = 1
format_html = 2
format_wiki = 3
format_restx = 4

#Comment status for entry

comment_none = 0
comment_open = 1
comment_closed = 2

#Trackback status for entry
trackback_none = 0
trackback_open = 1
trackback_closed = 2

excerpt_length = 250

def get_rendered_body(body,format):
    #Render body(in stx/restx format) and returns it.
    r_body = body
    if int(format) == format_stx:
        #Try to render structured text
        try:
             from DocumentTemplate.DT_Var import structured_text
             r_body = structured_text(body)
        except:
             pass
    elif int(format) == format_restx:
        #Try to render reStructuredText
        try:
             from DocumentTemplate.DT_Var import restructured_text
             r_body = restructured_text(body)
        except:
             pass
    return r_body


class Entry(ObjectBase,Management.Tabs,Undo.UndoSupport):
    """Class for COREBlog Entries"""

    security = ClassSecurityInfo()
    
    meta_type='COREBlog Entry'
    description = 'COREBlog Entry class'

    #allowing tags
    body_tags_id = "body_tags"

    icon = 'misc_/COREBlog/entry_img'

    manage_options=({'label':'Edit', 'icon':'', 'action':'manage_main', 'target':'manage_main'},
                {'label':'View', 'icon':'', 'action':'index_html', 'target':'manage_main'},
                {'label':'Comments', 'icon':'', 'action':'manage_comments', 'target':'manage_main'},
                {'label':'Trackbacks', 'icon':'', 'action':'manage_trackbacks', 'target':'manage_main'}
                #{'label':'Security', 'icon':'', 'action':'manage_access', 'target':'manage_main'},
                #{'label':'Undo', 'icon':'', 'action':'manage_UndoForm', 'target':'manage_main'}
                )

    security.declareProtected(ManageCOREBlog, 'manage_main')
    manage_main = HTMLFile('dtml/manage_editEntryForm',globals())
    security.declareProtected(ManageCOREBlog, 'manage_comments')
    manage_comments = HTMLFile('dtml/manage_listCommentForm',globals())
    security.declareProtected(ManageCOREBlog, 'manage_trackbacks')
    manage_trackbacks = HTMLFile('dtml/manage_listTrackbackForm',globals())
    security.declareProtected(ManageCOREBlog, 'manage_sendTrackback')
    manage_sendTrackback = HTMLFile('dtml/manage_sendTrackback',globals())
    security.declareProtected(ManageCOREBlog, 'manage_sendPINGTrackback')
    manage_sendPINGTrackback = HTMLFile('dtml/manage_sendPINGTrackback',globals())

    security.declareProtected(ManageCOREBlog, 'manage_editComment')
    manage_editComment = HTMLFile('dtml/manage_editCommentForm',globals())
    security.declareProtected(ManageCOREBlog, 'manage_editTrackback')
    manage_editTrackback = HTMLFile('dtml/manage_editTrackbackForm',globals())

    security.declareProtected(View, 'tbresult')
    tbresult = HTMLFile('dtml/trackbackResult',globals())


    security.declarePrivate('__init__')
    def __init__(self,id,author,body,extend,excerpt,moderated, \
                    title="",subtitle="", category = [], format = format_plain, \
                    allow_comment=comment_open,receive_trackback = trackback_open, \
                    trackback_url=[],created = -1):
        ObjectBase.__init__(self,id,moderated,created)
        self.author = author
        self.body = body
        self.rendered_body = body
        self.extend = extend

        self.excerpt = excerpt

        self.title = title
        self.subtitle = subtitle
        self.format = int(format)
        self.category = category
        self.trackback_url = trackback_url

        self.allow_comment = allow_comment
        self.receive_trackback = receive_trackback

        self.moderated = moderated

        self.comments = IISet()
        self.trackbacks = IISet()
        self.sendingtrackbacks = IOBTree()

        #SendingTrackback
        for url in trackback_url:
            self.addSendingTrackback(url)

        self.moderated_comment_count = 0
        self.moderated_trackback_count = 0



    security.declareProtected(AddCOREBlogEntries, 'manage_editEntry')
    def manage_editEntry(self,author,body,extend,excerpt,moderated, \
                    main_category,sub_category=[],title="",subtitle="",  \
                    format = format_plain, \
                    allow_comment=comment_open,receive_trackback = trackback_open, \
                    trackback_url="",sendnow=0,
                    REQUEST=None,**kw):
        """ Edit Entry """
        #COREBlog instanse
        cb = self.blog()
        #Validaters
        v_h = cb.removeHTML
        v_b = cb.validateEntryBody

        #Field validation
        self.author = v_h(author)
        self.body = v_b(body)
        self.rendered_body = v_b(body)
        self.extend = v_b(extend)

        if not excerpt:
            prebody = v_h(get_rendered_body(body,format))
            excerpt = get_string_part(prebody,excerpt_length,cb.get_charcode())
            if len(excerpt) < len(prebody):
                excerpt = excerpt + "..."
        self.excerpt = html2text(v_h(excerpt))
        self.title = v_h(title)
        self.subtitle = v_h(subtitle)
        self.format = format

        self.allow_comment = allow_comment
        self.receive_trackback = receive_trackback

        #category handling
        cats_s = [main_category] + sub_category
        cats = []
        for id in cats_s:
            if not cb.categories.has_key(int(id)):
                raise ValueError,"Category of ID(%s) does not exist." % (str(id))
            cats.append(int(id))
        cats = make_unique(cats)

        pre_moderated = self.moderated

        if not pre_moderated and moderated:
            self.category = cats

        self.setModeration(moderated)

        #Reindex
        if moderated:
            self.index()

        if pre_moderated and self.moderated:
            #set category counts
            #decrement old category count
            if self.category:
                try:
                    cb.addCategoryCount(self.category[0],-1)
                except KeyError:
                    #Ignore when main category does not exist.
                    pass
            #increment old category count
            if cats:
                cb.addCategoryCount(cats[0],1)

        tburls = split_in_newline(trackback_url)

        #Remove unsent trackbacks
        for id in self.sendingtrackbacks.keys():
            stb = self.sendingtrackbacks[id]
            if stb.sent == 0:
                del self.sendingtrackbacks[id]

        addedtbs = 0
        #SendingTrackback
        for url in tburls:
            r = self.addSendingTrackback(url)
            if r:
                addedtbs = addedtbs + 1

        self.category = cats
        if not title:
            kw['worning_message'] = "Title is required."

        if REQUEST:
            if sendnow and addedtbs:
                #send trackback
                return REQUEST.RESPONSE.redirect('./manage_sendTrackback')
            else:
	        #Set control values
		kw['noheader'] = 1
		kw['nocomment'] = 1
		kw['nocommentform'] = 1

                return self.manage_main(self,REQUEST,**kw)


    security.declareProtected(View, 'index_html')
    def index_html(self,ignore_moderation=0,REQUEST=None):
        """ Entry presentation """
        if self.moderated or ignore_moderation:
            return self.entry_html(self,REQUEST)
        else:
            raise KeyError,self.id

    security.declareProtected(View, 'body_size')
    def body_size(self):
        """ Entry presentation """
        return len(self.body)

    security.declareProtected(View, 'entry_title')
    def entry_title(self):
        """ Entry presentation """
        return self.title

    security.declareProtected(View, 'excerpt_flat')
    def excerpt_flat(self):
        """ Remove cr,lf from excerpt & return it """
        ex = self.excerpt
        ex = replace(ex,"\r","")
        ex = replace(ex,chr(0x0a),"")
        return ex

    security.declarePrivate('blog')
    def blog(self):
        return self.aq_parent

    security.declarePrivate('index')
    def index(self,parent=None):
        if parent == None:
            parent = self.aq_parent
        try:
            parent.catalog_object(self,join(parent.getPhysicalPath(),"/") + "/e" + str(self.id))
        except:
            pass

    security.declarePrivate('del_index')
    def del_index(self,parent=None):
        if parent == None:
            parent = self.aq_parent
        try:
            parent.uncatalog_object(join(parent.getPhysicalPath(),"/") + "/e" + str(self.id))
        except:
            pass

    security.declarePrivate('search_text')
    def search_text(self):
        if not self.moderated:
            return ""
        text = self.title + "\n" + self.subtitle + "\n" + self.rendered_body
        for com in self.comment_list():
            try:
                text = text + com.title + "\n" + com.author + "\n" + \
                    com.url + "\n" + com.body + "\n"
            except:
                pass
        for tb in self.trackback_list():
            try:
                text = text + tb.title + "\n" + tb.blog_name + "\n" + \
                    com.url + "\n" + com.excerpt + "\n"
            except:
                pass
        return text



    #Moderation

    security.declarePrivate('goClose')
    def goClose(self):
        #insert/remove datemap
        self.aq_parent.setDatemap(self)
        #decrement category count
        if self.category:
            self.aq_parent.addCategoryCount(self.category[0],-1)
        #remove from ZCatalog
        self.del_index()

    security.declarePrivate('goOpen')
    def goOpen(self):
        #insert/remove datemap
        self.aq_parent.setDatemap(self)
        #increment category count
        if self.category:
            self.aq_parent.addCategoryCount(self.category[0],1)


    #
    # Comment management
    #

    security.declarePrivate('checkCommentValues')
    def checkCommentValues(self,title,author,body,moderated,email="",url="",REQUEST=None):
        """ Preview a comment """
        #chech input values
        cb = self.blog()

        v_h = cb.removeHTML
        v_c = cb.validateCommentBody

        REQUEST.form["show_worning"] = 0

        #name
        if cb.hasProperty("require_name") and cb.getProperty("require_name") == 1 and \
                not v_h(REQUEST.form["author"]):
            REQUEST.form["show_worning"] = REQUEST.form["show_worning"] + 1
            REQUEST.form["name_required"] = 1

        #email
        if cb.hasProperty("require_email") and cb.getProperty("require_email") == 1 and \
                not v_h(REQUEST.form["email"]):
            REQUEST.form["show_worning"] = REQUEST.form["show_worning"] + 1
            REQUEST.form["email_required"] = 1

        #comment body
        if REQUEST.form.has_key("body") and not v_c(REQUEST.form["body"]):
            REQUEST.form["show_worning"] = REQUEST.form["show_worning"] + 1
            REQUEST.form["body_required"] = 1

        if REQUEST.form["show_worning"] == 0:
            del REQUEST.form["show_worning"]

        return REQUEST

        #if REQUEST:
        #    return REQUEST.RESPONSE.redirect("./previewcomment_html")


    security.declareProtected(AddCOREBlogComments, 'addComment')
    def addComment(self,title,author,body,moderated = 1,email="",url="",created="",REQUEST=None):
        """ Add a comment """
        if self.allow_comment != comment_open:
            #This entry does not allow adding comment
            raise RuntimeError,"This entry is closed for adding comment."
        #COREBlog instanse
        cb = self.blog()

        #Validaters
        v_h = cb.removeHTML
        v_c = cb.validateCommentBody
        comment_id = cb.getNewCommentID()
        title = v_h(title)
        author = v_h(author)
        email = v_h(email)
        url = v_h(url)
        body = v_c(body)

        #moderation
        try:
            if cb.getProperty("moderate_comment"):
                moderated = 0
        except:
            pass

        #check values
	if REQUEST:
	    REQUEST_bk = self.checkCommentValues(title,author,body,moderated,email,url,REQUEST)
	    if REQUEST_bk.form.has_key("show_worning"):
		return self.previewcomment_html(self,REQUEST_bk)

        #name
        if not author and \
            cb.hasProperty("require_name") and cb.getProperty("require_name") == 0 and \
            cb.hasProperty("anonymous_name"):
            author = cb.getProperty("anonymous_name")

	sec = -1
	if created:
	    try:
		dt = DateTime(created)
		sec = int(dt)
	    except:
		pass
	obj = Comment(comment_id,self.id,title,author,email,url,body,int(moderated),sec)

        self.comments.insert(comment_id)
        cb.setComment(comment_id,obj)

        if moderated:
            self.moderated_comment_count = self.moderated_comment_count + 1
            #catalogging...
            self.index()


        #set cookie
        if REQUEST and REQUEST.form.has_key('setcookie'):
            resp = REQUEST.RESPONSE
            #path = join(self.aq_parent.getPhysicalPath(),'/');
            path = "/"
            gtime = gmtime(time())
            gtup = (gtime[0] + 1,12,31,23,59,59,0,365,0)
            exp = strftime('%A, %d-%b-%y %H:%M:%S GMT',gtup)

            #exp = (self.ZopeTime() + 365).rfc822()

            resp.setCookie('comment_author',author,expires=exp,path=path)
            resp.setCookie('comment_email',email,expires=exp,path=path)
            resp.setCookie('comment_url',url,expires=exp,path=path)

        #tell ZODB that object has added.
        self._p_changed = 1

        #call the hook method
        call_addcomment_hook(self.aq_parent,comment_id,self.id,v_h(title),v_h(author), \
                                v_c(body),int(moderated),v_h(email),v_h(url))

        if REQUEST:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    security.declareProtected(AddCOREBlogComments, 'previewComment')
    def previewComment(self,title,author,body,moderated=1,email="",url="",REQUEST=None):
        """ Preview a comment """
        #chech input values
        REQUEST = self.checkCommentValues(title,author,body,moderated,email,url,REQUEST)

        return self.previewcomment_html(self,REQUEST)

        #if REQUEST:
        #    return REQUEST.RESPONSE.redirect("./previewcomment_html")


    security.declareProtected(View, 'forgetPersonalInfo')
    def forgetPersonalInfo(self,REQUEST=None):
        """ reset cookies for posting comment """
        #reset cookie
        resp = REQUEST.RESPONSE
        #path = join(self.aq_parent.getPhysicalPath(),'/');
        path = "/"
        gtime = gmtime(time())
        gtup = (gtime[0] + 1,12,31,23,59,59,0,365,0)
        exp = strftime('%A, %d-%b-%y %H:%M:%S GMT',gtup)

        #exp = (self.ZopeTime() + 365).rfc822()
        resp.setCookie('comment_author','',expires=exp,path=path)
        resp.setCookie('comment_email','',expires=exp,path=path)
        resp.setCookie('comment_url','',expires=exp,path=path)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    security.declareProtected(ManageCOREBlog, 'editComment')
    def editComment(self,comment_id,title,author,body,email="",url="",REQUEST=None):
        """ Edit a comment """
        if self.allow_comment != comment_open:
            #This entry does not allow adding trackback
            raise RuntimeError,"This entry is closed for editing comment."
        #COREBlog instanse
        cb = self.aq_parent

        int_comment_id = int(comment_id)
        obj = cb.getComment(int_comment_id)

        #Validaters
        v_h = cb.removeHTML
        v_c = cb.validateCommentBody
        obj.title = v_h(title)
        obj.author = v_h(author)
        obj.email = v_h(email)
        obj.url = v_h(url)
        obj.body = v_c(body)

        cb.setComment(int_comment_id,obj)

        if obj.moderated:
            #catalogging...
            self.index()

        #tell ZODB that object has added.
        self._p_changed = 1

        if REQUEST:
            return REQUEST.RESPONSE.redirect('./manage_comments')


    security.declareProtected(ManageCOREBlog, 'deleteAllComments')
    def deleteAllComments(self):
        """ Delete all comment """
        for id in self.comments:
            self.deleteComment(id)


    security.declareProtected(ManageCOREBlog, 'deleteComments')
    def deleteComments(self,ids,REQUEST=None):
        """ Delete comments in ids """
        if type(ids) != ListType:
            raise TypeError,"Paramater 'ids' must be a ListType."
        for id in ids:
            self.deleteComment(int(id))
        if REQUEST:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    security.declareProtected(ManageCOREBlog, 'deleteComment')
    def deleteComment(self,id):
        """ Delete a comment """
        if not id in self.comments:
            raise KeyError,"Comment(ID:%d) does not exists."
        self.comments.remove(id)
        self.moderated_comment_count = self.moderated_comment_count - 1
        if self.moderated_comment_count < 0:
            self.moderated_comment_count = 0
        self.aq_parent.deleteComment(id)
        #recatalog...
        self.index()


    security.declareProtected(ManageCOREBlog, 'moderateComments')
    def moderateComments(self,mod_ids=[],REQUEST=None):
        """ Chenge moderate setting for comments in mod_ids """
        if type(mod_ids) != ListType:
            raise TypeError,"Paramater 'ids' must be a ListType."
        for id in mod_ids:
            self.moderateComment(int(id),1)
        unmod_list = []
        int_mod_list = []
        for id in mod_ids:
            int_mod_list.append(int(id))
        for id in self.comments:
            if id not in int_mod_list:
                unmod_list.append(id)
        for id in unmod_list:
            self.moderateComment(id,0)

        self.moderated_comment_count = len(mod_ids)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    security.declareProtected(ManageCOREBlog, 'moderateComment')
    def moderateComment(self,id,moderation):
        """ Chenge moderate setting for comments """
        if not id in self.comments:
            raise KeyError,"Comment(ID:%d) does not exists."
        cb = self.blog()
        obj = cb.getComment(id)
        obj.moderated = moderation
        #recatalog...
        self.index()


    security.declareProtected(View, 'comment_list')
    def comment_list(self,consider_moderation = 1):
        if self.allow_comment == comment_none:
            return []
        #Return comment objects
        comments = []
        for comment_id in self.comments:
            obj = self.blog().getComment(comment_id)
            obj.__of__(self)
            if not consider_moderation or obj.moderated:
                comments.append(obj)
        return comments


    security.declareProtected(View, 'getComment')
    def getComment(self,comment_id,consider_moderation = 1):
        if self.allow_comment == comment_none:
            return None
        int_comment_id = int(comment_id)
        if int_comment_id in self.comments:
            obj = self.blog().getComment(int_comment_id)
            obj.__of__(self)
            return obj
        else:
            return None


    security.declareProtected(ManageCOREBlog, 'count_all_comment')
    def count_all_comment(self):
        #Return count of comment objects
        return len(self.comments)


    security.declareProtected(View, 'count_comment')
    def count_comment(self):
        #Return count of moderated comments
        return self.moderated_comment_count


    #
    # Trackback management
    #


    security.declareProtected(View, 'addTrackback')
    def addTrackback(self,title,excerpt,url,blog_name,created=""):
        if self.receive_trackback != trackback_open:
            #This entry does not allow adding trackback
            raise RuntimeError,"This entry is closed for adding trackback."
        cb = self.blog()
        trackback_id = cb.getNewTrackbackID()
        v_h = cb.removeHTML
        v_c = cb.validateCommentBody

        #moderation
        moderated = 1
        try:
            if cb.getProperty("moderate_comment"):
                moderated = 0
        except:
            pass

	sec = -1
	if created:
	    try:
		dt = DateTime(created)
		sec = int(dt)
	    except:
		pass
	
        obj = Trackback(trackback_id,self.id,
                            v_h(title),v_h(excerpt),v_c(url),v_c(blog_name),
			    sec,moderated)
        self.trackbacks.insert(trackback_id)
        cb.setTrackback(trackback_id,obj)

        if moderated:
            self.moderated_trackback_count = self.moderated_trackback_count + 1
            #catalogging...
            self.index()

        #tell ZODB that object has added.
        self._p_changed = 1

        #call the hook method
        call_addtrackback_hook(self.aq_parent,trackback_id,self.id, \
                                v_h(title),v_h(excerpt),v_c(url),v_c(blog_name))


    security.declareProtected(ManageCOREBlog, 'editTrackback')
    def editTrackback(self,trackback_id,title,excerpt,url,blog_name,REQUEST=None):
        """ Edit a trackback """
        if self.receive_trackback != trackback_open:
            #This entry does not allow editing trackback
            raise RuntimeError,"This entry is closed for editing trackback."
        cb = self.blog()
        v_h = cb.removeHTML
        v_c = cb.validateCommentBody

        int_trackback_id = int(trackback_id)
        obj = cb.getTrackback(int_trackback_id)

        obj.title = v_h(title)
        obj.excerpt = v_h(excerpt)
        obj.url = v_c(url)
        obj.blog_name = v_c(blog_name)

        cb.setTrackback(trackback_id,obj)

        if obj.moderated:
            #catalogging...
            self.index()

        #tell ZODB that object has added.
        self._p_changed = 1

        if REQUEST:
            return REQUEST.RESPONSE.redirect('./manage_trackbacks')


    security.declareProtected(AddCOREBlogComments, 'deleteAllTrackbacks')
    def deleteAllTrackbacks(self):
        """ Delete all trackback """
        for id in self.trackbacks:
            self.deleteTrackback(id)


    security.declareProtected(AddCOREBlogComments, 'deleteTrackbacks')
    def deleteTrackbacks(self,ids,REQUEST=None):
        """ Delete trackback in ids """
        if type(ids) != ListType:
            raise TypeError,"Paramater 'ids' must be a ListType."
        for id in ids:
            self.deleteTrackback(int(id))
        if REQUEST:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    security.declareProtected(AddCOREBlogComments, 'deleteTrackback')
    def deleteTrackback(self,id):
        """ Delete a trackback """
        if not id in self.trackbacks:
            raise KeyError,"Trackback(ID:%d) does not exists."
        self.trackbacks.remove(id)
        self.moderated_trackback_count = self.moderated_trackback_count - 1
        if self.moderated_trackback_count < 0:
            self.moderated_trackback_count = 0
        self.index()
        self.aq_parent.deleteTrackback(id)


    security.declareProtected(AddCOREBlogComments, 'moderateTrackbacks')
    def moderateTrackbacks(self,mod_ids=[],REQUEST=None):
        """ Chenge moderate setting for trackbacks in mod_ids """
        if type(mod_ids) != ListType:
            raise TypeError,"Paramater 'ids' must be a ListType."
        for id in mod_ids:
            self.moderateTrackback(int(id),1)
        unmod_list = []
        int_mod_list = []
        for id in mod_ids:
            int_mod_list.append(int(id))
        for id in self.trackbacks:
            if id not in int_mod_list:
                unmod_list.append(id)
        for id in unmod_list:
            self.moderateTrackback(id,0)

        self.moderated_trackback_count = len(mod_ids)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(REQUEST['HTTP_REFERER'])


    security.declareProtected(AddCOREBlogComments, 'moderateTrackback')
    def moderateTrackback(self,id,moderation):
        """ Chenge moderate setting for trackbacks """
        if not id in self.trackbacks:
            raise KeyError,"Comment(ID:%d) does not exists."
        cb = self.blog()
        obj = cb.getTrackback(id)
        obj.moderated = moderation
        #recatalog...
        self.index()


    security.declareProtected(View, 'trackback_list')
    def trackback_list(self,consider_moderation = 1):
        if self.receive_trackback == trackback_none:
            return []
        trackbacks = []
        for trackback_id in self.trackbacks:
            obj = self.blog().getTrackback(trackback_id)
            obj.__of__(self)
            if not consider_moderation or obj.moderated:
                trackbacks.append(obj)
        return trackbacks


    security.declareProtected(View, 'getTrackback')
    def getTrackback(self,trackback_id,consider_moderation = 1):
        if self.receive_trackback == trackback_none:
            return None
        int_trackback_id = int(trackback_id)
        if int_trackback_id in self.trackbacks:
            obj = self.blog().getTrackback(int_trackback_id)
            obj.__of__(self)
            return obj
        else:
            return None


    security.declareProtected(View, 'count_all_trackback')
    def count_all_trackback(self):
        #Return count of trackback objects
        return len(self.trackbacks)


    security.declareProtected(View, 'count_trackback')
    def count_trackback(self):
        #Return count of moderated trackback
        return self.moderated_trackback_count


    security.declareProtected(View, 'tbpingurl')
    def tbpingurl(self,REQUEST=None,RESPONSE=None):
        """Return the pbping url"""
        cb = self.aq_parent
        return cb.blogurl() + "/e" + self.id + "/tbping"


    security.declareProtected(View, 'tbping')
    def tbping(self,REQUEST=None,RESPONSE=None):
        """Method for receiving Trackback PING"""

        cb = self.blog()
        REQUEST.set('error_code',0)
        #char_code = cb.get_charcode()
        #resp = Entry.tb_ping_resp_tpl % (char_code,0,"")

        try:
            #__mode=rss
            if REQUEST and REQUEST.form.has_key('__mode') and REQUEST.form['__mode'] == 'rss':
                #rdf_body = Entry.tb_ping_moderdf_tpl % (self.title,cb.blogurl() + "/" + str(self.id),self.excerpt)
                REQUEST.set('mode_rss',1)
                #rdf_body = Entry.tb_ping_moderdf_tpl % ("1","2","3")
                #resp = Entry.tb_ping_resp_tpl % (char_code,0,rdf_body)
            #check parameters
            elif not REQUEST or (REQUEST and not REQUEST.form.has_key('url')):
                raise RuntimeError,"Paramater 'url' required."
            else:
                #check method... accept only 'POST' method
                #if not REQUEST.has_key('REQUEST_METHOD') or \
                #                lower(REQUEST['REQUEST_METHOD']) != 'post':
                #    raise RuntimeError, "Trackback ping was calld with 'GET' method. Please call with 'POST' method."

                char_code = cb.get_charcode()
                #parameters
                val = {}
                val['url'] = convert_charcode(REQUEST.form['url'],char_code)
                val['title'] = val['url']
                val['excerpt'] = ""
                val['blog_name'] = ""

                for key in ['title','excerpt','blog_name']:
                    if REQUEST.form.has_key(key):
                        val[key] = convert_charcode(REQUEST.form[key],char_code)
                #finnaly,add trackback to Entry!
                self.addTrackback(val['title'],val['excerpt'],val['url'],val['blog_name'])
        except ValueError,e:
            REQUEST.set('error_code',1)
            REQUEST.set('message',"Requested url('%s') does not exist" % (str(e.args[0])))
            #resp = Entry.self.tb_ping_resp_tpl % (char_code,1,Entry.tb_ping_message_tpl % ()))
        except RuntimeError,e:
            REQUEST.set('error_code',1)
            REQUEST.set('message',e.args[0])
            #resp = Entry.tb_ping_resp_tpl % (char_code,1,Entry.tb_ping_message_tpl % (e.args[0]))
        except:
            REQUEST.set('error_code',1)
            #resp = Entry.tb_ping_resp_tpl % (char_code,1,Entry.tb_ping_message_tpl % ("Some Error Occured"))

        return self.tbresult(self,REQUEST)

    #
    # Category management
    #


    security.declareProtected(View, 'entry_category_list')
    def entry_category_list(self):
        #Return list of category set for the entry
        cb = self.aq_parent
        ret_l = []
        for cat_id in self.category:
            try:
                cat = cb.getCategory(cat_id)[0]
                ret_l.append(cat)
            except KeyError,e:
                pass
            except Exception,e:
                raise e
        return ret_l

    security.declareProtected(ManageCOREBlog, 'set_category')
    def set_category(self,cats):
        #set category
        cb = self.aq_parent
        s_cats = []
        for id in cats:
            if not cb.categories.has_key(int(id)):
                raise ValueError,"Category of ID(%s) does not exist." % (str(id))
            s_cats.append(int(id))
        s_cats = make_unique(s_cats)
        self.category = s_cats


    #
    # SendingTrackback management
    #

    security.declareProtected(AddCOREBlogEntries, 'addSendingTrackback')
    def addSendingTrackback(self,url):
        url = sub("\s","",url)
        if not url or find(url,"http") != 0:
            return
        max = -1
        for id in self.sendingtrackbacks.keys():
            if self.sendingtrackbacks[id].url == url:
                #There is sendingtrackback who has same url
                return 0
            if max < id:
                max = id
        max = max + 1
        self.sendingtrackbacks[max] = SendingTrackback(max,self.id,url)
        return 1


    security.declareProtected(View, 'count_sending_trackback')
    def count_sending_trackback(self):
        #Return count of sendingTrackbacks
        return len(self.sendingtrackbacks)


    security.declareProtected(View, 'sending_trackback_list')
    def sending_trackback_list(self):
        #Return list of sendingTrackbacks
        ret_l = []
        for id in self.sendingtrackbacks.keys():
            tb = self.sendingtrackbacks[id]
            ret_l.append(tb)
        return ret_l


    security.declareProtected(AddCOREBlogEntries, 'sendTrackback')
    def sendTrackback(self):
        #send Trackback
        ret_l = []
        cb = self.aq_parent
        cbcc = ""
        src_url = cb.blogurl() + "/e" + str(self.id)
        blog_name = ""
        blog_name = cb.getProperty("title")
        blog_charcode = cb.get_charcode()
        if cb.hasProperty("trackback_char_code"):
            cbcc = cb.getProperty("trackback_char_code")
        for id in self.sendingtrackbacks.keys():
            tb = self.sendingtrackbacks[id]
            if not tb.sent:
                code,message = \
                    tb.post_trackback(src_url,blog_name,self.title,self.excerpt,cbcc,blog_charcode)
                ret_l.append( {"url":tb.url,"code":code,"message":message} )
        return ret_l


    security.declareProtected(AddCOREBlogEntries, 'sendPING')
    def sendPING(self):
        #send Update nortifications for PING Servers
        ret_l = []
        cb = self.aq_parent
        cbcc = ""
        url = cb.blogurl()
        #if cb.getProperty("use_permalink_on_ping") and entry_id != -1:
        #    url = url + "/e" + str(self.id)
        blog_name = ""
        blog_name = cb.getProperty("title")
        if cb.hasProperty("trackback_char_code"):
            cbcc = cb.getProperty("trackback_char_code")
        for pingurl in cb.getProperty("ping_servers"):
            if pingurl:
                try:
                    resp = send_ping(pingurl,blog_name,url,
                                cbcc,cb.get_product_version(),cb.get_charcode())
                except Exception,e:
                    resp = {}
                    resp["message"] = str(e)
                ret_l.append( {"url":pingurl,"message":resp["message"]} )
        return ret_l


Globals.InitializeClass(Entry)

