# $Id: ImportExportEML.py,v 1.7 2003/06/13 07:57:11 jmp Exp $
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

"""Contains classes responsible for importing and exporting the data to and from an FLE installation. Uses XML formatted EML documents for storage."""

import sys
import xml.dom.minidom
from xml.dom.minidom import Document
import zipfile
import time
from types import FloatType

from ImportExport import Counter, DataTable, to_utf8

def date2str(date):
    if not type(date)==type(()):
        date = time.gmtime(date)
    return time.strftime('%Y/%m/%d',date)

def str2date(str):
    return time.mktime(time.strptime(str,'%Y/%m/%d'))

def to_id(id):
    id=str(id)
    if id[0]>='0' and id[0]<='9':
        id='id'+id
    return id.replace('_','-')


class Exporter:
    """Class that handles the exporting (but not yet importing) of data
    to EML and also holds the XMLized content."""

    # If the parameter 'file' is specified, it is assumed to be
    # an uploaded zip file containing exported data and it is
    # loaded into memory. Otherwise an empty Exporter is created.
    def __init__(self,file=None):
        """Creates a new Exporter."""
        # Add a binary data hash table
        self.binarydata = DataTable()
        self.idmap = {}

        if file:
            self.loadZip(file)
        else:
            # Document: unlink, writexml(writer), toxml()
            self.dom = Document()
            type=xml.dom.minidom.DocumentType('"Unit-of-study PUBLIC "-//OUNL//DTD EML/XML binding 1.0/1.0//EN" "eml10.dtd"')
            self.dom.doctype=type
            self.root = self.dom.createElement("unit-of-study")
            self.root.setAttribute("encoding","utf-8")
            self.dom.appendChild(self.root)

    def createZip(self,file):
        """Dumps the currently exported data
        (XML document and binary files) into a zip file.

        - file: name of the file to create"""
        zip = zipfile.ZipFile(file,"w",zipfile.ZIP_DEFLATED)
        zip.writestr(zipfile.ZipInfo("fle_eml.xml"),self.dom.toxml())
        for name in self.binarydata.getNames():
            zip.writestr(
                zipfile.ZipInfo(name),
                str(self.binarydata.getData(name)))
        zip.close()

    def loadZip(self,file):
        """Loads a zipped FLE content file.

        - file: the file name to load."""
        zip = zipfile.ZipFile(file,"r",zipfile.ZIP_DEFLATED)

        xmlstring = unicode(
            zip.read("fledom.xml"), 'iso-8859-1').encode("utf-8")
        self.dom = xml.dom.minidom.parseString(xmlstring)
        self.root = self.dom.firstChild

        for name in zip.namelist():
            if name[:4]=='data':
                self.binarydata.restoreData(name,zip.read(name))
        zip.close()

    def exportCourse(self,course):
        """Exports the given course into an EML unit of study."""
        newElem = self.dom.createElement
        newText = self.dom.createTextNode

        elem = newElem("metadata")
        elem2 = newElem("title")
        elem2.appendChild(newText(course.get_name()))
        elem.appendChild(elem2)

        elem2 = newElem("creator")
        elem2.appendChild(newText(course.get_teacher()))
        elem.appendChild(elem2)

        elem2 = newElem("description")
        elem3 = newElem("p")
        elem3.appendChild(newText(course.get_description()))
        elem2.appendChild(elem3)
        elem.appendChild(elem2)

        elem2 = newElem("copyright")
        elem3 = newElem("copyright-year")
        elem3.appendChild(newText(date2str(course.get_end_date())[:4]))
        elem2.appendChild(elem3)
        elem3 = newElem("copyright-owner")
        elem3.appendChild(newText(course.get_organisation()))
        elem2.appendChild(elem3)
        elem.appendChild(elem2)

        elem2 = newElem("extra-meta")
        elem3 = newElem("creation-date")
        elem3.appendChild(newText(date2str(course.get_start_date())))
        elem2.appendChild(elem3)
        elem3 = newElem("date-last-change")
        elem3.appendChild(newText(date2str(course.get_end_date())))
        elem2.appendChild(elem3)
        elem3 = newElem("meta")
        elem3.setAttribute("base","FLE3")
        elem3.setAttribute("description","metatype")
        elem4 = newElem("unstructured-source")
        elem4.appendChild(newText("Course"))
        elem3.appendChild(elem4)
        elem2.appendChild(elem3)
        elem.appendChild(elem2)

        self.root.appendChild(elem)

        elem = newElem("roles")

        elem2 = newElem("learner")
        elem2.setAttribute("id","learner")
##         elem3 = newElem("role")
##         elem3.setAttribute("name","student")
##         elem2.appendChild(elem3)
##         elem3 = newElem("role")
##         elem3.setAttribute("name","tutor")
##         elem2.appendChild(elem3)
##         elem3 = newElem("role")
##         elem3.setAttribute("type","Facilitator")
##         elem3.setAttribute("name","teacher")
##         elem2.appendChild(elem3)
        elem.appendChild(elem2)
        elem2 = newElem("staff")
        elem2.setAttribute("id","staff")
##         elem3 = newElem("role")
##         elem3.setAttribute("name","student")
##         elem2.appendChild(elem3)
##         elem3 = newElem("role")
##         elem3.setAttribute("name","tutor")
##         elem2.appendChild(elem3)
##         elem3 = newElem("role")
##         elem3.setAttribute("type","Facilitator")
##         elem3.setAttribute("name","Teacher")
##         elem2.appendChild(elem3)
        elem.appendChild(elem2)

        self.root.appendChild(elem)

        elem = newElem("content")
        elem2 = newElem("activity")
        elem2.setAttribute("reusability","reusable")
        elem2.setAttribute("id","act0")
        elem3 = newElem("activity-description")
        elem4 = newElem("what")
        elem5 = newElem("p")
        elem5.appendChild(newText("Reflection on already completed knowledge building."))
        elem4.appendChild(elem5)
        elem3.appendChild(elem4)
        elem4 = newElem("completed")
        elem4.appendChild(newElem("unrestricted"))
        elem3.appendChild(elem4)
        elem2.appendChild(elem3)
        elem.appendChild(elem2)

        for ctx in course.get_children("CourseContext"):
            elem2 = elem.appendChild(self.exportContext(ctx))
            elem.appendChild(elem2)

        elem.appendChild(elem2)
        self.root.appendChild(elem)

        elem = newElem("method")
        elem2 = newElem("play")
        elem3 = newElem("comment")
        elem3.appendChild(newText("The original methods for building this knowledge were as follows:\n"+course.get_methods()))
        elem2.appendChild(elem3)
        elem3 = newElem("role-ref")
        elem3.setAttribute("id-ref","learner")
        elem2.appendChild(elem3)
        elem3 = newElem("activity-ref")
        elem3.setAttribute("id-ref","act0")
        elem2.appendChild(elem3)
        elem.appendChild(elem2)
        self.root.appendChild(elem)

        return elem


    def exportContext(self,ctx):
        """Exports the given course context."""
        newElem = self.dom.createElement
        newText = self.dom.createTextNode

        elem = newElem("environment")
        elem.setAttribute("id",to_id(ctx.get_id()))
        elem2 = newElem("metadata")
        elem3 = newElem("title")
        elem3.appendChild(newText(ctx.get_name()))
        elem2.appendChild(elem3)
        elem3 = newElem("creator")
        elem3.appendChild(newText(ctx.get_author()))
        elem2.appendChild(elem3)
        elem3 = newElem("description")
        elem4 = newElem("p")
        elem4.appendChild(newText(ctx.get_description()+"\n\n"+ctx.get_long_description()))
        elem3.appendChild(elem4)
        elem2.appendChild(elem3)

        elem3 = newElem("extra-meta")
        elem4 = newElem("meta")
        elem4.setAttribute("base","FLE3")
        elem4.setAttribute("description","metatype")
        elem5 = newElem("unstructured-source")
        elem5.appendChild(newText("CourseContext"))
        elem4.appendChild(elem5)
        elem3.appendChild(elem4)
        elem2.appendChild(elem3)
        elem.appendChild(elem2)

        elem.appendChild(self.exportTTS(ctx.get_thinking_type_set()))

        frag = self.dom.createDocumentFragment()
        for note in ctx.get_children('Note'):
            self.exportNote(frag,note)

        elem.appendChild(frag)
        return elem


    def exportTTS(self,set):
        """Exports the given knowledgetypeset."""
        newElem = self.dom.createElement
        newText = self.dom.createTextNode

        elem = newElem("knowledge-object")
        elem2 = newElem("metadata")
        elem3 = newElem("title")
        elem3.appendChild(newText(set.get_name()))
        elem2.appendChild(elem3)
        elem3 = newElem("description")
        elem4 = newElem("p")
        elem4.appendChild(newText(set.get_description()))
        elem3.appendChild(elem4)
        elem2.appendChild(elem3)

        elem3 = newElem("extra-meta")
        elem4 = newElem("meta")
        elem4.setAttribute("base","FLE3")
        elem4.setAttribute("description","metatype")
        elem5 = newElem("unstructured-source")
        elem5.appendChild(newText("ThinkingTypeSet"))
        elem4.appendChild(elem5)
        elem3.appendChild(elem4)
        elem2.appendChild(elem3)
        elem.appendChild(elem2)

        elem2 = newElem("source")

        for type in set.get_thinking_types():
            elem3 = newElem("section")
            elem3.setAttribute("id",to_id(set.parent().get_id()+'-'+type.get_id()))
            elem4 = self.exportTT(type)
            elem3.appendChild(elem4)
            elem2.appendChild(elem3)
        elem.appendChild(elem2)

        return elem

    def exportTT(self,type):
        """Exports the given knowledgetype."""
        newElem = self.dom.createElement
        newText = self.dom.createTextNode

        elem = newElem("source")
        elem2 = newElem("figure")
        elem3 = newElem("figure-source")
        elem3.setAttribute(
            "entity",
            self.binarydata.storeData(type.get_icon().data))
        elem2.appendChild(elem3)
        elem.appendChild(elem2)
        elem2 = newElem("p")
        elem2.appendChild(newText(type.get_name()))
        elem.appendChild(elem2)
        elem2 = newElem("p")
        elem2.appendChild(newText(type.get_description()))
        elem.appendChild(elem2)

        return elem

    def exportNote(self,frag,note):
        """Exports the given note."""
        newElem = self.dom.createElement
        newText = self.dom.createTextNode

        elem = newElem("knowledge-object")
        elem.setAttribute("id",to_id(note.get_id()))
        elem2 = newElem("metadata")
        elem3 = newElem("title")
        elem3.appendChild(newText(note.get_real_subject()))
        elem2.appendChild(elem3)
        elem3 = newElem("creator")
        elem3.appendChild(newText(note.get_author()))
        elem2.appendChild(elem3)

        elem3 = newElem("extra-meta")
        elem4 = newElem("creation-date")
        elem4.appendChild(newText(date2str(note.get_creation_time())))
        elem3.appendChild(elem4)
        elem4 = newElem("meta")
        elem4.setAttribute("base","FLE3")
        elem4.setAttribute("description","metatype")
        elem5 = newElem("unstructured-source")
        elem5.appendChild(newText("Note"))
        elem4.appendChild(elem5)
        elem3.appendChild(elem4)
        elem4 = newElem("meta")
        elem4.setAttribute("base","FLE3")
        elem4.setAttribute("description","parent")
        elem5 = newElem("unstructured-source")
        elem5.appendChild(newText(note.parent().get_id()))
        elem4.appendChild(elem5)
        elem3.appendChild(elem4)
        elem4 = newElem("meta")
        elem4.setAttribute("base","FLE3")
        elem4.setAttribute("description","type")
        elem5 = newElem("unstructured-source")
        elem5.appendChild(newText(note.get_tt_id()))
        elem4.appendChild(elem5)
        elem3.appendChild(elem4)
        elem2.appendChild(elem3)
        elem.appendChild(elem2)

        elem2 = newElem("source")
        elem3 = newElem("p")
        elem3.appendChild(newText(note.get_body()))
        elem2.appendChild(elem3)

        if note.get_url()!='':
            elem3 = newElem("internet-source")
            elem3.setAttribute("url",note.get_url())
            elem3.setAttribute("link-name",note.get_url_name())
            elem2.appendChild(elem3)

        if note.has_image():
            name = self.binarydata.storeData(
                note.get_image_data())
            elem3 = newElem("figure")
            elem4 = newElem("figure-source")
            elem4.setAttribute("entity",name)
            elem3.appendChild(elem4)
            elem4 = newElem("figure-text")
            elem5 = newElem("p")
            elem5.appendChild(newText(note.get_image_name()))
            elem4.appendChild(elem5)
            elem3.appendChild(elem4)
            elem2.appendChild(elem3)

        elem.appendChild(elem2)

        frag.appendChild(elem)

        for reply in note.get_children('Note'):
            self.exportNote(frag,reply)



#EOF


