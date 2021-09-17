# $Id: FilterManager.py,v 1.14 2003/06/13 07:57:11 jmp Exp $
#
# Copyright 2001, 2002, 2003 by Fle3 Team and contributors

"""Unused currently."""

__version__ = "$Revision: 1.14 $"[11:-2]

import os, sys
join = os.path.join

import Globals
import OFS
from Globals import MessageDialog as msg_diag
from Globals import Persistent
from Products.PythonScripts import PythonScript as ps

from TraversableWrapper import TraversableWrapper
from common import file_path, iterate_fs_files
filter_file_path = join(file_path, 'filters')
raise 'tjoo', "Don't use this file!!"
class FilterManager(
    Persistent,
    OFS.Folder.Folder,
    OFS.SimpleItem.Item,
    #TraversableWrapper
    ):
    """Filter manager folder."""
    meta_type = 'FilterManager'

    def __init__(self, id, title):
        """Construct filter manager with id and title."""
        self.id = id
        self.title = title

        # Add python scripts.
        iterate_fs_files(
            filter_file_path, '.py',
            self.add_filter)

    def add_filter(self, file):
        """Add Zope PythonScript to self folder.
        abs_file = 'python_script_name.py', with suffixing '.py'!"""
        search_dir = filter_file_path
        filter_name = file[:-3]
        p_obj = ps.PythonScript(filter_name)
        py_contents = open(join(search_dir, file)).read()
        p_obj.write(py_contents)
        self._setObject(filter_name, p_obj)

    def add_overwrite_filter(self, file):
        """Adds, and overwrites if already existing, a filter."""
        try:
            o = getattr(self, file[:-3])
        except AttributeError:
            pass
        else:
            self.manage_delObjects(str(o.id))
        self.add_filter(file)

    def reload_filters(self, REQUEST=None):
        """Reload scripts ->
        - Delete all scripts from folder.
        - Iterate over each python file in filter_file_path; add them."""
        iterate_fs_files(
            filter_file_path, '.py',
            self.add_overwrite_filter)

        if REQUEST:
            return msg_diag(
                title="Filters reloaded",
                message="Filters have been reloaded.",
                action="")

    def list_filters(self):
        """Return a list of filters available. This can't
        really be cached, because zodb contents can vary from time
        to time."""
        return self.objectIds('Script (Python)')

    def parse_filters(self, url):
        return None


# EOF
