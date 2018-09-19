import cgi
import textwrap
import urllib
import json
import datetime

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import datastore_errors

from distutils.util import strtobool

import webapp2

from utility import *

class ItemPage(BaseHandler):
    def get(self, owner, url_tag):
        if not verify_user(self.response):
            return

        links = Link.query_links(url_tag=url_tag, owner=owner)

        # If owner/url_tag pair doesn't exist, error
        if not links:
            self.response.set_status(404)
            return
        
        self.response.headers['Content-Type'] = 'application/json'
        for link in links:
            self.response.out.write("{}\n".format(
                json.dumps(ndb_as_json(link), indent=2)))
        self.response.set_status(200)

    '''
    def put(self, owner, url_tag):
        if not verify_user(self.response):
            return
        link = Link.query_links(url_tag=url_tag, owner=owner)

        allowed = ['url_tag', 'destination_url', 'owner', 'shy']
        for key, val in self.request.POST.items():
            if key not in allowed:
                self.response.out.write('Not allowed to be set: {}\n'.format(key))
                self.response.set_status(400)
                return
            if isinstance(getattr(Link, key), ndb.StringProperty):
                # Want strings, not unicode
                val = val.encode('ascii')
            if isinstance(getattr(Link, key), ndb.BooleanProperty):
                # Accept 1/0, y/n, true/false as bools
                val = bool(strtobool(val.lower()))
                    
            setattr(link, key, val)

        link.put()
        self.response.set_status(201)
        self.response.out.write('Successfully updated: {}\n'.format(link))
    '''            

    def delete(self, owner, url_tag):
        if not verify_user(self.response):
            return

        links = Link.query_links(url_tag=url_tag, owner=owner)
        if not links:
            return

        # Verify current_user is owner
        if owner != users.get_current_user().email():
            self.response.set_status(403)
            return
        
        for link in links:
            setattr(link, 'active', False)
            link.put()
        self.response.set_status(200)
