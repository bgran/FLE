#! /usr/bin/env python
#
# Usage:
# % cat somefile.html | python cr_remove.py > outputfile.html

if __name__ == '__main__':
        import sys, re, string
        rv = []
        while 1:
                buf = sys.stdin.read()
                if not buf: break
                rv.append(re.sub(chr(0xd), chr(0xa), buf))
        print string.join(rv, '')

# EOF
