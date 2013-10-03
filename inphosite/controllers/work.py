import logging
import re

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect

from pylons.decorators import validate
from pylons.decorators.cache import beaker_cache

from inphosite.controllers.entity import EntityController
from inphosite.lib.base import BaseController, render
import inphosite.lib.helpers as h
from inphosite.lib.rest import restrict, dispatch_on
import inpho.model as model
from inpho.model import Work, Entity
from inpho.model import Session

from sqlalchemy import or_
from sqlalchemy.sql.expression import func

log = logging.getLogger(__name__)

class WorkController(EntityController):
    _type = Work
    _controller = 'work'

    # render the editing GUI
    def edit(self, id=None):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        c.work = h.fetch_obj(Work, id)
        
        return render('work/work-edit.html')
    
    @restrict('POST')
    def create(self):
        valid_params = ["sep_dir", "wiki"]
        EntityController.create(self,entity_type=5,valid_params=valid_params)
