# $Id: PrinterManager.py,v 1.21 2003/06/13 07:57:11 jmp Exp $

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

"""Contains class PrinterManager, which contains printer objects, responsible for rendering Notes in different views. The printers are DTML Methods."""

__version__ = "$Revision: 1.21 $"[11:-2]

import os
join = os.path.join

import OFS, Globals, AccessControl
from Globals import Persistent, Acquisition
from TraversableWrapper import TraversableWrapper
from Cruft import Cruft

from common import file_path, iterate_fs_files
printer_file_path = join(file_path, 'printers')

# FIXME: permissions

# This class is a holder for printers, which are objects that
# do note rendering in dtml.
class PrinterManager(
    TraversableWrapper,
    Cruft,
    Persistent,
    OFS.Folder.Folder,
    OFS.SimpleItem.Item,
    ):
    """Printer manager folder."""

    meta_type = 'PrinterManager'

    def __init__(self, id, title):
        """Construct PrinterManager object."""
        self.id = id
        self.title = title

    def manage_afterAdd(self, item, container):
        """Add printer objects to Zope from fs."""
        self.reload_printers()

    def add_printer(self, file):
        """Add a printer to this folder."""
        search_dir = printer_file_path
        data = open(join(search_dir, file)).read()
        # FIXME: some error checking please

        printer_name = file[:-5]
        self.manage_addDTMLMethod(printer_name, '')

        printer = None
        for e in self.objectValues('DTML Method'):
            if e.id() == printer_name:
                printer = e
                break

        if not printer:
            raise 'This never happened.'

        # So that everybody is able to use printers...
        printer.manage_permission('View', ['Authenticated',], 0)

        # FIXME: Remove if not needed?!? -- ik, jmp
        printer.manage_edit(data, '')

    def reload_printers(self, REQUEST=None):
        """Reload printers."""
        for e in self.objectIds('DTML Method'):
            self.manage_delObjects(e)

        iterate_fs_files(
            printer_file_path, '.dtml',
            self.add_printer)

        if REQUEST:
            self.get_lang(('common','kb'),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_dtml_reloaded'],
                message=REQUEST['L_dtml_files_reloaded'],
                action="")

    def call_printer(self, REQUEST, printer_id, note_obj, start_path=None):
        """Call given printer (output thread or list)."""
        try:
            p = self._getOb(printer_id)
        except AttributeError:
            raise 'FLE Error', 'Unknown printer: %s' % printer_id
        if start_path:
            return p(note_obj, REQUEST, printer=printer_id, start_path=start_path)
        else:
            return p(note_obj, REQUEST, printer=printer_id)

#EOF
