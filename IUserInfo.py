# $Id: IUserInfo.py,v 1.6 2003/06/13 07:57:11 jmp Exp $
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

"""Contains an interface for UserInfo."""

__version__ = "$Revision: 1.6 $"[11:-2]

from Interface import Base

class IUserInfo(Base):
    """Interface for UserInfo."""

    def set_first_name(self, name):
        """Set the first name of the user."""
    def set_last_name(self, name):
        """Set the last name of the user."""
    def set_email(self, email):
        """Set the email address of the user."""
    def set_language(self, language):
        """Set the users language. (Languages are handled by Language.py)."""
    def set_photo(self, photo):
        """Set the user photo."""
    def set_group(self, group):
        """Set the users group."""
    def set_address(self, address):
        """Set the users address."""
    def set_country(self, country):
        """Set the users country."""
    def set_homepage(self, homepage):
        """Set the users homepage."""
    def set_phone(self, phone):
        """Set the phonenumber of the user."""
    def set_gsm(self, gsm):
        """Set the gsm (mobile phone) number of the user."""
    def set_quote(self, quote):
        """Set the user quote."""
    def set_background(self, background):
        """Set the user background."""
    def set_personal_interests(self, p_i):
        """Set the users personal interests."""
    def set_professional_interests(self, p_i):
        """Set the users professional interests."""

    def get_first_name(self, name):
        """Get the first name of the user."""
    def get_last_name(self, name):
        """Get the last name of the user."""
    def get_email(self, email):
        """Get the email address of the user."""
    def get_language(self, language):
        """Get the users language."""
    def get_photo(self, photo):
        """Get the user photo."""
    def get_group(self, group):
        """Get the users group."""
    def get_address(self, address):
        """Get the users address."""
    def get_country(self, country):
        """Get the users country."""
    def get_homepage(self, homepage):
        """Get the users homepage."""
    def get_phone(self, phone):
        """Get the phonenumber of the user."""
    def get_gsm(self, gsm):
        """Get the gsm (mobile phone) number of the user."""
    def get_quote(self, quote):
        """Get the user quote."""
    def get_background(self, background):
        """Get the user background."""
    def get_personal_interests(self, p_i):
        """Get the users personal interests."""
    def get_professional_interests(self, p_i):
        """Get the users professional interests."""

# EOF

