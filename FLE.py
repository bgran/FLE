# $Id: FLE.py,v 1.197 2005/02/22 11:57:26 tarmo Exp $
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

"""This is the main module for FLE, containing the FLE class and the Zope
factory method for creating a FLE installation inside Zope."""

__version__ = "$Revision: 1.197 $"[11:-2]
FLE_VERSION = "1.5.0"

import os.path, string, time

try:
    from PIL import Image
    PIL_imported = 1
except ImportError:
    PIL_imported = 0

import Globals
from Globals import Persistent, Acquisition, HTMLFile
import AccessControl
import OFS
from OFS.Application import Application
from OFS.Folder import Folder
from Products.ZCatalog.ZCatalog import ZCatalog

from TraversableWrapper import TraversableWrapper as TW
from Cruft import Cruft

from ThinkingTypeSetManager import ThinkingTypeSetManager as TTSM
from UserManager import UserManager
from CourseManager import CourseManager
from Timer import Timer
from State import State
from common import file_path, ui_path
from Translation import Translation
import Acquisition

from common import add_dtml_obj, new_add_dtml_obj, add_image_obj, \
     reload_dtml, add_dtml
from common import perm_view, perm_edit, perm_manage, perm_add_lo, \
     roles_admin, roles_staff, roles_user
import common

# This is the class for the FLE installation root object.
class FLE(
    Folder,
    TW,
    Cruft,
    Persistent,
    AccessControl.Role.RoleManager,
    OFS.SimpleItem.Item,
    Timer,
    State,
    Translation,
    ):
    """FLE product."""
    security = AccessControl.ClassSecurityInfo()
    security.declareObjectPublic()

    meta_type = 'FLE'

    management_tab = Globals.DTMLFile('ui/FLE/management_tab', globals())
    manage_options=((
        {'label' : 'Tools', 'action' : 'management_tab'},
        ) + OFS.Folder.Folder.manage_options)

    #index_html = Globals.HTMLFile("index_html", globals())
    dtml_files = (
        ('message_dialog', 'Message dialog', 'ui/FLE/message_dialog'),
        ('message_dialog2', 'Message dialog 2', 'ui/FLE/message_dialog2'),
        ('message_dialog_error', 'Error message dialog',
         'ui/FLE/message_dialog_error'),
        ('standard_error_message','Error page',
         'ui/FLE/standard_error_message'),
        ('super_header', '', 'ui/FLE/super_header'),

        ('index_html', 'Index HTML', 'ui/FLE/index_html'),
        ('hdr', 'HTML header',
         'ui/FLE/hdr'),

        ('course_attendees', '', 'ui/CourseManager/course_attendees'),

        ('hdr_form_cm', 'HTML header for forms (CM)',
         'ui/FLE/hdr_form_cm'),
        ('hdr_form_kb', 'HTML header for forms (KB)',
         'ui/FLE/hdr_form_kb'),
        ('hdr_form_um', 'HTML header for forms (UM)',
         'ui/FLE/hdr_form_um'),
        ('hdr_form_wt', 'HTML header for forms (WT)',
         'ui/FLE/hdr_form_wt'),
        ('hdr_form_jm', 'HTML header for forms (JM)',
         'ui/FLE/hdr_form_jm'),
        ('hdr_form_common', 'HTML header for forms (common)',
         'ui/FLE/hdr_form_common'),
        ('fle_header', 'Common FLE header, use with fle_footer',
         'ui/FLE/fle_header'),
        ('fle_footer', 'Common FLE footer, use with fle_header',
         'ui/FLE/fle_footer'),
        ('fle_form_footer', 'Standard FLE Html Footer for forms',
                     'ui/FLE/fle_form_footer'),

        ('fle_html_footer', 'Standard FLE Html Footer',
                     'ui/FLE/fle_html_footer'),
        ('navigation', 'Navigation toolbar', 'ui/FLE/navigation'),
        ('undefined_page', 'Undefined page',
         'ui/FLE/undefined_page'),
        ('todos_form', 'TODO', 'ui/FLE/todos_form'),
        )

    def __bobo_traverse__(self,REQUEST,entry_name=None):
        # Return the actual object if it exists
        try: return getattr(self, entry_name)
        except AttributeError: pass
        try: return self[entry_name]
        except KeyError: pass

        # If not, do some magic!
        course_cnames = {}
        for x in self.courses.get_courses():
            course_cnames[x.get_clean_name()]=x.get_id()
        if entry_name in course_cnames.keys():
            if hasattr(getattr(self.courses,course_cnames[entry_name]),"announcements"):
                REQUEST.RESPONSE.redirect(self.absolute_url() +"/courses/%s/announcements/" % course_cnames[entry_name])
                return getattr(self.courses,course_cnames[entry_name]).announcements

        method=REQUEST.get('REQUEST_METHOD', 'GET')
        if not method in ('GET', 'POST'):
            return NullResource(self, entry_name, REQUEST).__of__(self)
        try: REQUEST.RESPONSE.notFoundError("%s\n%s" % (entry_name, method))
        except AttributeError:
            raise KeyError, name

    # Parameters are received from the creation form at
    # ui/FLE/creation_form.dtml
    def __init__(
        self, _id, title,
        fle_admin, fle_admin_pwd, fle_admin_pwd2,
        fle_admin_first_name, fle_admin_last_name,
        acl_users_mode, smtp_host, smtp_port=25, import_data=None):
        """Construct FLE object."""

        from string import atoi

        self.setup_timer()

        errors = []
        if not _id:
            errors.append('ID not specified')
        if not title:
            errors.append('Title not specified')
        if not fle_admin:
            errors.append('Administrator user name not specified')
        if acl_users_mode=='create':
            if not fle_admin_pwd:
                errors.append('Administrator password not specified')
            if fle_admin_pwd != fle_admin_pwd2:
                errors.append('Administrator password and confirmation were not identical.')
        if errors:
            raise 'Insufficient form data',str(errors)

        self.id = _id
        self.title = title

        self.__fle_root = ''

        self.reload_translations()

        # The values are saved so that they can be used in
        # manage_afterAdd (where they are also deleted...)
        tmptbl = {}
        tmptbl['initial_fle_admin'] = fle_admin
        tmptbl['initial_fle_admin_pwd'] = fle_admin_pwd
        tmptbl['initial_fle_admin_first_name'] = fle_admin_first_name
        tmptbl['initial_fle_admin_last_name'] = fle_admin_last_name
        tmptbl['acl_users_mode'] = (acl_users_mode=='create')
        # Check that the fileupload exists and has a filename
        if import_data and import_data.filename:
            tmptbl['import_data'] = import_data
        else:
            tmptbl['import_data'] = None
            # If not, set it to none, so we only need to check one
            # thing if we need to decide whether we have a file or not.
            import_data = None

        self.tmptbl = tmptbl

        if len(smtp_host)>0 and smtp_port:
            from Products.MailHost import MailHost
            mailhost = MailHost.MailHost()
            mailhost._init(smtp_host, atoi(smtp_port))
            self._setObject('MailHost', mailhost)

        # Style sheets
        self.reload_style_sheets()

        # Set the zope manageable dtml objects of this class.
        self.reload_dtml()

        ###
        #self.new_reload_all_dtml()
        #self.reload_all_dtml()

        # Add images to images/
        self.manage_addFolder('images', '')
        from common import image_file_path
        self.add_images(self.images, image_file_path)

        # ZCatalog for webtop items
        catalog = ZCatalog('catalog_webtop_items', 'ZCatalog for webtop items')

        # indexes
        catalog.addIndex('get_name', 'TextIndex')
        catalog.addIndex('get_content', 'TextIndex')
        catalog.addIndex('get_author_name', 'FieldIndex')

        # metadata
        catalog.addColumn('get_name')
        catalog.addColumn('get_author_name')
        catalog.addColumn('absolute_url')
        catalog.addColumn('get_view_url')
        catalog.addColumn('get_context_url')
        catalog.addColumn('get_icon_path')

        self._setObject('catalog_webtop_items', catalog)

    security.declarePrivate('manage_afterAdd')
    # Executes a full FLE import if the export data was
    # passed to the constructor (ie. uploaded via the creation
    # form.
    def manage_afterAdd(self, item, container):
        """Add roles to the root level Fle folder and do other
        initialization tasks."""

        if hasattr(self,'typesets'):
            # If the typesets directory already exists, then this
            # isn't the initial installation, but rather a rename
            # or a move operation.
            # Skip everything!
            return

        t = self.tmptbl

        # Property telling whether or not we're using an external
        # user folder.
        # Ramifications:
        # - new users are allowed to login
        # - the user folder is read-only
        self.manage_addProperty('allow_external_users', not t['acl_users_mode'], 'boolean')
        # add properties for todos
        self.manage_addProperty('todo_mode', 0, 'boolean')
        self.manage_addProperty('todo_server', '', 'string')
        self.manage_addProperty('todo_login', '', 'string')
        self.manage_addProperty('todo_password', '', 'string')
        # add property for developer controls
        self.manage_addProperty('show_developer_controls', 0, 'boolean')
        # add properties for Webtop quotas
        self.manage_addProperty('webtop_quota', 0, 'boolean')
        self.manage_addProperty('webtop_quota_amount', 1048576, 'string')
        # add property for FLE version number
        self.manage_addProperty('FLE_VERSION', FLE_VERSION, 'string')
        # add property for maptool
        self.manage_addProperty('use_maptool', 0, 'boolean')

        tts_manager = TTSM('typesets', '')
        self._setObject('typesets', tts_manager)
        tts_manager=tts_manager.__of__(self)

        from Downloader import Downloader
        dloader=Downloader()
        dloader.id='download'
        self._setObject('download',dloader)

        from common import fle_roles

        for role in fle_roles:
            self._addRole(role)

        self.manage_permission(perm_manage, roles_admin, 1)
        self.manage_permission(perm_edit, roles_admin, 1)
        self.manage_permission(perm_add_lo, roles_admin, 1)
        self.manage_permission(perm_view, roles_user+('Authenticated',), 1)

        if not self.allow_external_users:
            # Create our own acl_users if requested.
            self.manage_addUserFolder()
        else:
            # Check that the supplied user name actually exists
            try:
                self.acl_users.getUser(t['initial_fle_admin'])
            except:
                return self.message_dialog_error(
                    self, REQUEST,
                    title='Administrator not found',
                    message='The user account %s that was supplied as the initial administrator could not be found.' % t['initial_fle_admin'],
                    action="index_html")


        um_obj = UserManager('fle_users',
                             #'FLE User Manager')
                             '')
        self._setObject('fle_users',
                        um_obj)

        import_data = t['import_data']

        # Create default knowledge type sets, whether importing
        # or not.
        tts_manager.load_default_sets()

        if self.allow_external_users:
            # Just create the FLE specific user information
            try:
                uo = self.fle_users.add_user_fle(
                    t['initial_fle_admin'], ('FLEAdmin','User'))
            except AttributeError:
                raise 'FLE Error','Problem accessing the initial Fle3 administrator account! Make sure that account "%s" exists!' % t['initial_fle_admin']
        else:
            # Create both FLE and Zope user information
            uo = self.fle_users.add_user(
                t['initial_fle_admin'], t['initial_fle_admin_pwd'],
                ('FLEAdmin','User'))
            # Add global Manager rights to the FLE administrator
            self.acl_users.getUser(t['initial_fle_admin']).roles=('Manager','FLEAdmin')

        #uo.set_password(t['initial_fle_admin_pwd'])
        uo.set_first_name(t['initial_fle_admin_first_name'])
        uo.set_last_name(t['initial_fle_admin_last_name'])
        uo.set_language('en')

        # Let's do courses last, since if we're importing, we
        # need to have the users already in place.
        cm_obj = CourseManager('courses')
        self._setObject('courses', cm_obj)

        # We don't need these any more.
        del self.tmptbl

        # Make index_html public
        getattr(self,'index_html').manage_permission(
            perm_view,
            ['Authenticated', 'Anonymous',], 1)

        getattr(self, 'images').manage_permission(
            'View', ['Authenticated', 'Anonymous',], 1)

        if import_data:
            import time
            ss_time=time.time()
            s_time=time.time()
            try:
                from ImportExport import Exporter
                import tempfile, os
                # Write data to a temporary file...
                filename = tempfile.mktemp()
                file = open(filename,"w+b")
                file.write(import_data.read())
                file.close()
            except ImportError:
                return self.message_dialog_error(
                    self, REQUEST,
                    title='Import failed',
                    message='Import function is unavailable, because the Python xml library containing package "xml.dom.minidom" is not installed. Please install the PyXML library and retry.',
                    action="index_html")

            import_data=None

            # ...and load it into the Exporter
            try:
                exported = Exporter("FLE",filename)
            except:
                # This handles older export versions...
                exported = Exporter("Interactions",filename)

            os.remove(filename)

            print "IMPORT PHASE 0: %s" % str(time.time()-s_time)
            s_time=time.time()
            exported.importData(
                'GlobalKnowledgeTypes',
                exported.importGlobalTypes,
                self)
            get_transaction().commit()
            print "IMPORT PHASE 1: %s" % str(time.time()-s_time)
            s_time=time.time()
            exported.importData(
                'Users',
                exported.importUsers,
                self)
            get_transaction().commit()
            print "IMPORT PHASE 2: %s" % str(time.time()-s_time)
            s_time=time.time()
            exported.importData(
                'KnowledgeBuilding',
                exported.importKB,
                self)
            get_transaction().commit()
            print "IMPORT PHASE 3: %s" % str(time.time()-s_time)
            s_time=time.time()
            exported.importData(
                'Jamming',
                exported.importJamming,
                self)
            get_transaction().commit()
            print "IMPORT PHASE 4: %s" % str(time.time()-s_time)
            s_time=time.time()
            exported.importData(
                'Users',
                exported.importUsersWebtops,
                self)
            get_transaction().commit()
            e_time=time.time()
            print "IMPORT PHASE 5: %s" % str(e_time-s_time)
            print "IMPORT TOTAL: %s" % str(e_time-ss_time)
            print "IMPORT TIME COUNTERS: %s" % str(exported.timecounters)
            self.fle_users.cleanup_webtops()


    security.declareProtected(perm_manage, 'reload_dtml')
    def reload_dtml(self, REQUEST=None):
        """Reloads dtml stuff."""
        reload_dtml(self, self.dtml_files)

        # Temporary hack, remove when permission with dtml files
        # are fixed. --jmp 2001-10-13
        getattr(self,'index_html').manage_permission(
            'View',
            ['Authenticated', 'Anonymous',], 1)

        # Makes user registration possible.
        for name in ('fle_header', 'hdr_form_um', 'fle_form_footer', \
                     'todos_form', 'hdr_form_common', 'fle_footer'):
            getattr(self, name).manage_permission(
                'View', ['Authenticated', 'Anonymous',], 1)

        if REQUEST:
            self.get_lang(('common',),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_dtml_reloaded'],
                message=REQUEST['L_dtml_files_reloaded'],
                action='index_html')

    security.declareProtected(perm_manage, 'fle_export')
    def fle_export(self,REQUEST):
        """Do a complete export (dump) of FLE data."""
        try:
            from ImportExport import Exporter
            ex = Exporter("FLE")
            ex.exportData(self.typesets,ex.exportGlobalTypes)
            ex.exportData(self.courses,ex.exportKB)
            ex.exportData(self.courses, ex.exportJamming)
            ex.exportData(self.fle_users,ex.exportUsers)
            import tempfile, os
            filename = tempfile.mktemp()
            ex.createZip(filename)
            file = open(filename,"rb")
            export_data=file.read()
            file.close()
            os.remove(filename)
            REQUEST.RESPONSE.setHeader('content-type','application/zip')
            return export_data
        except ImportError:
            return self.message_dialog_error(
                self, REQUEST,
                title='Export failed',
                message='Export function is unavailable, because the Python xml library containing package "xml.dom.minidom" is not installed. Please install the PyXML library and retry.',
                action="index_html")

    security.declareProtected(perm_manage, 'reload_typesets')
    def reload_typesets(self,REQUEST=None):
        """Reload typesets."""
        self.typesets.load_default_sets()
        if REQUEST:
            return self.message_dialog(
                self, REQUEST,
                title='Knowledge type sets reloaded',
                message='Knowledge type sets reloaded',
                action='index_html')


    security.declareProtected(perm_manage, 'reload_images')
    def reload_images(self,REQUEST=None):
        """Reload images."""
        for e in self.images.objectIds():
            self.images.manage_delObjects(e)

        from common import image_file_path
        self.add_images(self.images, image_file_path)

        if REQUEST:
            return self.message_dialog(
                self, REQUEST,
                title='Images reloaded',
                message='Images reloaded',
                action='index_html')

    security.declarePrivate('add_images')
    # fs_path is CVS path
    def add_images(self, zope_path, fs_path):
        """Add images recursively."""
        for e in os.listdir(fs_path):
            full_path = os.path.join(fs_path, e)

            if os.path.isdir(full_path):
                if e == 'CVS': continue
                zope_path.manage_addFolder(e, '')
                self.add_images(getattr(zope_path, e), full_path)
            else:
                # title (3rd parameter) will be used as an alt parameter
                # inside HTML <img> tag. (Override in DTML code when you
                # want some alt text (i.e. almost always...))

                # This can be like this for now .... -granbo
                import re
                m = re.match("^(.*)\.", e)

                add_image_obj(zope_path, m.group(1), '', full_path)

    security.declarePrivate('add_style_sheets')
    def add_style_sheets(self, fs_path):
        """Add style sheets."""

        for e in os.listdir(fs_path):             # fetch all style sheets
            if e[-4:] != 'dtml':
                continue
            if e == 'personal_style_sheet.dtml':  # This goes under UserInfo
                continue                          # object (see UserInfo.py).
            full_path = os.path.join(fs_path, e)
            if os.path.isdir(full_path):
                continue                          # skip the CVS directory
            # get the  code
            f = open(full_path)
            code = f.read()
            f.close()

            self.styles.manage_addFile(
                id=e[:-5],
                file=code,
                title=e,
                content_type='text/css')

            # Everybody can access style sheets.
            getattr(self.styles, e[:-5]).manage_permission(
                'View', ['Authenticated', 'Anonymous',], 1)

    security.declareProtected(perm_manage, 'reload_style_sheets')
    def reload_style_sheets(self, REQUEST=None):
        """Reload style sheets."""
        from common import styles_path

        try:
            for e in self.styles.objectIds():
                self.styles.manage_delObjects(e)
            self.manage_delObjects('styles')
        except:
            pass

        self.manage_addFolder('styles', '')
        self.add_style_sheets(styles_path)

        if REQUEST:
            self.get_lang(('common',),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_css_reloaded'],
                message=REQUEST['L_css_files_reloaded'],
                action='index_html')

    security.declareProtected(perm_manage, 'reload_all')
    def reload_all(self, REQUEST=None):
        """Reload all dtml, style sheet, image, printer, and
        translation files."""
        self.reload_all_dtml()
        self.reload_style_sheets()
        self.reload_images()
        self.courses.printers.reload_printers()
        self.reload_translations()
        self.reload_typesets()

        if REQUEST:
            return self.message_dialog(
                self, REQUEST,
                title='Reload of all data successful',
                message='Reloaded all dtml, css, images, printers, translations and knowledge type sets',
                action='index_html')

    security.declareProtected(perm_manage, 'reload_all_dtml')
    def reload_all_dtml(self, REQUEST=None):
        """Reload _all_ dtml files."""
        from common import tree_reload_dtml
        tree_reload_dtml(self)

        if REQUEST:
            self.get_lang(('common',),REQUEST)
            return self.message_dialog(
                self, REQUEST,
                title=REQUEST['L_dtmls_reloaded'],
                message=REQUEST['L_dtmls_files_reloaded'],
                action='index_html')

    # FIXME: What should we do if self.webtop_quota_amount is invalid?
    security.declareProtected(perm_view, 'get_quota')
    def get_quota(self):
        """Return quota limit in bytes (-1 if no quota in use)."""
        if not self.webtop_quota:
            return -1 # no quota
        s = self.webtop_quota_amount.strip()
        if s[-1].lower() == 'k':
            return int(s[:-1]) * 1024
        elif s[-1].lower() == 'm':
            return int(s[:-1]) * 1024 * 1024
        else:
            return int(s)

    def show_controls_for_developers(self, REQUEST):
        """Return boolean depending on whether we are in debug mode
        or not!"""
        return not not self.show_developer_controls

    # This is used by message_dialog.dtml.
    def message_dialog_handler(self, action, REQUEST):
        """Redirects to the given URL, preserving the
        state information in the url."""
        REQUEST.RESPONSE.redirect(self.state_href(REQUEST, action))


    security.declareProtected(perm_view, 'get_todos')
    def get_todos(self, path, meta_type, ids):
        """XML-RPC proxy method for getting todos from server."""
        try:
            import xmlrpclib
        except:
            return 'No xmlrpclib installed.'
        old_path = path
        path = meta_type + '/' + path[path.rfind('/') + 1:]
        server = xmlrpclib.Server(self.todo_server)
        return server.todo.xmlrpc_get_todos(path,ids)

    # FIXME: input_checks
    security.declareProtected(perm_manage, 'todo_remove_form_handler')
    def todo_remove_form_handler(self, removes, remove, REQUEST = None):
        """XML-RPC proxy method for marking todos as complete."""
        try:
            import xmlrpclib
        except:
            return 'No xmlrpclib installed.'

        server_address = self.todo_server
        login = self.todo_login
        password = self.todo_password

        server = xmlrpclib.Server(server_address,
                                  login = login,
                                  password = password,
                                  transport = None)
        try:
            server = xmlrpclib.Server(server_address, login, password)
        except:
            return 'this version of xmlrpclib does not support authentication'

        if removes:
            from types import StringType
            if type(removes) == StringType:
                removes = (removes,)

        server.todo.remove_form_handler(removes)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(self.state_href(
                REQUEST, 'index_html'))

    # FIXME: input_checks
    security.declareProtected(perm_manage, 'todo_form_handler')
    def todo_form_handler(self, body, path, meta_type, REQUEST = None):
        """XML-RPC proxy method for posting todo to server."""
        try:
            import xmlrpclib
        except:
            return 'No xmlrpclib installed.'

        came_from = path

        server_address = self.todo_server
        login = self.todo_login
        password = self.todo_password

        server = xmlrpclib.Server(server_address,
                                  login = login,
                                  password = password,
                                  transport = None)
        try:
            server = xmlrpclib.Server(server_address, login, password)
        except:
            return 'this version of xmlrpclib does not support authentication'

        path = meta_type + '/' + path[path.rfind('/') + 1:]

        server.todo.form_handler(body, path)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(
                self.state_href(REQUEST, came_from))


    security.declareProtected(perm_view, 'redirect_to_webtop')
    def redirect_to_webtop(self, REQUEST):
        """Redirect to webtop."""
        uname = str(REQUEST.AUTHENTICATED_USER)
        if uname == "Anonymous User":
            REQUEST.RESPONSE.setStatus(401)
            REQUEST.RESPONSE.setHeader("WWW-Authenticate", 'basic realm="Zope"')
            return
        if hasattr(self.fle_users,uname):
            return REQUEST.RESPONSE.redirect(
                self.state_href(REQUEST, 'fle_users/' + uname + '/webtop/'))
        else:
            # The logged in user does not exist inside UserManager
            if hasattr(self,'allow_external_users') \
               and self.allow_external_users:
                self.fle_users.add_user_fle(uname, ('User',))
                return self.message_dialog(
                    self, REQUEST,
                    title='First login registration',
                    message="Welcome to Fle3, %s! This is your first visit here, so you'll need to fill in some information about yourself." % uname,
                    action="fle_users/%s/edit_user_form" % uname)
            else:
                return self.message_dialog_error(
                    self, REQUEST,
                    title='Login not allowed',
                    message="""Sorry, login not allowed. You're logged in as a user ("%s") that does not exist in this Fle3 and the administrator has disallowed the automatic registration of authenticated users. You need to logout and relogin as another user that already exists in the Fle3.""" % uname,
                    action="logout")


    # Returns whether we use our own acl_users or not.
    def private_acl_users(self):
        return hasattr(self.aq_base,'acl_users')

    # Not used yet.
    # Locates a user object from the Fle3's own acl_users or
    # by acquisition.
    def get_acl_user(self,uname):
        user = self.acl_users.getUser(uname)
        if user:
            return user
        return self.parent().acl_users.getUser(uname)

    security.declareProtected(perm_manage, 'manage_workspace')
    def manage_workspace(self,REQUEST):
        """This makes sure that ZCatalog doesn't override manage_workspace
        and make it point to index_html, when we actually want manage_main"""
        REQUEST.RESPONSE.redirect('manage_main')

    def logout(self,REQUEST):
        """This is the logout instruction page."""
        self.get_lang(('common',),REQUEST)
        return self.message_dialog2(
            self, REQUEST,
            title=REQUEST['L_logout'],
            message=REQUEST['L_logout_pre3'],
            extra_value_name = '',
            extra_values = (),
            option1_value = REQUEST['L_logout'],
            option1_name = 'logout',
            option2_value = '',
            option2_name = '',
            handler = 'clear_password')

    def clear_password(
        self,
        REQUEST=None):
        """This will clear the password cache."""
        REQUEST.RESPONSE.setStatus(401)
        REQUEST.RESPONSE.setHeader("WWW-Authenticate", 'basic realm="Zope"')
        return '<html><head><meta content="2; URL=%s" http-equiv="REFRESH"></head><body>You\'ve been logged out.</body></html>' %  self.absolute_url()
    def has_PIL(self):
        """Has the system PIL (Python Image Library) installed?"""
        return PIL_imported

Globals.InitializeClass(FLE)


# FIXME: input_checks (some checks done in FLE.__init__)
def manage_addFLE(
    self, _id, title,
    fle_manager, fle_manager_pwd, fle_manager_pwd2,
    fle_manager_first_name, fle_manager_last_name,
    acl_users_mode, smtp_host, smtp_port, import_data=None,
    REQUEST=None):
    """Create a FLE object. (Product Factory Method)."""

    fle = FLE(
        _id, title, fle_manager, fle_manager_pwd, fle_manager_pwd2,
        fle_manager_first_name, fle_manager_last_name,
        acl_users_mode, smtp_host, smtp_port, import_data)
    self._setObject(_id, fle)
    if REQUEST:
        return self.manage_main(self, REQUEST)

manage_addFLEForm = Globals.HTMLFile('ui/FLE/creation_form', globals())

# EOF
