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

class MainPage(BaseHandler):
    def get(self):
        if not verify_user(self.response):
            return
        self.response.out.write('<html><body>')
        links = Link.query_links()

        link_blockquotes = []
        for link in links:
            link_blockquotes.append(
                    '<blockquote>{} => {} ({})</blockquote>'.format(link.url_tag, link.destination_url, link.active))

        self.response.out.write(textwrap.dedent("""\
            <html>
              <body>
                <form action="/links?" method="post">
                  <input name="url_tag" placeholder="URL Tag">
                  =>
                  <input name="destination_url" size="80" placeholder="Destination URL">
                  <input type="submit" value="Reserve Tag">
                </form>
                <hr>
                <form action="/test?" method="post">
                  Test Button:
                    <input type="submit" value="test">
                </form>
                <form action="/delete?" method="post">
                  <input type="submit" value="Delete All">
                </form>
                <hr>
                {blockquotes}
              </body>
            </html>""").format(
                blockquotes='\n'.join(link_blockquotes)))
        self.response.set_status(200)
