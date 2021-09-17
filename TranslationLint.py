# $Id: TranslationLint.py,v 1.8 2004/11/22 14:59:28 tarmo Exp $
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

"""Contains utility functions that can update all Fle3 vocabulary files to
match the master vocabulary file, including adding missing keywords, removing
extra keywords and moving keywords from module to module."""

from types import UnicodeType
import encodings.iso8859_1

def dict_to_txt(name, dict):
    """Convert python dictionary to text string.
       'name = {dict}'
    """

    # Character encodings: all vocabulary strings are in utf-8, so
    # if we do nothing, we'll end up with utf-8 encoded strings.
    # Great, just what we need!

    from pprint import pformat

    retval = name + ' = '

    retval += pformat(dict)

    # f = open('foo.py', 'w')
    # f.write(retval)
    # f.close()

    return retval

import os,re
def dal_load(fname,header_break="common = "):
    f=open(fname,"r")
    buff = f.read()

    buff=re.sub('{','[',buff)
    buff=re.sub('}',']',buff)
    buff=re.sub("':","',",buff)

    header=""
    for line in buff.split('\n'):
        if line.startswith(header_break):
            break
        header+=line+'\n'

#    lines = os.popen("cat %s | sed 's/{/[/g'|sed 's/}/]/g'|sed 's/: /, /g'" % fname).readlines()
    exec buff
    try:
        if is_broken:
            return (None,None)
    except NameError:
        pass
    return (vocabulary,header)

def dal_save(fname,buff,header):
    import string
    buff=re.sub('\[','{',buff)
    buff=re.sub('\]','}',buff)
    lines = buff.split('\n')
    buff=""
    for line in lines:
        # Transform into dictionary...
        if not re.search('\(',line):
            line=re.sub("',$","':",line)

        # Turn \xNN codings into actual binary characters
        enc_str=r"(\\x[a-z0-9][a-z0-9])"
        while 1:
            rs=re.search(enc_str,line)
            if not rs:
                break
            val=string.atoi(rs.group(1)[2:],16)
            line=re.sub(enc_str,chr(val),line,1)
        buff+=line+"\n"

    os.rename(fname,fname+".orig")
    f = open(fname,"w")
    f.write(header)
    f.write(buff)
    f.close()

def dal_value4key(list,key):
    ndx = list.index(key)
    return list[ndx+1]

def dal_indexof(list,key):
    return list.index(key)

def dal_items(list):
    items = []
    pair = []
    for i in list:
        pair.append(i)
        if len(pair)==2:
            items.append(pair)
            pair = []
    return items

def dal_keys(list):
    keys = []
    take=1
    for i in list:
        if take:
            keys.append(i)
        take=not take
    return keys

def dal_del(list,keyword):
    ndx = list.index(keyword)
    del list[ndx:ndx+2]

def dal_add(list,keyword,value,toindex=-1):
    if toindex>=0:
        list.insert(toindex,value)
        list.insert(toindex,keyword)
    else:
        list.append(keyword)
        list.append(value)

def update_dicts(directory):
    """Update all changes made to the master vocabulary to other
    language specific vocabularies."""
    import sys, os
    #base_voc_module = __import__('vocabulary')
    (base_voc,base_headers) = dal_load(directory+"/vocabulary.py")
    #print repr(base_voc)
    for file in os.listdir(directory):
        if file.find('vocabulary_')==0 and \
           file.rfind('.py')==len(file)-3:
            print
            print "Processing language "+file[11:-3]+"..."
            #voc_module = __import__(file[:-3])
            (voc,headers)=dal_load(directory+"/"+file)
            if not voc:
                continue
            lang_name=file[11:-3]

            try:
                common = dal_value4key(voc,'common')
                orig_encoding= dal_value4key(common,'charset_encoding')[0]
            except ValueError:
                orig_encoding=None

            master=base_voc
            slave=voc

            # Remove old 'removed' keywords
            if 'removed' in slave:
                dal_del(slave,'removed')
            slave.append('removed')
            slave.append([])

            for (modname,module) in dal_items(master):
                for (keyword,trans) in dal_items(module):
                    try:
                        smod = dal_value4key(slave,modname)
                    except ValueError: # Module doesn't exist
                        slave.append(modname)
                        slave.append([])
                        smod = dal_value4key(slave,modname)
                    if not keyword in dal_keys(smod):
                        print "Keyword %s not found!" % keyword
                        for (mname,mdule) in dal_items(slave):
                            if keyword in dal_keys(mdule):
                                # Keyword found in different module, so
                                # check that is really isn't necessary
                                mmod = dal_value4key(master,mname)
                                if not keyword in dal_keys(mmod):
                                    # Keyword not in the master vocabulary,
                                    # so we can move it
                                    dal_add(smod,keyword,dal_value4key(mdule,keyword),dal_indexof(module,keyword))
                                    dal_del(mdule,keyword)
                                    print "Moved keyword %s from module %s to %s" % \
                                          (keyword,mname,modname)
                                    break
                        else:
                            dal_add(smod,keyword,("##"+trans[0],trans[1]),dal_indexof(module,keyword))
                            print "Added missing keyword %s to module %s" % \
                                  (keyword,modname)

            for (mname,mdule) in dal_items(slave):
                if mname=='removed':
                    pass
                else:
                    for (keyword,trans) in dal_items(mdule):
                        mmod = dal_value4key(master,mname)
                        if not keyword in dal_keys(mmod):
                            removed = dal_value4key(slave,'removed')
                            dal_add(removed,keyword,trans)
                            dal_del(mdule,keyword)
                            print "Removed extra keyword %s from module %s" % \
                                  (keyword,mname)

            removed = dal_value4key(slave,'removed')
            if len(removed)==0:
                dal_del(slave,'removed')

            #os.rename(directory+"/"+file,directory+"/"+file+".orig")

            stamp = "# Fle3 vocabulary file, generated by TranslationLint\n"
            if not re.search(stamp,headers):
                headers = stamp + headers
            buff=""
            for (mname,mdule) in dal_items(slave):
                buff+=dict_to_txt(mname,mdule)
                buff+="\n\n"
            buff+="vocabulary={\n"
            for (mname,mdule) in dal_items(slave):
                buff+="        '%s': %s,\n" % (mname,mname)
            buff+="}\n\n#EOF\n"

            dal_save(directory+"/"+file,buff,headers)


if __name__=='__main__':
    update_dicts('.')
