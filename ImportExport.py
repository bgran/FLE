# $Id: ImportExport.py,v 1.88 2005/02/22 11:54:26 tarmo Exp $
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

"""Contains classes responsible for importing and exporting the data to and from an FLE installation. Uses XML for data storage."""

import sys, time
import zipfile
from types import UnicodeType
from common import FakeRequest, FakeUpload
from cgi import escape

import Shared.DC.xml.pyexpat.pyexpat
import NanoDom
from NanoDom import to_utf8

class Counter:
    def __init__(self):
        self.__counter=0

    def get_next_counter(self):
        self.__counter+=1
        return self.__counter

    def get_counter(self):
        """Returns the value of the automatic counter."""
        return self.__counter

    def set_counter(self,val):
        self.__counter=val

class DataTable(Counter):
    """Auxiliary class for storing binary data needed for
    XML export."""
    def __init__(self):
        Counter.__init__(self)
        self.__cache={}

    def get_size(self):
        """Returns the size of the binary cache (in items)."""
        return len(self.__cache)

    def storeData(self,data):
        """Stores a new binary data into the storage and
        assigns it a unique name. The name is returned."""
        name = 'data'+str(self.get_next_counter())
        self.__cache[name]=data
        return name

    def restoreData(self,name,data):
        """Re-stores binary data into the storage. The name
        is given as a parameter, but should be of the form
        'dataN' where N is an integer (of any length). The
        restoration process should make sure that all numbers
        from 1 to the highest number are filled."""
        self.__cache[name]=data
        num = int(name[4:])
        if self.get_counter()<num:
            self.set_counter(num)

    def getData(self,name):
        """Returns the binary data associated with the given name."""
        return self.__cache[name]

    def removeData(self,name):
        """Removes the binary data associated with the given name."""
        self.__cache[name]=None

    def getNames(self):
        """Returns the names of the binary packages in the cache."""
        names = []
        for n in range(1,self.get_counter()+1):
            names.append('data'+str(n))
        return names

def make_attr(elem,name,value):
    elem.setAttribute(name,value)

def make_text(elem,text):
    elem.appendChild(elem.ownerDocument.createTextNode(text))

def get_attr(elem,name):
    return to_utf8(elem.getAttribute(name))

def get_text(elem):
    res=u''
    for line in elem.childNodes:
        res += line.nodeValue
    return to_utf8(res)

class Dump:
    def __init__(self):
        self.storage=[]
    def write(self,s):
        # Note: s should be Unicode
        self.storage.append(s)
    def getdata(self):
        return u''.join(self.storage).encode('utf-8')


# Example of using the Exporter: look at tests/testImportExport.py
class Exporter:
    """Class that handles the exporting and importing of data
    and also holds the XMLized content."""

    # If the parameter 'file' is specified, it is assumed to be
    # an uploaded zip file containing exported data and it is
    # loaded into memory. Otherwise an empty Exporter is created.
    def __init__(self,root_element,file=None):
        """Creates a new Exporter."""
        # Add a binary data hash table
        self.binarydata = DataTable()
        self.idmap = {}
        self.timecounters=[0,0,0,0,0,0,0,0,0,0]

        if file:
            self.loadZip(file)
            if self.root.tagName != root_element:
                raise 'Import error',"XML data should specify document %s. Instead, document %s was found." % (root_element, self.root.tagName)
        else:
            # Document: unlink, writexml(writer), toxml()
            converter = NanoDom.NanoDom()
            self.dom = converter.dom
            #type=xml.dom.minidom.DocumentType('FLE PUBLIC "-//UIAHFI//DTD FLE export data FLE/1.1//EN" "FLE.dtd"')
            self.root = self.dom.createElement(root_element)
            self.root.setAttribute("encoding","utf-8")
            self.dom.appendChild(self.root)

    def exportData(self,data,method):
        """Does exporting of data.

        - data: The object that should be exported.

        - method: The (bound) method of Exporter that should be
        used to export the object."""
        result = method(data)
        if result:
            self.root.appendChild(result)

    def importData(self,elem_name,method,parent_object):
        """Imports data from a given XML element into Zope.

        - elem_name: The name of the top level element that should be
        imported.

        - method: The (bound) method of Exporter that should be
        used to import the element.

        - parent_object: The Zope object under which this element
        should be imported."""

        names=''
        for elem in self.root.childNodes:
            names=names+' %s' % elem.nodeName
            if elem.nodeName == elem_name:
                method(elem,parent_object)
                return
        raise 'FLE Error','Unknown import segment: %s / %s' % (elem_name, names)


    def createZip(self,file):
        """Dumps the currently exported data
        (XML document and binary files) into a zip file.

        - file: name of the file to create"""
        zip = zipfile.ZipFile(file,"w",zipfile.ZIP_DEFLATED)
        dump = Dump()
        self.dom.writexml(dump)
        zip.writestr(zipfile.ZipInfo("fledom.xml"),dump.getdata())
        for name in self.binarydata.getNames():
            zip.writestr(
                zipfile.ZipInfo(name),
                str(self.binarydata.getData(name)))
        zip.close()

    def loadZip(self,file):
        """Loads a zipped FLE content file.

        - file: the file name to load."""
        zip = zipfile.ZipFile(file,"r",zipfile.ZIP_DEFLATED)

        #xmlstring = unicode(
        #    zip.read("fledom.xml"), 'utf-8').encode("utf-8")
        xmlstring = zip.read("fledom.xml")
        try:
            # TODO: Check which characters are allowed!
            parser=Shared.DC.xml.pyexpat.pyexpat.ParserCreate('utf-8')
            converter=NanoDom.NanoDom(parser)
            parser.Parse(xmlstring)
            self.dom = converter.dom
        except UnicodeError:
            print "XML data is not utf-8 encoded! Detecting encoding..."
            import re
            encoding = re.search('encoding="([-a-zA-Z0-9]*)">',xmlstring).group(1)
            print "Transforming from %s to utf-8..." % encoding
            xmlstring = unicode(xmlstring,encoding).encode("utf-8")
            self.dom = xml.dom.minidom.parseString(xmlstring)
        self.root = self.dom.firstChild

        for name in zip.namelist():
            if name[:4]=='data':
                self.binarydata.restoreData(name,zip.read(name))
        zip.close()

    def exportGlobalTypes(self,globals):
        """Exports globally available knowledge types."""
        elem = self.dom.createElement("GlobalKnowledgeTypes")
        for set in globals.objectValues('ThinkingTypeSet'):
            elem.appendChild(self.exportTypeSet(set))
        if hasattr(globals,'tmp_objects'):
            for set in globals.tmp_objects.objectValues('ThinkingTypeSet'):
                elem.appendChild(self.exportTypeSet(set))
        return elem

    def importGlobalTypes(self,elem,fle_root):
        """Imports globally available knowledge types."""

        for telem in elem.childNodes:
            self.importTypeSet(telem,fle_root.typesets)

    def exportKB(self,courses):
        """Exports the entire knowledge building.
        Parameter should point to the CourseManager."""

        kb = self.dom.createElement("KnowledgeBuilding")

        for c in courses.get_children('Course'):
            kb.appendChild(self.exportCourse(c))

        return kb

    def importKB(self,elem,fle_root):
        """Import knowledge building.

        - elem: The XML element containing the data.

        - obj: The Zope object containing CourseManager."""

        # All children should be course objects
        for child in elem.getElementsByTagName('Course'):
            print "Importing course %s..." % get_attr(child,'Name')
            self.importCourse(child,fle_root.courses)
            get_transaction().commit()

    def exportCourse(self,course):
        """Exports the given course."""
        elem = self.dom.createElement("Course")
        name = course.get_name()
        make_attr(elem,"Name",name)
        teacher=course.get_teacher()
        if not teacher:
            teacher=''
        make_attr(elem,"Teacher",teacher)
        make_attr(elem,"Organisation",course.get_organisation())
        make_attr(elem,"StartDate",str(int(round(course.get_start_date()))))
        make_attr(elem,"EndDate",str(int(round(course.get_end_date()))))

        if course.get_description():
            desc=self.dom.createElement("Descr")
            make_text(desc,course.get_description())
            elem.appendChild(desc)

        if course.get_methods():
            meth = self.dom.createElement("Methods")
            make_text(meth,course.get_methods())
            elem.appendChild(meth)

##         for set in course.objectValues('ThinkingTypeSet'):
##             elem.appendChild(self.exportTypeSet(set))

        resources = self.dom.createElement("Resources")
        try:
            for res in course.get_resources():
                resource = self.dom.createElement("Resource")
                make_attr(resource, "Title", res.get_title())
                make_attr(resource, "Author", res.get_author())
                make_attr(resource, "Description", res.get_description())
                make_attr(resource, "Type", res.get_type())
                make_attr(resource, "Location", res.get_location())
                resources.appendChild(resource)
        except AttributeError:
            # Fle3 versions 1.4.2 _and_ before don't have resources.
            pass
        elem.appendChild(resources)

        if course.has_announcements():
            anns = self.dom.createElement("Announcements")
            for entry in course.announcements.entry_items(start=0,count=9999):
                ann = self.dom.createElement("Entry")
                make_attr(ann,"Title",entry.title)
                make_attr(ann,"Author",entry.author)
                make_attr(ann,"Body",entry.body)
                make_attr(ann,"Created",str(entry.created))
                make_attr(ann,"Category",str(entry.category[0]))
                anns.appendChild(ann)
            elem.appendChild(anns)

        for fol in course.get_children('GroupFolder'):
            elem.appendChild(self.exportGroupFolder(fol))

        for ctx in course.get_children("CourseContext"):
            elem.appendChild(self.exportContext(ctx))
        return elem

    def importCourse(self,elem,courses):
        """Imports a course under the given CourseManager."""

        id = courses.add_course_impl(get_attr(elem,'Teacher'))
        course = courses.get_child(str(id))

        descr = ''
        if elem.getElementsByTagName("Descr"):
            descr = get_text(elem.getElementsByTagName("Descr")[0])

        methods = ''
        if elem.getElementsByTagName("Methods"):
            methods = get_text(elem.getElementsByTagName("Methods")[0])

        course.update(
            get_attr(elem,"Name"),
            descr,
            get_attr(elem,"Organisation"),
            methods,
            int(get_attr(elem,"StartDate")),
            int(get_attr(elem,"EndDate")))

        # Set local roles to users
        for uelem in elem.ownerDocument.firstChild.getElementsByTagName("User"):
            try:
                user = course.fle_users.get_user_info(
                    get_attr(uelem,"Name"))
            except:
                continue # If the user doesn't exist, we'll just skip

            for celem in uelem.getElementsByTagName("ACL")[0].\
                getElementsByTagName("CourseRole"):

                if get_attr(celem,"CourseName") != \
                   course.get_name():
                    continue

                roles = []
                for relem in celem.childNodes:
                    roles.append(get_attr(relem,"Name"))

                if roles:
                    course.set_roles(user.get_uname(),tuple(roles))

        try:
            resources = elem.getElementsByTagName('Resources')[0]
            for resource in resources.getElementsByTagName('Resource'):
                res_title = get_attr(resource, "Title")
                res_author = get_attr(resource, "Author")
                res_description = get_attr(resource, "Description")
                res_type = get_attr(resource, "Type")
                res_location = get_attr(resource, "Location")
                course.add_resource(res_title, res_author,res_description,
                                 res_type, res_location)
        except IndexError:
            # Fle3 versions 1.4.2 _and_ before don't have resources.
            pass

        try:
            anns = elem.getElementsByTagName("Announcements")[0]
            course.add_announcements()
            for ann in anns.getElementsByTagName("Entry"):
                ent_title = get_attr(ann,"Title")
                ent_body= get_attr(ann,"Body")
                ent_author = get_attr(ann,"Author")
                ent_created = float(get_attr(ann,"Created"))
                ent_category = int(get_attr(ann,"Category"))
                course.announcements.manage_addEntry(author=ent_author,
                                                     body=ent_body,
                                                     title=ent_title,
                                                     extend="",
                                                     excerpt="",
                                                     main_category=ent_category,
                                                     entry_date=ent_created,
                                                     moderated=1,
                                                     format=1,
                                                     subtitle='',
                                                     sendping=0)
        except IndexError:
            # Course doesn't have announcements
            pass


        for fol in elem.childNodes:
            if fol.nodeName != 'GroupFolder':
                continue
            self.importGroupFolder(fol,course.__of__(courses),toplevel=1)
        for ctx in elem.childNodes:
            if ctx.nodeName != 'Context':
                continue
            self.importContext(ctx,course.__of__(courses))

        return course


    def exportContext(self,ctx):
        """Exports the given course context."""
        elem = self.dom.createElement("Context")
        make_attr(elem,"Name",ctx.get_name())
        make_attr(elem,"Author",ctx.get_author())
        descr = self.dom.createElement("Descr")
        make_text(descr,ctx.get_description())
        elem.appendChild(descr)
        descr = self.dom.createElement("LongDescr")
        make_text(descr,ctx.get_long_description())
        elem.appendChild(descr)

        if hasattr(ctx, '_' + ctx.__class__.__name__+ '__roleplay_in_use'):
            make_attr(elem, "RoleplayInUse",
                      (ctx.uses_roleplay() and ["1"] or ["0"])[0])
            play_roles = self.dom.createElement("PlayRoles")
            for uname in ctx.get_all_users_id():
                role_name = ctx.get_role_played_by_user(uname)
                role_elem = self.dom.createElement("PlayRole")
                make_attr(role_elem, "Uname", uname)
                make_attr(role_elem, "RoleName", role_name)
                play_roles.appendChild(role_elem)
            elem.appendChild(play_roles)

        elem.appendChild(self.exportTypeSet(ctx.get_thinking_type_set()))

        for fol in ctx.get_children('GroupFolder'):
            elem.appendChild(self.exportGroupFolder(fol))

        for note in ctx.get_children('Note'):
            elem.appendChild(self.exportNote(note))

        return elem

    def importContext(self,elem,course):
        """Imports a context into a course."""

        desc = get_text(elem.getElementsByTagName("Descr")[0])
        ldesc = get_text(elem.getElementsByTagName("LongDescr")[0])

        from CourseContext import CourseContext
        ctx = CourseContext(
            course,
            get_attr(elem,"Name"),
            desc,
            ldesc,
            None, # tt_set not given
            get_attr(elem,"Author"))
        course._setObject(ctx.get_id(),ctx)

        if get_attr(elem, 'RoleplayInUse') == '1':
            ctx.set_roleplay_use(1)
        else:
            ctx.set_roleplay_use(0)

        try:
            play_roles = elem.getElementsByTagName('PlayRoles')[0]
            for play_role in play_roles.getElementsByTagName('PlayRole'):
                uname = get_attr(play_role, "Uname")
                role_name = get_attr(play_role, "RoleName")
                ctx.set_user_role_name(uname, role_name)
        except IndexError:
            # Fle3 versions before version 1.4b don't have play roles.
            pass

        set = elem.getElementsByTagName('KnowledgeTypeSet')[0]
        self.importTypeSet(set,ctx.__of__(course))
        ctx._tt_set_id=get_attr(set,'ID')

        for nelem in elem.childNodes:
            if nelem.nodeName != 'GroupFolder':
                continue
            self.importGroupFolder(nelem,ctx.__of__(course),toplevel=1)
        for nelem in elem.childNodes:
            if nelem.nodeName != 'Note':
                continue
            self.importNote(nelem,ctx.__of__(course))

    def exportNote(self,note):
        """Exports the given note."""
        if not hasattr(note,'censored'):
            note.censored=0
        elem = self.dom.createElement("Note")
        make_attr(elem,"KnowledgeTypeRef",note.get_tt_id())
        make_attr(elem,"ID",note.get_id())
        make_attr(elem,"Date",str(int(round(note.get_creation_time()))))
        if hasattr(note,'get_real_subject'):
            make_attr(elem,"Subject",note.get_real_subject())
        else:
            make_attr(elem,"Subject",note.get_subject())
        make_attr(elem,"Author",note.get_author())
        if hasattr(note,'censored') and note.censored:
            make_attr(elem,"CensoredBy",note.censorer)
            make_attr(elem,"CensoredTime",str(note.censored))
            make_attr(elem,"CensoredReason",str(note.censor_reason))

        body = self.dom.createElement("NoteBody")
        make_text(body,note.get_body())
        elem.appendChild(body)

        reader_list = self.dom.createElement("ReaderList")

        try:
            for (uname, date_data) in note.get_readers_with_all_dates().items():
                reader = self.dom.createElement("Reader")
                make_attr(reader,"Name", uname)
                try:
                    for date in date_data['when']:
                        d = self.dom.createElement("Event")
                        make_attr(d,"Type","ReadTime")
                        make_attr(d,"Value",str(date))
                        reader.appendChild(d)
                except TypeError:
                    # This will come up if the 'when' item isn't a list
                    d = self.dom.createElement("Event")
                    make_attr(d,"Type","ReadCount")
                    make_attr(d,"Value",str(date_data))
                    reader.appendChild(d)
                reader_list.appendChild(reader)
        except AttributeError:
            # This will rise if Thread.py is an old versio.
            # In this case we'll just have to skip the reader information.
            pass

        elem.appendChild(reader_list)

        if note.get_url()!='':
            link = self.dom.createElement("Link")
            make_attr(link,"Src",note.get_url())
            make_attr(link,"Name",note.get_url_name())
            elem.appendChild(link)

        if note.has_image():
            name = self.binarydata.storeData(
                note.get_image_data())
            link = self.dom.createElement("DataLink")
            make_attr(link,"LocalName",name)
            make_attr(link,
                "ContentType",
                note.get_image_content_type())
            make_attr(link,"Name",note.get_image_name())
            elem.appendChild(link)

        for reply in note.get_children('Note'):
            elem.appendChild(self.exportNote(reply))

        return elem

    def importNote(self,elem,parent):
        """Imports a note into a context or note."""
        s_time=time.time()

        url=''
        url_name=''
        image=None
        image_name=''

        for lelem in elem.childNodes:
            if lelem.nodeName=="Link":
                url=get_attr(lelem,"Src")
                url_name=get_attr(lelem,"Name")
                break

        for delem in elem.childNodes:
            if delem.nodeName=='DataLink':
                image_data=self.binarydata.getData(get_attr(delem,"LocalName"))
                image_name=get_attr(delem,"Name")
                image_content_type = get_attr(delem,"ContentType")
                image = FakeUpload('image',image_data,image_content_type)
                break
        self.timecounters[0]+=(time.time()-s_time)
        s_time=time.time()

        # We suppose that each Note has a NoteBody.
        body = get_text(elem.getElementsByTagName("NoteBody")[0])
##         body=''
##         for line in elem.getElementsByTagName("NoteBody")[0].childNodes:
##             snippet = to_utf8(line.nodeValue)
##             if snippet == '\n':
##                 body += '\r\n'
##             else:
##                 body += snippet
        self.timecounters[1]+=(time.time()-s_time)
        s_time=time.time()

        note = parent.add_reply(
            get_attr(elem,"KnowledgeTypeRef"),
            get_attr(elem,"Author"),
            get_attr(elem,"Subject"),
            body,
            url,
            url_name,
            image,
            image_name,
            creation_time=float(get_attr(elem,"Date")))

        self.timecounters[2]+=(time.time()-s_time)
        s_time=time.time()

        note.set_temporary(0)
        parent._setObject(note.id,note)
        note=note.__of__(parent)
        self.idmap[get_attr(elem,"ID")]=note

        self.timecounters[3]+=(time.time()-s_time)
        s_time=time.time()

        censored = get_attr(elem,"CensoredTime")
        if censored:
            note.do_censor(float(str(censored)),
                           get_attr(elem,"CensoredBy"),
                           get_attr(elem,"CensoredReason"))

        # readers (read/unread status)
        for rlelem in elem.childNodes:
            if rlelem.nodeName == 'ReaderList':
                for relem in rlelem.childNodes:
                    uname = get_attr(relem,'Name')
                    dates = []
                    for delem in relem.childNodes:
                        if delem.nodeName == 'Event' and \
                           get_attr(delem,"Type")=="ReadTime":
                            dates.append(float(get_attr(delem,"Value")))
                        elif delem.nodeName == 'Event' and \
                           get_attr(delem,"Type")=="ReadCount":
                            dates.append(time.time())

                    note.set_exported_reader(uname, dates)

        self.timecounters[4]+=(time.time()-s_time)
        s_time=time.time()

        #get_transaction().commit()

        for nelem in elem.childNodes:
            if nelem.nodeName != 'Note':
                continue
            self.importNote(nelem,note.__of__(parent))


    def exportTypeSet(self,set):
        """Exports the given knowledgetypeset."""

        elem = self.dom.createElement("KnowledgeTypeSet")
        make_attr(elem,"ID", set.get_id())
        make_attr(elem,"Name", set.get_name())
        make_attr(elem,"Language", set.get_language())
        make_attr(elem,"Original", set.get_original_name())
        if set.is_in_tmp(set):
            make_attr(elem,"Status",'Unfinished')
        delem = self.dom.createElement("Description")
        make_text(delem,set.get_description())
        elem.appendChild(delem)

        starting = self.dom.createElement("StartingTypes")
        for start in set.get_thinking_type_thread_start():
            starting.appendChild(self.exportTypeRef(start))
        elem.appendChild(starting)

        for type in set.get_thinking_types():
            felem = self.dom.createElement("FollowupRule")
            ffelem = self.dom.createElement("KnowledgeTypeRef")
            make_attr(ffelem,"ID-REF",type.get_id())
            felem.appendChild(ffelem)
            for followup in set.get_possible_follow_ups(type):
                ffelem = self.dom.createElement("KnowledgeTypeRef")
                make_attr(ffelem,"ID-REF", followup.get_id())
                felem.appendChild(ffelem)
            elem.appendChild(felem)

        for type in set.get_thinking_types():
            elem.appendChild(self.exportType(type))

        return elem

    def importTypeSet(self,elem,parent,force_update=0):
        """Imports a knowledge type set into a ThinkingTypeSetManager
        or a course."""
        from ThinkingTypeSet import ThinkingTypeSet
        from ThinkingType import ThinkingType

        my_id = get_attr(elem,"ID")

        # If the ID of this set is not of the form "ttsNN", then it's a
        # predefined set (installed from the file system).

        # We check if the set by the same ID already is created and:
        # if the set is of the form "ttsNN", we change its id
        # else if force_update is activated, we remove the previous version
        # else we skip this import.

        if my_id in parent.objectIds('ThinkingTypeSet'):
            if my_id[:3]=='tts':
                # We must assume now that the parent
                # is a ThinkingTypeSetManager. Importing several sets
                # into course contexts shouldn't happen.
                my_id = parent.get_new_valid_tts_id()
            elif force_update:
                parent.manage_delObjects(my_id)
            else:
                return

        types = []
        for telem in elem.getElementsByTagName("KnowledgeType"):
            try:
                desc=get_text(telem.getElementsByTagName("Description")[0])
            except IndexError:
                desc=''
            try:
                checklist=get_text(telem.getElementsByTagName("Checklist")[0])
            except IndexError:
                checklist=''
            try:
                phrase=get_text(telem.getElementsByTagName("StartingPhrase")[0])
            except IndexError:
                phrase=''

            type = {
                'id': get_attr(telem,"ID"),
                'name': get_attr(telem,"Name"),
                'starting_phrase': phrase,
                'description': desc,
                'colour': get_attr(telem,"Colour"),
                'icon': None,
                # No image file - we'll store the data directly
                'icondata': self.binarydata.getData(get_attr(telem.getElementsByTagName("Icon")[0],"LocalName")),
                'checklist': checklist,
                }

            types.append(type)

        starters = []

        selem = elem.getElementsByTagName("StartingTypes")[0]
        for stelem in selem.childNodes:
            starters.append(get_attr(stelem,"ID-REF"))

        relations = {}

        for felem in elem.getElementsByTagName("FollowupRule"):
            orig = None
            list = []
            for ffelem in felem.childNodes:
                if orig:
                    list.append(get_attr(ffelem,"ID-REF"))
                else:
                    orig=get_attr(ffelem,"ID-REF")
            relations[orig]=list

        descr = get_text(elem.getElementsByTagName("Description")[0])

        tts = ThinkingTypeSet(
            my_id,
            get_attr(elem,"Name"),
            get_attr(elem,"Original"),
            get_attr(elem,"Language"),
            descr,
            types, # list of pairs (name,obj)
            starters, # list of names
            relations) # list of pairs (orig_name,reply_name)

        parent._setObject(
            my_id,
            tts)

        if get_attr(elem,"Status")=='Unfinished':
            parent.move_to_tmp(tts)

        #get_transaction().commit()

    def exportTypeRef(self,type):
        """Exports the given knowledgetypeset reference."""
        elem = self.dom.createElement("KnowledgeTypeRef")
        make_attr(elem,"ID-REF",type.get_id())
        return elem

    def exportType(self,type):
        """Exports the given knowledgetype."""
        elem = self.dom.createElement("KnowledgeType")
        make_attr(elem,"ID",type.get_id())
        make_attr(elem,"Name",type.get_name())
        make_attr(elem,"Colour",type.get_colour())

        icon = self.dom.createElement("Icon")
        make_attr(icon,
            "LocalName",
            self.binarydata.storeData(type.get_icon().data))
        make_attr(icon,"ContentType",type.get_icon().getContentType())
        elem.appendChild(icon)

        expl = self.dom.createElement("StartingPhrase")
        make_text(expl,type.get_starting_phrase())
        elem.appendChild(expl)

        instr = self.dom.createElement("Description")
        make_text(instr,type.get_description())
        elem.appendChild(instr)

        cl = self.dom.createElement("Checklist")
        make_text(cl,type.get_checklist())
        elem.appendChild(cl)

        return elem

    def exportJamming(self, courses):
        """Exports the entire jamming stuff.
        Parameter should point to the CourseManager."""
        jamming = self.dom.createElement('Jamming')

        try:
            for c in courses.get_children('Course'):
                for js in c.get_child('jamming').get_children('JamSession'):
                    jamming.appendChild(self.exportJamSession(c, js))

            return jamming

        except AttributeError:
            # We are exporting old FLE version where Course
            # objects don't have Jamming object.
            return None

    def importJamming(self, elem, fle_root):
        """Import Jamming."""
        for js in elem.getElementsByTagName('JamSession'):
            self.importJamSession(js, fle_root.courses)
            #get_transaction().commit()

    def exportJamSession(self, course, jam_session):
        """Export the given jam session (on a given course)."""
        elem = self.dom.createElement("JamSession")
        make_attr(elem, 'CourseName', course.get_name())
        make_attr(elem, 'Name', jam_session.get_name())
        make_attr(elem, 'Type', jam_session.get_type())
        make_attr(elem, 'Descr', jam_session.get_description())
        make_attr(elem, 'ID', jam_session.get_id())
        make_attr(elem, 'StartingArtefactIDRef',
                  jam_session.get_starting_artefact_id())

        for ja in jam_session.get_children('JamArtefact'):
            elem.appendChild(self.exportJamArtefact(ja))
        return elem

    def importJamSession(self, elem, courses):
        """Import a jam session (under jamming (under course)) under
        the given CourseManager."""

        course_name = get_attr(elem, 'CourseName')
        for course in courses.get_courses():
            if course.get_name() == course_name:
                jamming = course.get_child('jamming')
                break

        starting_artefact_id = get_attr(elem, 'StartingArtefactIDRef')

        for ja_elem in elem.childNodes:
            if ja_elem.nodeName == 'JamArtefact' and \
               get_attr(ja_elem, 'ID') == starting_artefact_id:

                ja_name = get_attr(ja_elem, 'Name')
                for delem in ja_elem.childNodes:
                    if delem.nodeName == 'DataLink':
                        ja_data = self.binarydata.getData(
                            get_attr(delem, 'LocalName'))
                        ja_content_type = get_attr(delem, 'ContentType')
                        break
                break

        # Create a jam session with starting artefact.
        jam_session = jamming.form_handler(
            get_attr(elem, 'Name'),
            get_attr(elem, 'Type'),
            get_attr(elem, 'Descr'),
            ja_name,
            FakeUpload('some name', ja_data, ja_content_type),
            submit=1,
            called_from_import_code=1,
            REQUEST=FakeRequest(user=get_attr(ja_elem, 'Author')),
            )

        starting_artefact = jam_session.get_children('JamArtefact')[0]
        self.idmap[get_attr(elem, 'ID')] = jam_session

        # Add annotations to the starting artefact.
        self.idmap[get_attr(ja_elem, 'ID')] = starting_artefact
        for e in ja_elem.childNodes:
            if e.nodeName == 'Annotations':
                i = 0
                for a in e.childNodes:
                    if a.nodeName == 'Annotation':
                        starting_artefact.add_annotation(
                            get_attr(a, 'Author'),
                            float(get_attr(a, 'Date')),
                            get_text(a.getElementsByTagName('Text')[0]))

                        censored = get_attr(a, 'Censored')
                        if censored:
                            starting_artefact.do_censor_annotations((i,), float(censored), get_attr(a, 'Censorer'))
                        i += 1
                break

        # readers (read/unread status of the starting artefact)
        for rlelem in ja_elem.childNodes:
            if rlelem.nodeName == 'ReaderList':
                for relem in rlelem.childNodes:
                    uname = get_attr(relem,'Name')
                    dates = []
                    for delem in relem.childNodes:
                        if delem.nodeName == 'Event' and \
                           get_attr(delem,"Type")=="ReadTime":
                            dates.append(float(get_attr(delem,"Value")))
                        elif delem.nodeName == 'Event' and \
                           get_attr(delem,"Type")=="ReadCount":
                            dates.append(time.time())

                    starting_artefact.set_exported_reader(uname, dates)

        # Import the rest of the jam artefacts in this jam session
        for ja_elem in elem.childNodes:
            if ja_elem.nodeName == 'JamArtefact' and \
               get_attr(ja_elem, 'ID') != starting_artefact_id:
                self.importJamArtefact(ja_elem, jam_session)

        # set parent ids
        for ja_elem in elem.childNodes:
            id_ = get_attr(ja_elem, 'ID')
            if ja_elem.nodeName == 'JamArtefact' and \
               id_ != starting_artefact_id:

                parent_ids = []
                for pelem in ja_elem.childNodes:
                    if pelem.nodeName == 'Parents':
                        for prelem in pelem.childNodes:
                            if prelem.nodeName == 'ParentRef':
                                parent_ids.append(get_attr(prelem, 'ID-REF'))
                        break

                real_parent_ids = []
                for pid in parent_ids:
                    real_parent_ids.append(self.idmap[pid].get_id())
                self.idmap[id_].set_parent_ids(real_parent_ids)

        jam_session.update_drawing()

    def exportJamArtefact(self, jam_artefact):
        """Export the given JamArtefact."""
        elem = self.dom.createElement('JamArtefact')
        make_attr(elem, 'Name', jam_artefact.get_real_name())
        make_attr(elem, 'Author', str(jam_artefact.get_author()))
        make_attr(elem, 'ID', jam_artefact.get_id())

        annotations = self.dom.createElement('Annotations')
        for tple \
            in jam_artefact.get_real_annotations():

            try:
                (uname, a_time, a_text, censored, censorer) = tple
            except ValueError:
                # This comes up with versions 1.1betaX
                (uname, a_time, a_text) = tple
                censored=0
                censorer=''

            a_elem = self.dom.createElement('Annotation')
            make_attr(a_elem, 'Author', uname)
            make_attr(a_elem, 'Date', repr(a_time))
            text = self.dom.createElement('Text')
            make_text(text, a_text)
            a_elem.appendChild(text)
            make_attr(a_elem, 'Censored', repr(censored))
            make_attr(a_elem, 'Censorer', censorer)
            annotations.appendChild(a_elem)
        elem.appendChild(annotations)

        parents = self.dom.createElement('Parents')
        for p_id in jam_artefact.get_parent_ids():
            p_elem = self.dom.createElement('ParentRef')
            make_attr(p_elem, 'ID-REF', p_id)
            parents.appendChild(p_elem)
        elem.appendChild(parents)

        name = self.binarydata.storeData(jam_artefact.get_real_data())
        link = self.dom.createElement('DataLink')
        make_attr(link, 'LocalName', name)
        make_attr(link, 'ContentType', jam_artefact.get_content_type())
        elem.appendChild(link)

        reader_list = self.dom.createElement("ReaderList")
        for (uname, date_data) in \
            jam_artefact.get_readers_with_all_dates().items():

            reader = self.dom.createElement("Reader")
            make_attr(reader,"Name", uname)
            try:
                for date in date_data['when']:
                    d = self.dom.createElement("Event")
                    make_attr(d,"Type","ReadTime")
                    make_attr(d,"Value",repr(date))
                    reader.appendChild(d)
            except TypeError:
                # This will come up if the 'when' item isn't a list
                d = self.dom.createElement("Event")
                make_attr(d,"Type","ReadCount")
                make_attr(d,"Value",repr(date_data))
                reader.appendChild(d)
            reader_list.appendChild(reader)
        elem.appendChild(reader_list)

        return elem

    def importJamArtefact(self, ja_elem, jam_session):
        """Import a jam artefact under given jam session."""


        for delem in ja_elem.childNodes:
            if delem.nodeName == 'DataLink':
                ja_data = self.binarydata.getData(
                    get_attr(delem, 'LocalName'))
                ja_content_type = get_attr(delem, 'ContentType')
                break

        artefact = jam_session.add_artefact(get_attr(ja_elem, 'Name'),
                                            ja_data,
                                            ja_content_type,
                                            get_attr(ja_elem, 'Author'),
                                            'temp value')
        self.idmap[get_attr(ja_elem, 'ID')] = artefact

        for e in ja_elem.childNodes:
            if e.nodeName == 'Annotations':
                i = 0
                for a in e.childNodes:
                    if a.nodeName == 'Annotation':
                        artefact.add_annotation(
                            get_attr(a, 'Author'),
                            float(get_attr(a, 'Date')),
                            get_text(a.getElementsByTagName('Text')[0]))

                        censored = get_attr(a, 'Censored')
                        if censored:
                            artefact.do_censor_annotations((i,), float(censored), get_attr(a, 'Censorer'))
                        i += 1
                break

        # readers (read/unread status)
        for rlelem in ja_elem.childNodes:
            if rlelem.nodeName == 'ReaderList':
                for relem in rlelem.childNodes:
                    uname = get_attr(relem,'Name')
                    dates = []
                    for delem in relem.childNodes:
                        if delem.nodeName == 'Event' and \
                           get_attr(delem,"Type")=="ReadTime":
                            dates.append(float(get_attr(delem,"Value")))
                        elif delem.nodeName == 'Event' and \
                           get_attr(delem,"Type")=="ReadCount":
                            dates.append(time.time())

                    artefact.set_exported_reader(uname, dates)

    def exportUsers(self,users):
        """Exports FLE users. Parameter should point to the
        UserManager."""
        elem = self.dom.createElement("Users")

        groups = self.dom.createElement("Groups")
        try:
            for (gid, gname) in users.get_group_ids_and_names():
                group = self.dom.createElement("Group")
                make_attr(group, "GroupID", gid)
                make_attr(group, "GroupName", gname)
                groups.appendChild(group)
            elem.appendChild(groups)
        except AttributeError:
            # We'll end up here if the database doesn't contain correct
            # group information (version of Fle3 prior to 1.4)
            pass

        for user in users.objectValues('UserInfo'):
            elem.appendChild(self.exportUser(user))

        return elem

    def exportUserList(self,userlist,do_webtop=0,do_passwd=0):
        """Export a given set of FLE users. Parameter should be
        a list of UserInfo objects. By default doesn't export
        the webtop or the user's password."""
        elem = self.dom.createElement("Users")
        for user in userlist:
            elem.appendChild(self.exportUser(user,do_webtop,do_passwd))
            #get_transaction().commit()
        return elem

    def importUsers(self,elem,fle_root):
        """Import all users into the given FLE root."""

        try:
            groups = elem.getElementsByTagName("Groups")[0]
            for group in groups.childNodes:
                self.importGroup(group, fle_root.fle_users)
        except IndexError:
            # Importing from old Fle3 version that has no
            # group information here.
            pass

        for user in elem.getElementsByTagName("User"):
            self.importUser(user,fle_root.fle_users,do_user=1,do_webtop=0)

    def importGroup(self, elem, fle_users):
        """Import a group."""
        group_id = get_attr(elem, 'GroupID')
        group_name = get_attr(elem, 'GroupName')
        fle_users.add_group_with_existing_id(group_id, group_name)

    def importUsersWebtops(self,elem,fle_root):
        """Import all users into the given FLE root."""

        for user in elem.childNodes:
            self.importUser(user,fle_root.fle_users,do_user=0,do_webtop=1)

    def exportUserACL(self,fle_user,do_passwd=1):
        """Export a user's Zope ACL information.
        User parameter is an FLE UserInfo instance."""
        elem = self.dom.createElement("ACL")
        #user = fle_user.acl_users.getUser(fle_user.get_uname())

        if do_passwd:
            try:
                passwd = fle_user.getPassword()
            except:
                passwd = fle_user.getFrozenPassword()
            make_attr(elem,"Password",passwd)

        try:
            domains = fle_user.getDomains()
        except:
            domains = fle_user.getFrozenDomains()

        for dom in domains:
            delem = self.dom.createElement("Domain")
            dmake_attr(elem,"Name",dom)
            elem.appendChild(delem)

        if fle_user.is_frozen():
            roles = fle_user.getFrozenRoles()
        else:
            roles = fle_user.getRoles()

        for role in roles:
            # Skip role 'Authenticated' since that is added
            # to a user's roles supefluously and does not need
            # to be saved.
            if role == 'Authenticated':
                continue
            relem = self.dom.createElement("Role")
            make_attr(relem,"Name",role)
            elem.appendChild(relem)

        for course in fle_user.courses.objectValues('Course'):
            roles = fle_user.getRolesInObject(course)
            relem = self.dom.createElement("CourseRole")
            make_attr(relem,"CourseName",course.get_name())
            for role in roles:
                relem2 = self.dom.createElement("Role")
                make_attr(relem2,"Name",role)
                relem.appendChild(relem2)
            elem.appendChild(relem)

        return elem

    def retrieveUserACL(self,elem):
        """Retrieves a user's ACL information.
        Returns password, domains and roles."""

        # If the Password attribute doesn't exist, will return
        # an empty string (at least xml.dom.minidom does), which
        # is ok.
        password = get_attr(elem,"Password")

        domains = []
        for delem in elem.getElementsByTagName("Domain"):
            domains.append(get_attr(delem,"Name"))
        roles = []
        for delem in elem.childNodes:
            if delem.nodeName != 'Role':
                continue
            roles.append(get_attr(delem,"Name"))

        return (password, domains, roles)


    def exportUser(self,user,do_webtop=1,do_passwd=1):
        """Exports the given user."""
        elem = self.dom.createElement("User")

        elem.appendChild(self.exportUserACL(user,do_passwd))

        make_attr(elem,"Name",user.get_uname())
        make_attr(elem,"Nickname", user.get_nickname())
        make_attr(elem,"FirstName",user.get_first_name())
        make_attr(elem,"LastName",user.get_last_name())
        make_attr(elem,"Organisation",user.get_organization())
        make_attr(elem,"Lang",user.get_language())
        make_attr(elem,"Email",user.get_email())
        # We don't have group anymore: we have groups! See the code below.
        # make_attr(elem,"Group",user.get_group())
        make_attr(elem,"Address1",user.get_address1())
        make_attr(elem,"Address2",user.get_address2())
        make_attr(elem,"City",user.get_city())
        make_attr(elem,"Country",user.get_country())
        make_attr(elem,"Homepage",user.get_homepage())
        make_attr(elem,"Phone",user.get_phone())
        make_attr(elem,"Mobile",user.get_gsm())
        make_attr(elem,"WebtopBgImagePath", user.get_webtop_bg_image_path())

        if user.is_frozen():
            make_attr(elem,"Frozen","1")

        try:
            if user.get_webtop_bg_image_path()[:len('images')] != 'images':
                bg_image = self.dom.createElement("WebtopBackgroundImage")
                make_attr(bg_image,
                          "LocalName",
                          self.binarydata.storeData(
                    getattr(user.own_styles,
                            user.get_webtop_bg_name()).data))
                make_attr(bg_image,
                          "ContentType",
                          getattr(user.own_styles,
                                  user.get_webtop_bg_name()).getContentType())
                elem.appendChild(bg_image)
        except AttributeError:
            # Some problem with bg image. Let's just leave it out.
            pass

        if user.get_photo() and len(user.get_photo())>0:
            photo = self.dom.createElement("Photo")
            make_attr(photo,
                "LocalName",
                self.binarydata.storeData(user.get_photo()))
            if user.get_photo_type():
                make_attr(photo,
                          "ContentType",user.get_photo_type())
            elem.appendChild(photo)

        if len(user.get_quote())>0:
            quote = self.dom.createElement("Quote")
            make_text(quote,user.get_quote())
            elem.appendChild(quote)

        if len(user.get_background())>0:
            back = self.dom.createElement("Background")
            make_text(back,user.get_background())
            elem.appendChild(back)

        if len(user.get_personal_interests())>0:
            personal = self.dom.createElement("Personal")
            make_text(personal,user.get_personal_interests())
            elem.appendChild(personal)

        if len(user.get_professional_interests())>0:
            pro = self.dom.createElement("Professional")
            make_text(pro,user.get_professional_interests())
            elem.appendChild(pro)

        try:
            if len(user.get_groups()) > 0:
                groups = self.dom.createElement("Groups")
                for gid in user.get_groups():
                    group = self.dom.createElement("Group")
                    make_attr(group, "GroupID", gid)
                    groups.appendChild(group)
                elem.appendChild(groups)
        except AttributeError:
            # We'll end up here if we're export from a pre 1.4 version
            # database
            pass

        if do_webtop:
            elem.appendChild(self.exportWebtop(user.webtop))

        return elem

    def importUser(self,elem,fle_users,do_user,do_webtop):
        """Import a user into the UserManager.
        If the user already exists, we'll just skip user creation."""

        uname = get_attr(elem,"Name")
        if not do_user:
            try:
                user = fle_users.get_child(uname)
            except AttributeError:
                return
        else:
            try:
                fle_users.get_user_info(uname)
            except:
                pass
            else:
                print "Skipping import of pre-existing user "+uname
                return

            (password, domains, roles) = \
                       self.retrieveUserACL(elem.getElementsByTagName("ACL")[0])
            # If the user has no roles and no password, we'll just skip.
            if not password and not roles:
                return

            try:
                user = fle_users.add_user(
                    uname,
                    password,
                    roles,
                    domains)
            except:
                # Error adding user - just skip
                return
            if not user:
                # OK, user adding failed more nicely. Skip again
                return

            photo=None
            try:
                photo_data = self.binarydata.getData(
                    get_attr(elem.getElementsByTagName("Photo")[0],"LocalName"))
                photo_content = get_attr(elem.getElementsByTagName("Photo")[0],"ContentType")
                photo = FakeUpload('image',photo_data,photo_content)
            except IndexError:
                pass

            try:
                web_bg_image_data = self.binarydata.getData(
                    get_attr(elem.getElementsByTagName("WebtopBackgroundImage")[0],"LocalName"))
            except IndexError:
                web_bg_image_data = ''

            try:
                quote=get_text(elem.getElementsByTagName("Quote")[0])
            except IndexError:
                quote=''

            try:
                background=get_text(elem.getElementsByTagName("Background")[0])
            except IndexError:
                background=''

            try:
                personal=get_text(elem.getElementsByTagName("Personal")[0])
            except IndexError:
                personal=''

            try:
                professional=get_text(elem.getElementsByTagName("Professional")[0])
            except IndexError:
                professional=''

            try:
                groups = elem.getElementsByTagName("Groups")[0]
                group_ids = [get_attr(group, "GroupID") for
                             group in groups.childNodes]
            except IndexError:
                group_ids = []

            # Pre 1.4 versions did not export nickname.
            nickname = get_attr(elem, "Nickname")
            if nickname: user.set_nickname(nickname)

            user.edit_info(
                first_name = get_attr(elem,"FirstName"),
                last_name = get_attr(elem,"LastName"),
                email = get_attr(elem,"Email"),
                organization = get_attr(elem,"Organisation"),
                language = get_attr(elem,"Lang"),
                photo_upload = photo,
                # photo_url = '',
                group_ids = group_ids,
                address1 = get_attr(elem,"Address1"),
                address2 = get_attr(elem,"Address2"),
                city = get_attr(elem,"City"),
                country = get_attr(elem,"Country"),
                homepage = get_attr(elem,"Homepage"),
                phone = get_attr(elem,"Phone"),
                gsm = get_attr(elem,"Mobile"),
                quote = quote,
                background = background,
                personal_interests = personal,
                professional_interests = professional,
                )

            if web_bg_image_data:
                user.set_webtop_bg_from_image_data(web_bg_image_data)
            else:
                image_name = get_attr(elem,"WebtopBgImagePath")[len('images/'):]
                if image_name:
                    try:
                        user.set_webtop_bg_from_default_image(image_name)
                    except KeyError:
                        # We get this if the specified default image
                        # doesn't exist
                        pass

            if get_attr(elem,"Frozen"):
                fle_users.freeze_user(user.get_uname())

        if do_webtop:
            wtelems = elem.getElementsByTagName("Webtop")
            if len(wtelems)>0:
                webtop=user.__of__(fle_users).webtop
                self.importWebtop(wtelems[0],webtop)

    def exportWebtop(self,webtop):
        """Export a user's webtop."""

        elem = self.dom.createElement("Webtop")
        self.exportWebtopFolderContents(webtop,elem)
        return elem

    def importWebtop(self,elem,webtop):
        """Import a user's webtop."""
        self.importWebtopFolderContents(elem,webtop)

    def exportWebtopItemAttrs(self,item,elem):
        """Export attributes common to all webtop items
        into a predefined XML element."""
        make_attr(elem,"Name",item.get_name())
        make_attr(elem,"Date",str(int(item.get_timestamp())))
        make_attr(elem,"Owner",str(item.get_author_name()))

    def importWebtopItemAttrs(self,elem,item):
        """Import attributes common to all WebtopItems."""
        item.set_timestamp(int(get_attr(elem,"Date")))
        owner = get_attr(elem,"Owner")
        if owner:
            try:
                item.set_author(owner)
            except AttributeError:
                pass
##         elif hasattr(item,'get_uname'):
##             item.set_author(item.get_uname()) # Acquired from UserInfo

    def exportWebtopFolder(self,folder):
        """Export a folder from a user's webtop."""
        elem = self.dom.createElement("WebtopFolder")
        self.exportWebtopItemAttrs(folder,elem)
        self.exportWebtopFolderContents(folder,elem)
        return elem

    def exportGroupFolder(self,folder):
        """Export a group folder."""
        elem = self.dom.createElement("GroupFolder")
        self.exportWebtopItemAttrs(folder,elem)
        self.exportWebtopFolderContents(folder,elem)
        make_attr(elem,"ID",folder.get_id())
        return elem

    def importWebtopFolder(self,elem,parent):
        """Imports a webtop folder into the specified parent folder."""
        name = get_attr(elem,"Name")
        folder = parent.add_folder(name)
        self.importWebtopItemAttrs(elem,folder)
        self.importWebtopFolderContents(elem,folder)
        return folder

    def importGroupFolder(self,elem,parent,toplevel=0):
        folder = self.importWebtopFolder(elem,parent)
        if toplevel:
            self.idmap[get_attr(elem,'ID')]=folder

    def exportWebtopFolderContents(self,folder,elem):
        """Export a folder's contents from a webtop, into
        a predefined XML element. This method is called from
        both exportWebtop and exportWebtopFolder."""
        for fol in folder.objectValues('WebtopFolder'):
            elem.appendChild(self.exportWebtopFolder(fol))
        for file in folder.objectValues('WebtopFile'):
            elem.appendChild(self.exportWebtopFile(file))
        for link in folder.objectValues('WebtopLink'):
            elem.appendChild(self.exportWebtopLink(link))
        for memo in folder.objectValues('WebtopMemo'):
            elem.appendChild(self.exportWebtopMemo(memo))
        for fol in folder.objectValues('GroupFolder'):
            elem.appendChild(self.exportGroupFolder(fol))

        return elem

    def importWebtopFolderContents(self,elem,folder):
        """Import a webtop folder's contents."""
        for celem in elem.childNodes:
            if celem.nodeName == 'WebtopFolder':
                self.importWebtopFolder(celem,folder)
            elif celem.nodeName == 'WebtopFile':
                self.importWebtopFile(celem,folder)
            elif celem.nodeName == 'Link':
                self.importWebtopLink(celem,folder)
            elif celem.nodeName == 'WebtopMemo':
                self.importWebtopMemo(celem,folder)
            elif celem.nodeName == 'GroupFolder':
                self.importGroupFolder(celem,folder)

    def exportWebtopFile(self,file):
        """Export a file from a user's webtop."""
        elem = self.dom.createElement("WebtopFile")
        self.exportWebtopItemAttrs(file,elem)
        make_attr(elem,
            "LocalName",
            self.binarydata.storeData(file.data))
        make_attr(elem,"ContentType",file.getContentType())
        return elem

    def importWebtopFile(self,elem,folder):
        """Imports a webtop file into the given folder."""
        data = self.binarydata.getData(get_attr(elem,"LocalName"))
        name = get_attr(elem,"Name")
        file = folder.add_file(
            name,
            FakeUpload(name,data,get_attr(elem,"ContentType")))
        self.importWebtopItemAttrs(elem,file)

    def exportWebtopLink(self,link):
        """Export a link from a user's webtop."""
        elem = self.dom.createElement("Link")
        self.exportWebtopItemAttrs(link,elem)
        try:
            if link.is_internal_link():
                make_attr(elem,"IDRef",link.get_obj_ref().get_id())
                return elem
        except TypeError:
            # We get this if is_internal_link requires parameters.
            # Exporting from older versions may cause this.
            # We'll just handle those links as external.
            pass
        except AttributeError:
            # This means a link is broken (doesn't point to an
            # existing object). Let's just skip export.
            pass

        make_attr(elem,"Src",link.get_url())
        return elem

    def importWebtopLink(self,elem,folder):
        """Imports a webtop link into the given folder."""
        name = get_attr(elem,"Name")
        src = get_attr(elem,"Src")
        objref = get_attr(elem,"IDRef")
        if objref:
            try:
                obj = self.idmap[objref]
                link = folder.add_link(name, obj, 1)
            except KeyError:
                # We get a keyerror if the id is not found.
                print "WebtopLink %s with target id %s doesn't exist!" % (name,objref)
                return
        else:
            link = folder.add_link(name, src)
        self.importWebtopItemAttrs(elem,link)

    def exportWebtopMemo(self,memo):
        """Export a memo from a user's webtop."""
        elem = self.dom.createElement("WebtopMemo")
        self.exportWebtopItemAttrs(memo,elem)
        celem = self.dom.createElement("Contents")
        make_text(celem,memo.get_body())
        elem.appendChild(celem)
        return elem

    def importWebtopMemo(self,elem,folder):
        """Imports a webtop memo into the given folder."""
        name = get_attr(elem,"Name")
        contents=get_text(elem.getElementsByTagName("Contents")[0])
        memo = folder.add_memo(name, contents)
        self.importWebtopItemAttrs(elem,memo)

#EOF



