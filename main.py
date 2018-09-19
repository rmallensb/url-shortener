import webapp2

from backend import MainPage
from backend import LinkPage
from backend import OwnerPage
from backend import ItemPage
from backend import Redirect
from backend.utility import *


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
    ('/links/?', LinkPage),
    ('/links/(.+)/(.+)', ItemPage),
    ('/links/(.+)', OwnerPage),
    ('/delete', DeleteAll),
    ('/test', TestButton),
    ('/(.+)', Redirect)
])
