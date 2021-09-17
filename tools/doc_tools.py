# reload_docs() (external method)
#
# Install note:
#
# Copy this file to Zope/Extensions directory.
#

import os

FLE_PATH = '/usr/local/zope/Zope-2.3.1-src/lib/python/Products/FLE/'

def reload_docs(self):

    # DON'T CALL!
    # call document creation script
    # os.system(FLE_PATH + 'create_docs.py')

    # grab documentation files
    html_files = os.listdir(FLE_PATH + 'doc')

    # filter some files
    try:
        html_files.remove('__init__.py.html')
    except:
        pass

    # install files to Zope
    for html_file in html_files:

        f = open(FLE_PATH + 'doc/' + html_file, 'r')

        # delete existing object
        try:
            self.manage_delObjects([html_file])
        except:
            pass

        # create a new object
        self.manage_addFile(html_file, file=f.read(), content_type='text/html')

        f.close()

    return '<a href="index.html">Fresh FLE3 documentation..</a>'
