import logging
import os

import tornado.web
import tornado.wsgi
from tornado.web import url

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app

import forms
import models

# Constants
IS_DEV = os.environ['SERVER_SOFTWARE'].startswith('Dev')  # Development server

class Application(tornado.wsgi.WSGIApplication):
  def __init__(self):
    handlers = [
      (r'/', IndexHandler),
      (r'/home', HomeHandler),

      # Inbound
      (r'/_ah/mail/.+', InboundHandler),
    ]
    settings = dict(
      debug=IS_DEV,
      static_path=os.path.join(os.path.dirname(__file__), "static"),
      template_path=os.path.join(os.path.dirname(__file__), 'templates'),
      xsrf_cookies=True,
      cookie_secret="m9i-asdj123ansdnzxjch7o23ij09iaodljansdiu123ojadsoo",
    )
    tornado.wsgi.WSGIApplication.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
  def get_current_user(self):
    user = users.get_current_user()
    if user:
      user.admin = users.is_current_user_admin()
    return user

  def get_login_url(self):
    return users.create_login_url(self.request.uri)

  def render_string(self, template, **kwds):
    return tornado.web.RequestHandler.render_string(
        self, template, users=users, DEBUG=IS_DEV, **kwds)


class IndexHandler(BaseHandler):
  def get(self):
    self.write('Hello from tornado on app engine')


class HomeHandler(BaseHandler):
  @tornado.web.authenticated
  def get(self):
    self.write("Naber lan? %s" % self.current_user)


class InboundHandler(BaseHandler):
  def initialize(self):
    self.application.settings['xsrf_cookies'] = False

  def post(self):
    message = mail.InboundEmailMessage(self.request.body)
    logging.info('%s' % message)

class OutboundHandler(BaseHandler):
  def initialize(self):
    self.application.settings['xsrf_token'] = False

  def post(self):
    pass


def main():
  run_wsgi_app(Application())

if __name__ == '__main__':
  main()
