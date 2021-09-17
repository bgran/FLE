#! /usr/bin/env python
#
# FLE3 installation tool. For copyrights please consult the
# COPYING file provided within.
#
# $Id: install.py,v 1.11 2001/12/19 18:36:54 granbo Exp $

__version__ = '$Revision: 1.11 $'[11:-2]

import sys, os, getopt, shutil
import string

conf = {}

# Valid file prefixes
valid_file_prefixes = ('.txt', '.py', '.dtml', '.xml', '.dtd', '.gif', '.png', '.jpg')

def usage(str=''):
    if str: print str
    print 'Usage: %s [options]' % (sys.argv[0])
    print 'Options:'
    print '\t-i\t[directory path]\tThe installation direcory path (Zope/lib/python/Products/ or something similar)'
    print '\t-h\t\t\t\tThis message'

def walk_clb(arg, dirname, names):
    try:
        if dirname[-4:] == '/CVS':
            return
    except IndexError: pass

    inst_path = arg[0]
    base_install_path = arg[1]
    curr_install_path = dirname

    # See jack hack, hack jack hack
    b = base_install_path   # This is the one that should be shorter
    c = curr_install_path   # And this should be longer
    if len(b) > len(c):
        raise 'base_install_path is longer than curr_install_path. That is not possible!'

    relative_path = c[len(b):]
    try:
        if relative_path[0] == '/':
            relative_path = relative_path[1:]
    except IndexError:
        pass

    # Create install directory
    new_dir = os.path.join(inst_path, relative_path)
    try:
        os.mkdir(new_dir)
    except OSError, err:
        if err.errno == 17:
            pass
        else:
            raise OSError, err

    for file in names:
        i_curr_file = os.path.join(inst_path, relative_path, file)
        b_curr_file = os.path.join(curr_install_path, file)

        if os.path.isdir(b_curr_file): continue
        for prefix in valid_file_prefixes:
            if file[-len(prefix):].lower() == prefix:
                print b_curr_file, " -> ", i_curr_file

                # Overwrite stuff!
                shutil.copyfile(b_curr_file, i_curr_file)

    os.system("chmod -R g+w %s 1>/dev/null 2>/dev/null" % (inst_path))
    print '---------------------------------'

def do_install(conf):
    os.path.walk(conf.get('base_dir'),
                 walk_clb,
                 (conf.get('install_dir'),
                  conf.get('base_dir')))

if __name__ == '__main__':
    print 'FLE3 installation tool version %s' % (__version__)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:h')
    except getopt.GetoptError:
        usage()
        sys.exit(255)

    for (o, a) in opts:
        if o in ('-h',):
            usage() ; sys.exit(0)
        if o in ('-i',):
            conf['install_dir'] = a #os.path.join(a, 'FLE')
    if not conf.has_key('install_dir'):
        usage('No installation directory defined') ; sys.exit(255)

    # Checking
    if not os.path.isdir(conf['install_dir']):
        usage('%s not a valid installation directory' % (conf['install_dir']))
        sys.exit(255)

    conf['install_dir'] = os.path.join(conf['install_dir'], 'FLE')

    conf['install_dir'] = os.path.abspath(conf.get('install_dir'))
    conf['base_dir'] = os.getcwd()
    do_install(conf)

# EOF
