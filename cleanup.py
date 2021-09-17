#! /usr/bin/env python
#
# FLE cleanup tool. Please use this script on files that are supposed
# to be added to the repository.
#
# $Id: cleanup.py,v 1.2 2001/12/13 18:58:31 granbo Exp $

__version__ = '$Revision: 1.2 $'[11:-2]

import sys, os, getopt
import string, re

from os.path import abspath, join

create_cleanups = 0
do_nothing = 1

def walk_clb(arg, dirname, names):
    try:
        if dirname[-4:] == '/CVS':
            return
    except IndexError: pass

    f = lambda x,i=os.path.isdir:x[-3:]=='.py' and not i(x)
    for file in filter(f, names):
        abs_file = join(dirname, file)
        sys.stdout.write("Processing: %s.." % (abs_file))
        sys.stdout.flush()

        # Get file data
        file_data = open(abs_file, "r").readlines()

        file_buf = []
        whitespace = string.whitespace
        whitespace = string.join(
            filter(lambda x,c=chr:x!=c(10), whitespace), '')

        # Do processing:
        for line in file_data:
            # Covert tabs to 8 spaces.
            s8 = chr(32) * 8
            tab = chr(9)
            line = re.sub(tab, s8, line)

            # Filter lineends to be \n, only!
            # I don't know currently of other combinations than \r\n
            line = re.sub(chr(13)+chr(10), chr(10), line)

            # Allow no whitespace between end of file and the last
            # occurence of text.
            buf = []
            rev = string.join(
                [line[x] for x in range(-1, -len(line)-1, -1)], '')
            # Sorry for implementing these dfa:s as python formalisms,
            # but I don't like regexps. ;)
            start_newline = 0
            terminal_c = 0
            nw = 0
            for e in rev:
                if e == chr(10):
                    start_newline = 1
                    buf.append(e)
                else:
                    # Oh god.
                    if start_newline:
                        if e in whitespace:
                            if terminal_c:
                                buf.append(e)
                        else:
                            if not terminal_c:
                                terminal_c = 1
                                buf.append(e)
                            else:
                                buf.append(e)
                    else:
                        raise 'Error', "Line reverse doesn't start with newline."
            # And then reverse the thing back.
            buf.reverse()
            line = string.join(buf, '')

            # Add line to buffer.
            file_buf.append(line)

        if not do_nothing:
            if create_cleanups:
                # Ok.
                sys.stdout.write("writing..")
                sys.stdout.flush()
                f = open(abs_file, 'w')
                f.write(string.join(file_buf, ''))
                f.close()
        sys.stdout.write("[DONE]\n")
        sys.stdout.flush()

def do_cleanup(cwd):
    print "Starting cleanups."
    os.path.walk(cwd, walk_clb, ())

if __name__ == '__main__':
    print 'FLE3 cleanup tool version %s' % (__version__)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'x')
    except getopt.GetoptError:
        usage()
        sys.exit(255)

    for (o, a) in opts:
        if o in ('-x',):
            do_nothing = 0
            create_cleanups = 1
        if o in ('-n',):
            do_nothing = 1

    # Checking
    cwd = os.path.abspath(".")
    print "Using: %s" % (cwd)
    assert os.path.isdir(cwd), 'Pretty weak: the current directory is not.'
    do_cleanup(cwd)

# EOF
