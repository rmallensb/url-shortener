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

class LinkPage(BaseHandler):
    #TODO: Also show shy links for current_user
    def get(self):
        if not verify_user(self.response):
            return

        links = Link.query_links(active=True)
        
        self.response.headers['Content-Type'] = 'application/json'
        for link in links:
            self.response.out.write("{}\n".format(
                json.dumps(ndb_as_json(link), indent=2)))
        self.response.set_status(200)

    def post(self):
        if not verify_user(self.response):
            return
        
        required = ['url_tag', 'destination_url']
        for key in required:
            if key not in self.request.POST:
                print(self.request.POST.items())
                self.response.out.write('Missing required value: {}\n'.format(key))
                self.response.set_status(400)
                return
        
        # Needs to be a better way
        url_tag='STUB'
        for key, val in self.request.POST.items():
            if key == 'url_tag':
                url_tag = val
                break

        # Verify that url_tag isn't already active
        if Link.query_links(url_tag=url_tag, active=True):
            self.response.out.write("Already exists.\n")
            self.response.set_status(403)
            return

        # Have already verified the required fields were entered, so stubs will be replaced
        # Not entering now due to extra scrubbing necessary
        link = Link(url_tag=url_tag,
                    destination_url='STUB',
                    owner=users.get_current_user().email(),
                    #owner='ryan.allen',
                    active=True,
                    shy=False)

        allowed = ['owner', 'active', 'shy']
        for key, val in self.request.POST.items():
            if key not in allowed and key not in required:
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
