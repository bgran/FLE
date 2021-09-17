##############################################################################
#
# AuthBridge.py
# Classes to pass Zope authentication information to XMLRPC methods
#
# Copyright (c) 2003-2004 Atsushi Shibata. All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and its 
# documentation for any purpose and without fee is hereby granted, provided that
# the above copyright notice appear in all copies and that both that copyright 
# notice and this permission notice appear in supporting documentation, and that
# the name of Atsushi Shibata not be used in advertising or publicity pertaining 
# to distribution of the software without specific, written prior permission. 
# 
# ATSUSHI SHIBAT DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, 
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO
# EVENT SHALL SHIBAT ATSUSHI BE LIABLE FOR ANY SPECIAL, INDIRECT OR 
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF
# USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE. 
#
##############################################################################

from OFS.SimpleItem import SimpleItem
import Globals

from base64 import encodestring,decodestring

_debug_mode = 1

class AuthBridge(SimpleItem):
    '''
    Bridge class to pass Zope authentication via xmlrpc
    '''
    manage_options = (SimpleItem.manage_options)

    def __before_publishing_traverse__(self, container, REQUEST):
        '''__before_publishing_traverse__ hook.'''
        #Check if TraversalRequest is in procedure map.
        if len(REQUEST['TraversalRequestNameStack']) == 1 and \
           REQUEST['TraversalRequestNameStack'][0] in self.proc_dict.keys() and \
           len(self.proc_dict[REQUEST['TraversalRequestNameStack'][0]]) >= 2:
            #then set auth informations
            proc_name = REQUEST['TraversalRequestNameStack'][0]
            username = REQUEST.args[self.proc_dict[proc_name][0]]
            password = REQUEST.args[self.proc_dict[proc_name][1]]
            if _debug_mode:
                #Log request
                try:
                    import zLOG
                    log_body = ""
                    idx = 0
                    zLOG.LOG("XML-RPC Log.", zLOG.INFO,
                              self.id + "." + REQUEST['TraversalRequestNameStack'][0],
                              detail=REQUEST.args)
                except:
                    pass
            REQUEST._auth = "basic " + encodestring('%s:%s' % (username,password))
            REQUEST.RESPONSE._auth = 1
            #remap method if need
            if len(self.proc_dict[proc_name]) >= 3:
                REQUEST['TraversalRequestNameStack'][0] = self.proc_dict[proc_name][2]

    def set_proc_map(self,proc_dict):
        self.proc_dict = proc_dict


Globals.InitializeClass(AuthBridge)

