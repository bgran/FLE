# $Id: test.py,v 1.4 2003/06/13 07:57:13 jmp Exp $

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

import sys, os, re
import unittest
sys.path.insert(0,'.')
#sys.path.insert(0,'../')
#print sys.path
import tests

def _getPackagePath(package):
    """Return the path to a given package/module."""
    return os.path.join(os.getcwd(),sys.modules[package].__path__[0])

def collectModules(package):
    """Return a list of modules starting with 'test' in the given package."""
    path=_getPackagePath(package)
    modules = []
    exp = re.compile("^test.+\.py$")
    for f in os.listdir(path):
        if exp.search(f):
            modules.append(f[0:len(f)-3])
    return modules

def collectTests(package):
    """Return a TestSuite, containing all TestCases from a given package."""
    allsuites = unittest.TestSuite()
    modules = collectModules(package)
    for m in modules:
        print 'Importing '+m+'...'
        suite = __import__(m).suite()
        allsuites.addTest(suite)
    return allsuites

def runTests(package):
    """Run all TestCases from a given package."""
    suites = collectTests(package)
    runner=unittest.TextTestRunner()
    print "Starting test run..."
    print
    runner.run(suites)

if __name__=='__main__':
    runTests('tests')

from tests import *

