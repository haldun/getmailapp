import os

from google.appengine.ext import db

class Account(db.Model):
  user = db.UserProperty(auto_current_user_add=True, required=True)
  email = db.EmailProperty(required=True) # key == <email>
  created_at = db.DateTimeProperty(auto_now_add=True)
  updated_at = db.DateTimeProperty(auto_now=True)
  lower_email = db.StringProperty()

  def put(self):
    self.lower_email = str(self.email).lower()
    super(Account, self).put()

  @classmethod
  def get_account_for_user(cls, user):
    email = user.email()
    assert email
    key = '<%s>' % email
    account = cls.get_by_key_name(key)
    if account is not None:
      return account
    return cls.get_or_insert(key, user=user, email=email)


class Address(db.Model):
  account = db.ReferenceProperty(Account, collection_name='addresses', required=True)
  address = db.StringProperty(required=True) # key
  callback_url = db.URLProperty(required=True)
  token = db.StringProperty()
  created_at = db.DateTimeProperty(auto_now_add=True)
  updated_at = db.DateTimeProperty(auto_now=True)

  def put(self):
    self.token = os.urandom(16).encode('hex')
    super(Address, self).put()


class MessageState(object):
  WAITING = 1
  SUCCESS = 2
  FAILED = 3

class Message(db.Model):
  account = db.ReferenceProperty(Account, collection_name='messages')
  address = db.ReferenceProperty(Address, collection_name='messages')
  raw_contents = db.TextProperty()
  status = db.IntegerProperty(default=MessageState.WAITING)
  created_at = db.DateTimeProperty(auto_now_add=True)
