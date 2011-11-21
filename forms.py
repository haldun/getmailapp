from wtforms import *
from wtforms.validators import *

from django.utils.datastructures import MultiValueDict

import models

class BaseForm(Form):
  def __init__(self, handler=None, obj=None, prefix='', formdata=None, **kwargs):
    if handler:
      formdata = MultiValueDict()
      for name in handler.request.arguments.keys():
        formdata.setlist(name, handler.get_arguments(name))
    Form.__init__(self, formdata, obj=obj, prefix=prefix, **kwargs)


class AddressForm(BaseForm):
  address = TextField('address', [Required()])
  callback_url = TextField('callback url', [Required()])

  def validate_address(self, field):
    if models.Address.all().filter('address =', field.data).count():
      raise ValidationError("is in use. Try a different one.")
