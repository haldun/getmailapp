from google.appengine.ext import db

class Account(db.Model):
  user = db.UserProperty(auto_current_user_add=True, required=True)
  email = db.EmailProperty(required=True) # key == <email>
  created_at = db.DateTimeProperty(auto_now_add=True)
  updated_at = db.DateTimeProperty(auto_now=True)


class Address(db.Model):
  account = db.ReferenceProperty(Account, collection_name='addresses')
  token = db.StringProperty(required=True) # key
  post_url = db.URLProperty(required=True)
  created_at = db.DateTimeProperty(auto_now_add=True)
  updated_at = db.DateTimeProperty(auto_now=True)


class Message(db.Model):
  account = db.ReferenceProperty(Account, collection_name='messages')
  address = db.ReferenceProperty(Address, collection_name='messages')
  raw_contents = db.TextProperty()
  created_at = db.DateTimeProperty(auto_now_add=True)
