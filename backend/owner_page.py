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

class OwnerPage(BaseHandler):
    def get(self, owner):
        if not verify_user(self.response):
            return

        shy = False
        if owner == users.get_current_user().email():
            #If the user is the owner, show shy keys as well
            shy = True
        owner_links = Link.query_links(owner=owner, shy=shy)

        self.response.headers['Content-Type'] = 'application/json'
        for link in owner_links:
            self.response.out.write("{}\n".format(
                json.dumps(ndb_as_json(link), indent=2)))
        self.response.set_status(200)
