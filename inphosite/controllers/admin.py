import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect as rd

# import decorators
from pylons.decorators import validate
from pylons.decorators.cache import beaker_cache
from inphosite.lib.rest import restrict, dispatch_on

# import inphosite information
from inphosite.lib.base import BaseController, render

from inpho.corpus.sep import get_title, get_titles, new_entries
import inpho.model as model
from inpho.model import *
from inpho.model import Session
import inphosite.lib.helpers as h
import webhelpers.paginate as paginate
from sqlalchemy import or_

log = logging.getLogger(__name__)

import formencode
from formencode import htmlfill, validators, FancyValidator
import simplejson

class AdminController(BaseController):
    def __before__(self):
        # protect entire controller for admins only
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

    def list(self, id = None):
        return rd('/entity/list_new')
