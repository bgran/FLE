# $Id: Translation.py,v 1.30 2003/06/13 07:57:11 jmp Exp $
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

"""Contains class Translation, which is inherited into FLE and contains functionality for string translation to local languages."""

from types import UnicodeType
import encodings.iso8859_1
from common import perm_view, perm_edit, perm_manage, perm_add_lo, \
     roles_admin, roles_staff, roles_user
import AccessControl

class Translation:
    """Contains functionality for loading translation tables and
    adding translations to http responses.

    Should be inherited to the object that needs translation capabilities
    (in FLE this is the root object, FLE)."""

    security = AccessControl.ClassSecurityInfo()

    def __init__(self):
        """Initialize and reload translation tables."""
        import vocabulary, vocabulary_fi
        self.reload_translations()

    # This is just for load speed testing.
    security.declareProtected(perm_manage, 'speed_test')
    def speed_test(self,REQUEST):
        """Speed testing."""
        import time
        start=time.time()
        for i in range(5000):
            self.get_lang(REQUEST)
        stop=time.time()
        return "TIME ELAPSED: "+str(stop-start)

    security.declarePrivate('get_lang')
    # Parameters:
    #
    # - modules: a list of language modules that should be loaded
    # (by default the 'common' module)
    #
    # - REQUEST: the http request object that should receive the translations
    #
    # This method extracts the authenticated user name from the REQUEST
    # object and tries to locate that user's preferred language setting.
    # If this fails, the default language of 'en' will be used.
    #
    # The translations for the found language and requested modules
    # are then stored into the REQUEST object as key/value pairs.
    # Each keyword is prefixed by 'L_'.
    #
    # Accessing a loaded translation from DTML:
    #
    # &lt;dtml-var L_keyword&gt;
    #
    # Accessing a loaded translation from Python:
    #
    # REQUEST['L_keyword']
    def get_lang(
        self,
        modules=('common',),
        REQUEST=None):
        """Locates the language dictionary for the user and stores
        it in the REQUEST."""
        try:
            lang = self.fle_users.get_user_info(
                str(REQUEST.AUTHENTICATED_USER)).get_language()
        except:
            lang='en'
        if not lang in self.langs.keys():
            lang='en'

        for module in modules:
            for (word,trans) in self.langs[lang][module].items():
                #REQUEST['L_'+word]='['+tuple[0]+']'
                REQUEST['L_'+word]=trans

    def __encode_to_html_entity(self,word):
        if type(word)!=UnicodeType:
            return word
        res = ''
        for ch in word:
            if ord(ch)>127:
                res+="&#"+str(ord(ch))+";"
            else:
                res+=ch
        return res

    def __encode_to_utf8(self,word,orig_encoding=None):
        if type(word)==UnicodeType:
            return word.encode('utf-8')
        if orig_encoding:
            # Encoding is specified, so use that.
            if orig_encoding=='utf-8':
                # If it's in utf-8, just return the original string
                return word
            else:
                return unicode(word,orig_encoding).encode('utf-8')
        else:
            # Unknown encoding; we'll try utf-8 and if that doesn't work
            # we then assume we're given iso-8859-1.
            # If that fails, we're in trouble.
            try:
                word_u = unicode(word,'utf-8')
                # word_u is not needed; if the unicode transformation
                # works, we probably have a utf-8 string, so we just
                # return the original string.
                return word
            except UnicodeError:
                return unicode(word,'iso-8859-1').encode('utf-8')

##     def test_encode_speed(self,word):
##         "foo"
##         import time
##         start=time.time()
##         for i in range(1000):
##             result = self.__encode_to_utf8(word)
##         end=time.time()
##         return "Time elapsed for 1000 encodings: "+ str(end-start)

##     def __encode_to_utf8_test(self,word):
##         if type(word)==UnicodeType:
##             return (word.encode('utf-8'), "unicode")
##         # Check that this is utf-8 and not something else
##         try:
##             word_u = unicode(word,'utf-8')
##             return (word, "utf-8 or ascii")
##         except UnicodeError:
##             word_u = unicode(word,'iso-8859-1')
##             return (word_u.encode('utf-8'), "iso-8859-1")

##     def encode_check(self,word='foo'):
##         """For checking the utf-8/iso-8859-1 -> utf-8 converter."""
##         (new_word,type)=self.__encode_to_utf8_test(word)
##         self.form2utf8(self.REQUEST)
##         return '<html><head>'+\
##                '<META http-equiv="Content-Type" content="text/html; charset=utf-8">'+\
##                '</head><body>'+\
##                "Original stream was: "+type +"<br>"+\
##                "Original input was: "+repr(word)+"<br>"+\
##                "Translated into utf-8, the word is: "+repr(new_word)+"<hr>"+new_word+"<hr><p>"+\
##                '<form method="get" action="encode_check" accept-charset="utf-8"><input name="word"><input type="submit"></form>'+\
##                str(self.REQUEST)+\
##                '</body></html>'

##     # This method is used to convert the form entries of a REQUEST
##     # into utf-8. This is mainly needed because of Netscape 4.xx,
##     # which doesn't send utf-8 even though it's ordered to do so.
##     def form2utf8(self,REQUEST):
##         for (key,value) in REQUEST.form.items():
##             REQUEST.form[key]=self.__encode_to_utf8(value)


    security.declarePrivate('get_lang_given')
    # Identical to get_lang() except language is given as a parameter.
    def get_lang_given(
        self,
        modules=('common',),
        REQUEST=None,
        language=None,
        ):
        """Store language dictionary in the REQUEST."""

        # Yes, this is stupid but I am trying to make argument
        # list very similar get_lang().
        if REQUEST is None or language is None:
            raise 'FLE Error', \
                  'get_given_lang() called with invalid parameters.'

        for module in modules:
            for (word,trans) in self.langs[language][module].items():
                REQUEST['L_'+word] = trans

    security.declareProtected(perm_manage, 'reload_translations')
    # All vocabulary*.py files are loaded from the FLE installation
    # directory. Each python file should contain a dictionary named
    # "vocabulary", which in turn contains module dictionaries which
    # in turn contain pairs of translations/descriptions by keyword.
    # See examples in vocabulary.py and vocabulary_fi.py.
    def reload_translations(self, REQUEST=None):
        """Reloads the translation files."""
        from common import file_path
        import os, sys
        sys.path.insert(0,file_path)
        new_langs={}
        for file in os.listdir(file_path):
            if file.find('vocabulary')==0 and \
               file.rfind('.py')==len(file)-3:
                voc_module = __import__(file[:-3])
                # If the language is marked as broken, we ignore it.
                try:
                    if voc_module.is_broken:
                        continue
                except AttributeError:
                    pass
                reload(voc_module)
                kw_count=0
                kwt_count=0
                if len(file)>14:
                    lang_name=file[11:-3]
                else:
                    lang_name='en'

                try:
                    orig_encoding= \
                                   voc_module.vocabulary['common'] \
                                   ['charset_encoding'][0]
                except KeyError:
                    orig_encoding=None

                new_langs[lang_name]={}
                for (modname,module) in voc_module.vocabulary.items():
                    new_langs[lang_name][modname]={}
                    for (keyword,trans) in module.items():
                        kw_count+=1
                        new_langs[lang_name][modname][keyword]=self.__encode_to_utf8(trans[0],orig_encoding)
                        if new_langs[lang_name][modname][keyword][:2]!='##':
                            kwt_count+=1
                ratio=kwt_count*100/kw_count
                if ratio<100:
                    new_langs[lang_name]['common']['language_name']+=" ("+str(ratio)+"%)"

        self.langs=new_langs
        try:
            if REQUEST:
                return self.message_dialog(
                    self, REQUEST,
                    title='Translations reloaded',
                    message='Translation files have been reloaded.',
                    action='index_html')
        except:
            return "Translations reloaded"

    security.declarePrivate('get_languages')
    def get_languages(self):
        """Return a list of available languages, showing english
        first."""
        lang_list=[]
        for (name,dict) in self.langs.items():
            if name!='en':
                lang_list.append((name,name+': '+dict['common']['language_name'],))
        lang_list.sort()
        lang_list.insert(
            0,
            ('en','en: '+self.langs['en']['common']['language_name'],))
        return lang_list

