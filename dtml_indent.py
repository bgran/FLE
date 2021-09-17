#! /usr/bin/env python
# $Id: dtml_indent.py,v 1.3 2002/01/03 12:19:23 granbo Exp $
# Usage:
# % cat somefile.html | python filter.py > outputfile.html

if __name__ == '__main__':
        import sys, re, string
        rv = []
        while 1:
                buf = sys.stdin.read()
                if not buf: break
                rv.append(re.sub(chr(0x9), ' ', buf))
        print string.join(rv, '')

# EOF
