import logging
import os
import email.utils

import tornado.web
import tornado.wsgi
from tornado.web import url

from google.appengine.api import mail
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import deferred
from google.appengine.ext.webapp.util import run_wsgi_app

from django.utils import simplejson as json

import forms
import models
import uimodules

# Constants
IS_DEV = os.environ['SERVER_SOFTWARE'].startswith('Dev')  # Development server

class Application(tornado.wsgi.WSGIApplication):
  def __init__(self):
    handlers = [
      (r'/', IndexHandler),
      (r'/home', HomeHandler),
      url(r'/addresses', ListAddressHandler, name='addresses'),
      url(r'/addresses/new', NewAddressHandler, name='new_address'),
      url(r'/addresses/edit', EditAddressHandler, name='edit_address'),
      url(r'/addresses/delete', DeleteAddressHandler, name='delete_address'),
      url(r'/addresses/([^/]+)/messages', ListMessagesHandlers, name='messages'),

      # Inbound
      (r'/_ah/mail/.+', InboundHandler),

      # Tasks
      (r'/tasks/transmit_message', TransmitMessageHandler),
    ]
    settings = dict(
      debug=IS_DEV,
      static_path=os.path.join(os.path.dirname(__file__), "static"),
      template_path=os.path.join(os.path.dirname(__file__), 'templates'),
      xsrf_cookies=True,
      cookie_secret="m9i-asdj123ansdnzxjch7o23ij09iaodljansdiu123ojadsoo",
      ui_modules=uimodules,
    )
    tornado.wsgi.WSGIApplication.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
  def get_current_user(self):
    user = users.get_current_user()
    if user:
      user.admin = users.is_current_user_admin()
      account = models.Account.get_account_for_user(user)
      self.current_account = account
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


class ListAddressHandler(BaseHandler):
  @tornado.web.authenticated
  def get(self):
    self.render('list_addresses.html', addresses=self.current_account.addresses)


class NewAddressHandler(BaseHandler):
  @tornado.web.authenticated
  def get(self):
    self.render('new_address.html', form=forms.AddressForm())

  @tornado.web.authenticated
  def post(self):
    form = forms.AddressForm(self)
    if form.validate():
      address = models.Address(
        account=self.current_account,
        address=form.address.data,
        callback_url=form.callback_url.data)
      address.put()
      self.redirect(self.reverse_url('addresses'))
    else:
      self.render('new_address.html', form=form)


class EditAddressHandler(BaseHandler):
  @tornado.web.authenticated
  def get(self):
    self.write("not implemented")

  @tornado.web.authenticated
  def post(self):
    self.write("not implemented")


class DeleteAddressHandler(BaseHandler):
  @tornado.web.authenticated
  def post(self):
    self.write("not implemented")


def transmit_message(address_key, message):
  address = models.Address.get(address_key)
  logging.info("address: %s" % address)


class InboundHandler(BaseHandler):
  def initialize(self):
    self.application.settings['xsrf_cookies'] = False

  def post(self):
    message = mail.InboundEmailMessage(self.request.body)

    # Get all address in the email to + cc
    addresses = message.to.split(',')
    if hasattr(message, 'cc'):
      addresses += message.cc.split(',')
    addresses = email.utils.getaddresses(addresses)

    # Try to find the account in db
    address = None
    for _, address in addresses:
      address = address.split('@')[0]
      # TODO Check if the address is in our domain
      address = models.Address.all().filter('address =', address).get()
      if address is not None:
        break

    if address is None:
      logging.info("Unknown address")
      return

    # Save message
    contents = message.original.as_string(True)
    msg = models.Message(
      account=address.account,
      address=address,
      subject=message.subject,
      sender=message.sender,
      raw_contents=contents,
    )
    msg.put()

    # Send the message to the callback_url
    taskqueue.add(url='/tasks/transmit_message',
                  params={'message_key': msg.key()})


class TaskHandler(BaseHandler):
  def initialize(self):
    self.application.settings['xsrf_cookies'] = False


class TransmitMessageHandler(TaskHandler):
  def post(self):
    message = models.Message.get(self.get_argument('message_key'))
    address = message.address
    result = {'email': {'raw': message.raw_contents}}

    try:
      result = urlfetch.fetch(address.callback_url,
                              payload=json.dumps(result),
                              method='POST',
                              headers={
                               'Content-Type': 'application/json'
                              },
                              deadline=10)
    except:
      message.status = models.MessageState.FAILED
    else:
      if result.status_code == 200:
        message.status = models.MessageState.SUCCESS
      else:
        message.status = models.MessageState.FAILED
    message.put()


class ListMessagesHandlers(BaseHandler):
  @tornado.web.authenticated
  def get(self, id=None):
    address = models.Address.get_by_id(int(id))
    if address.account.key() != self.current_account.key():
      raise tornado.web.HTTPError(403)
    self.render("list_messages.html", address=address, messages=address.recent_messages)


def main():
  run_wsgi_app(Application())

if __name__ == '__main__':
  main()
