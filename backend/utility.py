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


MIN_TAG_LENGTH = 3
MAX_TAG_LENGTH = 16

class BaseHandler(webapp2.RequestHandler):
    def handle_exception(self, exception, debug_mode):
        if isinstance(exception, datastore_errors.BadValueError):
            self.response.write('BadValueError: {}.\n'.format(exception))
            self.response.set_status(400)
        else:
            self.response.write('Unexpected Error: {}.\n'.format(exception))
            self.response.set_status(400)


def verify_user(response):
    user = users.get_current_user()
    print("inside verify_user\n")
    print(user)
    if not user: 
        login_button = ("<a href=\"{}\">sign in</a>".format(
            users.create_login_url('/')))
        response.write('Please {} to continue.\n'.format(login_button))
        response.set_status(401)
        return False
    return True

# Might want to also be > 31
def verify_ascii(s):
    return all(ord(c) < 128 for c in s)

def tag_validator(prop, value):
    if not verify_ascii(value):
        raise datastore_errors.BadValueError('{} must be ascii'.format(prop._name))
    if len(value) < MIN_TAG_LENGTH or len(value) > MAX_TAG_LENGTH:
        raise datastore_errors.BadValueError('{} must be between 3 and 16 characters'.format(prop._name))
    return

def dest_validator(prop, value):
    if len(value) < 1:
        raise datastore_errors.BadValueError('{} must be entered'.format(prop._name))
    return

def owner_validator(prop, value):
    if not verify_ascii(value):
        raise datastore_errors.BadValueError('{} must be ascii'.format(prop._name))
   return
       
def ndb_as_json(entity):
    data = entity.to_dict()
    record = {}

    for key in data.iterkeys():
        if isinstance(data[key], datetime.datetime):
            record[key] = data[key].isoformat()
            continue
        record[key] = data[key]

    return record
'''
def verify_user():
    user = users.get_current_user()
    if user:
        return
    else:
        login_button = ("<a href=\"{}\">Sign in or Register</a>.".format(
            users.create_login_url('/')))
'''

class Link(ndb.Model):
    url_tag         = ndb.StringProperty(required=True, validator=tag_validator)
    destination_url = ndb.StringProperty(required=True, validator=dest_validator)
    owner           = ndb.StringProperty(required=True, validator=owner_validator)
    active          = ndb.BooleanProperty(required=True, default=True)
    shy             = ndb.BooleanProperty(required=True, default=False)
    create_time     = ndb.DateTimeProperty(auto_now_add=True)
    modify_time     = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def query_links(self, url_tag=None, destination_url=None, owner=None, active=None, shy=False):
        query = Link.query()
        if url_tag is not None:
            query = query.filter(Link.url_tag == url_tag)
        if destination_url is not None:
            query = query.filter(Link.destination_url == destination_url)
        if owner is not None:
            query = query.filter(Link.owner == owner)
        if active is not None:
            query = query.filter(Link.active == active)
        if shy is False:
            query = query.filter(Link.shy == shy)
        return query.fetch()
