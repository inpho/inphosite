"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password
from pylons import url
from webhelpers.html.tags import *
#from formbuild.helpers import field
#from formbuild import start_with_layout as form_start, end_with_layout as form_end
from pylons.controllers.util import abort, redirect
import re


def titlecase(s):
    title = []
    stops = ['the', 'a', 'an', 'of',
             'and', 'or', 'but',
             'in', 'on', 'from', 'with', 'to', 'by']
    for i, subst in enumerate(s.split()):
        if i > 0 and subst in stops:
            title.append(subst)
        else:
            title.append(subst[0].upper() + subst[1:])
    s = ' '.join(title)
    title = []
    for i, subst in enumerate(s.split('-')):
        if i > 0 and subst in stops:
            title.append(subst)
        else:
            title.append(subst[0].upper() + subst[1:])
    return '-'.join(title)

# MISC HELPERS:

import datetime
def now():
    """
    Simple helper function to return current date/time 
    """
    return datetime.datetime.now()

def bc(year=None):
    if year:
        if re.search('BC', year):
            year = year.split(' BC')[0]
            return ('BC', year)
        elif re.search('AD', year):
            year = year.split(' AD')[0]
            return ('AD', year)
        else:
            return ("", year)
    else:
        return ("", "")
#form tools
'''
import pylons.decorators as decorators
from decorator import decorator
@decorator
def validate(*args, **kwargs): 
    f = decorators.validate
    return f(*args, **kwargs)
'''

from webhelpers.html import literal
class LiteralForm(Form):
    def __getattribute__(self, name):
        if name in ['value', 'option', 'error', 'checked', 'flow']:
            return Form.__getattribute__(self, name)
        def make_literal(*k, **p):
            return literal(getattr(Form, name)(self, *k, **p))
        return make_literal

#authentication tools
from inphosite.lib import auth

#model tools
from inphosite.model import User
from inphosite.model.meta import Session
from sqlalchemy.orm.attributes import set_attribute, get_attribute 
from sqlalchemy import or_

def get_user(login):
    """
    Returns the User object from the model.

    :rtype: :class:`inphosite.model.User`
    """
    user = Session.query(User).filter(or_(User.email==login,
                                          User.username==login.lower())).first()
    return user

def fetch_obj(type, id, error=404, new_id=False):
    """
    Fetches the object with the given id from the collection of type type. If
    the object does not exist, throw an HTTP error (default: 404 Not Found).

    :param type: object type
    :type type: class in :mod:`inphosite.model`
    :param id: object id
    :type id: integer or None
    :param error: HTTP error code.
    :rtype: *type*
    """
    if id is None:
        abort(error)
    obj_q = Session.query(type)
    obj = obj_q.get(int(id))
    #else:
    #    obj = obj_q.filter(type.ID==int(id)).first()

    if obj is None:
        abort(error)
    return obj

def update_obj(obj, attributes, params):
    """
    Updates any arbitrary object. Takes a list of attributes and a dictionary of update
    parameters. Checks if each key is in the list of approved attributes and then attempts
    to set it. If the object does not have that key, throw an HTTP 400 Bad Request

    :param obj: object to update
    :param attributes: list of approved attributes
    :param params: dictionary of update parameters 

    """
    for key in params.keys():
        if key in attributes:
            try:
                set_attribute(obj, key, params[key])
            except:
                abort(400)
    
    Session.flush()

def delete_obj(obj):
    """
    Deletes any arbitrary object from the SQLAlchemy Session and cascades deletes to evaluations.

    :param obj: object to delete

    """
    Session.delete(obj)
    Session.flush()

import simplejson
from decimal import Decimal
class ExtJsonEncoder(simplejson.JSONEncoder):
    '''
    Extends ``simplejson.JSONEncoder`` by allowing it to encode any
    arbitrary generator, iterator, closure or functor.
    '''
    def default(self, c):
        # Handles generators and iterators
        if hasattr(c, '__iter__'):
            return [i for i in c]

        # Handles closures and functors
        if hasattr(c, '__call__'):
            return c()

        # Handles precise decimals with loss of precision to float.
        # Hack, but it works
        if isinstance(c, Decimal):
            return float(c)

        return simplejson.JSONEncoder.default(self, c)

def json(*args): 
    '''
    Shortcut for ``ExtJsonEncoder.encode()``
    '''
    return ExtJsonEncoder(sort_keys=False, ensure_ascii=False, 
            skipkeys=True).encode(*args)
