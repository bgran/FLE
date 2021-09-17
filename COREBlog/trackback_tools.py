##############################################################################
#
# trackback_tools.py
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

#import python modules
import string,os,urllib,httplib,urlparse,re
import sys

default_title = ""
default_url = ""
blog_name = ""
agent_name = "COREBlog"

def discover_trackback(url):
    """
    To generate trackback:ping url from given url
    """

    o = urllib.urlopen(url)
    src = o.read()
    #Regex pattern
    rdfpat = re.compile("<rdf:RDF.*?</rdf:RDF>",re.DOTALL)
    #Pattern for Trackback PING URL
    tppat = re.compile("""trackback:ping="([^"]+)""",re.DOTALL)
    trackback_ping_url = ""
    #Finc Trackback PING URL
    for item in rdfpat.findall(src):
        m = tppat.search(item)
        if m:
            trackback_ping_url =  m.group(1)
            break

    return trackback_ping_url

def post_trackback(ping_url, \
                   title=default_title, \
                   src_url=default_url, \
                   blog_name=blog_name,
                   excerpt=""):
    """
    Try to send PING request to ping_url
    """
    try:
        #To make dictionary for POST
        params = {"title":    title,\
                  "url":      src_url,\
                  "blog_name":blog_name \
                  }
        headers = ({"Content-type": "application/x-www-form-urlencoded",
                    "User-Agent": agent_name})

        if len(excerpt) > 0:
            params["excerpt"] = excerpt

        tb_url_t = urlparse.urlparse(ping_url)

        enc_params = urllib.urlencode(params)

        #check if trackback url contains parameter section(for PyDs!)
        ut = urlparse.urlparse(ping_url)
        if len(ut) >= 4 and ut[4]:
            #add params to parameter section
            enc_params = ut[4] + '&' + enc_params

        host = tb_url_t[1]
        path = tb_url_t[2]
        con = httplib.HTTPConnection(host)
        con.request("POST", path, enc_params, headers)
        r = con.getresponse()
        http_response = r.status
        http_reason = r.reason
        resp = r.read()

        err_code_pat = re.compile("<error>(.*?)</error>",re.DOTALL)
        message_pat = re.compile("<message>(.*?)</message>",re.DOTALL)
        error_code = 0
        message = ""
        err_m = err_code_pat.search(resp)
        if err_m:
            try:
                error_code = int(err_m.group(1))
            except:
                pass
        mes_m = message_pat.search(resp)
        if mes_m:
            try:
                message = mes_m.group(1)
            except:
                pass
    except Exception,e:
        error_code = -1
        message = str(e)
    return error_code,message

#Test codes...
if __name__ == "__main__":

    tp = discover_trackback("http://some.blog.url/")
    print tp

    error_code,message = post_trackback(tp)
    print error_code,":",message
    
