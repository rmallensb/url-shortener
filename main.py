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


class MainPage(BaseHandler):
    def get(self):
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
                <form action="/links?" method="delete">
                  Delete Link:
                    <input name="inactive_host">
                    <input type="submit" value="delete">
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


class LinkPage(BaseHandler):
    #TODO: Also show shy links for current_user
    def get(self):
        links = Link.query_links(active=True)
        
        self.response.headers['Content-Type'] = 'application/json'
        for link in links:
            self.response.out.write("{}\n".format(
                json.dumps(ndb_as_json(link), indent=2)))
        self.response.set_status(200)

    def post(self):
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
                    #owner=users.get_current_user().email(),
                    owner='ryan.allen',
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


class RedirectPage(BaseHandler):
    def get(self, url_tag):
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

class OwnerPage(BaseHandler):
    def get(self, owner):
        shy = False
        #if owner == users.get_current_user().email():
            # If the user is the owner, show shy keys as well
        #    shy = True
        owner_links = Link.query_links(owner=owner, shy=shy)

        self.response.headers['Content-Type'] = 'application/json'
        for link in owner_links:
            self.response.out.write("{}\n".format(
                json.dumps(ndb_as_json(link), indent=2)))
        self.response.set_status(200)

class ItemPage(BaseHandler):
    def get(self, owner, url_tag):
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
        links = Link.query_links(url_tag=url_tag, owner=owner)
        
        if not links:
            return

        # Verify current_user is owner
        if owner != 'ryan.allen': #users.get_current_user().email():
            self.response.set_status(403)
            return
        
        for link in links:
            setattr(link, 'active', False)
            link.put()
        self.response.set_status(200)


class TestButton(BaseHandler):
    def post(self):
        #url_tag = self.request.get("check_if_active")

        #url = self.request.url.replace(self.request.host, 'www.google.com')
        #return self.redirect('https://www.google.com', True)

        query = Link.query_links(url_tag='host', active=True)
        print(query)
        return


# Temporary class to flush out ndb storage
class DeleteAll(BaseHandler):
    def post(self):
        links = Link.query_links()

        for link in links:
            link.key.delete()

        self.redirect('/')
        self.response.set_status(205)

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/links', LinkPage),
    ('/links/', LinkPage),
    ('/links/(.+)/(.+)', ItemPage),
    ('/links/(.+)', OwnerPage),
    ('/delete', DeleteAll),
    ('/test', TestButton),
    ('/(.+)', RedirectPage)
])
