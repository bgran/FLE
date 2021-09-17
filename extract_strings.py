#!/usr/bin/env python

# $Id: extract_strings.py,v 1.2 2003/06/13 07:57:12 jmp Exp $
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

import sys
import re

"""Extract all translated strings from the vocabulary file. This is useful
if you want to spell check your translation."""

def extract(in_file, out_file):
    buffer = in_file.read()
    in_file.close()
    buffer =re.sub('{', '(',   buffer)
    buffer =re.sub('}', ')',   buffer)
    buffer =re.sub("':" ,"',", buffer)

    exec buffer
    for i in range(0, len(vocabulary)):
        if not (i % 2):
            if i: out_file.write('\n\n\n')
            continue
        for j in range(0, len(vocabulary[i])):
            if not (j % 2): continue
            out_file.write(vocabulary[i][j][0] + '\n')

    out_file.close()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        extract(open(sys.argv[1], "r"), sys.stdout)
    elif len(sys.argv) == 3:
        extract(open(sys.argv[1], "r"), open(sys.argv[2], "w"))
    else:
        sys.stderr.write('Usage: %s infile [outfile]\n' % sys.argv[0])
