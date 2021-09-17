#!/usr/bin/env python
# $Id: create_docs.py,v 1.16 2003/06/13 07:57:12 jmp Exp $

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

# notice:
# 1. this script needs happydoc program
# Please also notice, that this is a brain-dead script in the current
# configuration :/.

import os

from URLOpener import open_url

HAPPY_PATH = '/usr/local/bin/'
TMP_PATH ='/tmp/'

def create_docs(self):
    os.chdir(TMP_PATH)
    os.system('rm -rf FLE')
    os.system('cvs co FLE')
    os.chdir('FLE')
    os.system(HAPPY_PATH + 'happydoc *.py')

    # Call external method (tools/doc_tools.py copied to Zope/Extensisons) that
    # copies documents from the file system to the Zope.
    open_url("http://flea.uiah.fi:8080/fle3docs/api/reload_docs")

if __name__ == '__main__':
    create_docs(None)

# EOF
