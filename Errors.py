# $Id: Errors.py,v 1.7 2003/06/13 07:57:11 jmp Exp $
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

"""Will contain the error classes FLE raises. Not currently in use."""

__version__ = "$Revision: 1.7 $"[11:-2]

class FleError(Exception):
    def __init__(self, args):
        Exception.__init__(self, args)

class UserAlreadyInGroup(FleError): pass
class NoSuchUser(FleError): pass

# EOF
