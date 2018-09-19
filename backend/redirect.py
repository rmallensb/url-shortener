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

class Redirect(BaseHandler):
    def get(self, url_tag):
        if not verify_user(self.response):
            return

        links = Link.query_links(url_tag=url_tag, active=True)
        
        # If url_tag isn't active, error
        if not links:
            self.response.out.write("Tag does not exist.\n")
            self.response.set_status(404)
            return

        link = links[0]
        destination_url = getattr(link, 'destination_url').encode('ascii')

        self.redirect(destination_url)
        self.response.set_status(302)
