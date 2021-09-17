# $Id: input_checks.py,v 1.24 2004/09/15 09:43:49 tarmo Exp $

# Copyright 2001, 2002, 2003 by Fle3 Team and contributors-2002
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

import string
import re
from types import UnicodeType
from NanoDom import strip_non_xml

def is_valid_uname(uname):
    #allowed = "".join([chr(i) for i in range(ord('a'), ord('z')+1)]) + \
    #          "".join([chr(i) for i in range(ord('A'), ord('Z')+1)]) + \
    #          string.digits
    allowed = string.letters+string.digits+" _-"
    for c in uname:
        if c not in allowed:
            return 0
    return 1

def is_valid_url(url):
    """Check if given URL is valid."""
    # FIXME: Add some more strict checks here...
    return is_valid_title(url) and re.search('^[a-z]+\:[a-z/]+',url)

# This should accept most reasonable one line human
# readable string. Use something more strict for ids.
def is_valid_title(name):
    """Check if given name is valid."""

    if len(name) == 0:
        return 0
    if name[0] in string.whitespace or name[-1] in string.whitespace:
        return 0
    for c in name:
        if c in '<>\t\n\r\x0b\x0c':
            return 0
    return 1

def is_valid_id(name):
    if not is_valid_title(name):
        return 0
    allowed = "".join([chr(i) for i in range(ord('a'), ord('z')+1)]) + \
              "".join([chr(i) for i in range(ord('A'), ord('Z')+1)]) + \
              string.digits + '_-'
    for c in name:
        if c not in allowed:
            return 0
    return 1

def is_valid_date(dd, mm, yyyy):
    """Check if given date is valid."""
    return 1

# legal_tags should be a list of element names without angle brackets,
# e.g. ('p','b','br')
def strip_tags(s, legal_tags=[]):
    """Return a string with almost all tags removed."""
    s=strip_non_xml(s)

##     utf_prefixes = ''.join([chr(x) for x in range(240,256)])
##     control_chars = '|'.join([chr(x) for x in range(0,32)])
##     print repr(utf_prefixes)
##     print repr(control_chars)
##     #s=re.sub('([^\xff\xfe\xfd\xfc\xfb\xfa])(\x0f|\x0e)','\\1',s,re.M)
##     s=re.sub('([^%s])(%s)' % (utf_prefixes,control_chars),'\\1',s,re.M)

    # Append closing tags for all elements.
    tags = [x for x in legal_tags] + ['/'+x for x in legal_tags]

    # We have to add space after tag, because otherwise (for example)
    # if we have 'i' in legal_tags, the regular expression would accept
    # tags like 'img'...
    tags1 = [x + ' ' for x in tags]
    tags2 = [x + '>' for x in tags]
    tags3 = [x + '/>' for x in tags] # Allow tags like <br/>
    tags = tags1 + tags2 + tags3

    # If no tags are allowed, we need to use something here
    # so that the regexp works correctly.
    if not tags:
        tags=['___']
    else:
        # Convert legal upper case tags to lower case. (We don't
        # care about illegal tags as they are thrown away anyway...)
        for tag in tags:
            s = re.sub('<'+string.upper(tag), '<'+tag, s)

    # Remove all tags that do not contain an opening or closing
    # version of the allowed tags.
    return re.sub("<(?!("+'|'.join(tags)+")).*?>","",s,re.M)

def strip_all(s):
    """Strip leading and tailing white space + all HTML tags (i.e.
    all stuff inside < and > characters (including those chars.))"""
    return strip_tags(s.strip())


normal_entry_tags = ['p','br','i','b','ul','ol','li']
normal_entry_tags_and_link = normal_entry_tags + ['a']

def render(
    text,
    do_strip=1,
    legal_tags=[],
    do_vertical_space=1,
    do_horizontal_space=0,
    ignore_whitespace_magic=('p','br')
    ):
    """Render given text with whitespace respect on, optionally
    removing all or some tags."""

    if do_strip:
        text = strip_tags(text,legal_tags)

    ig_0 = ['<'+x for x in ignore_whitespace_magic]
    ignore = [x.upper() for x in ig_0] + ig_0

    for magic in ignore:
        if text.find(magic)>-1:
            return text

    # According to Jukka Korpela
    # (http://www.cs.tut.fi/~jkorpela/HTML3.2/5.56.html):
    # 'It is recommended in the specifications that browsers
    # canonicalize line endings to CR, LF (ASCII decimal 13, 10)
    # when submitting the contents of the field. However, authors
    # should not rely on this, since not all browsers behave so.'
    #
    # So, let's be paranoid...
    # ... and normalize all line feeds to \n
    lf1 = re.compile('\r\n')
    lf2 = re.compile('\r')
    text = lf1.sub('\n',text)
    text = lf2.sub('\n',text)

    # Convert spaces and tabs to &nbsp;s at the beginning of
    # the paragraphs. (Makes some kind of indentation possible.)
    if do_horizontal_space:
        lines = [list(x) for x in text.split('\n')]
        for i in range(len(lines)):
            for j in range(len(lines[i])):
                if lines[i][j] == ' ':
                    lines[i][j] = '&nbsp;'
                elif lines[i][j] == '\t':
                    lines[i][j] = '&nbsp;&nbsp;&nbsp;&nbsp;'
                else:
                    break
            lines[i] = ''.join(lines[i])

        text = '\n'.join(lines)

    if do_vertical_space:
        vert1 = re.compile('\n\n')
        vert2 = re.compile('\n')
        text = vert1.sub("</p><p>",text)
        text = vert2.sub("<br />",text)
        text = "<p>"+text+"</p>"

    return text

def wordwrap(text,limit=66):
    words = text.split(' ')
    text = ''
    line = ''
    width = -1
    for word in words:
        width += len(word)+1
        if '\n' in word:
            width=-1+len(word)-word.rfind('\n')
        if width>limit:
            width = -1
            text = text + "\n" + line
            line = ''
            width += len(word)+1
        if line:
            line = line + ' ' + word
        else:
            line = word
    text = text[1:] + "\n" + line
    return text
