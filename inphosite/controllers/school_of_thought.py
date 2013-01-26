import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect

# import decorators
from pylons.decorators import validate
from pylons.decorators.cache import beaker_cache
from inphosite.lib.rest import restrict, dispatch_on

from inphosite.lib.base import BaseController, render

import inpho.model as model
from inpho.model import SchoolOfThought, Entity
from inpho.model import Session
import inphosite.lib.helpers as h
from inphosite.controllers.entity import EntityController

from sqlalchemy import or_
from sqlalchemy.sql.expression import func

import re



log = logging.getLogger(__name__)

class SchoolOfThoughtController(EntityController):
    _type = SchoolOfThought
    _controller = 'school_of_thought'

    # render the editing GUI
    def edit(self, id=None):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        c.school_of_thought = h.fetch_obj(SchoolOfThought, id)

        return render('school_of_thought/school_of_thought-edit.html')

    def data_integrity(self, filetype='html', redirect=False):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        school_q = Session.query(SchoolOfThought)
        c.schools = list(school_q)

        # Missing sep_dir
        c.missing_sep_dir = [school for school in c.schools
                             if not getattr(school, "sep_dir")]

        # Duplicates
        c.duplicate = []
        c.sorted_schools = sorted(c.schools, key=lambda school: school.label)
        for i in range(len(c.sorted_schools) - 1):
            if c.sorted_schools[i].label == c.sorted_schools[i+1].label:
                c.duplicate.append(c.sorted_schools[i])
                c.duplicate.append(c.sorted_schools[i+1])

        return render('school_of_thought/data_integrity.%s' % filetype)

    @restrict('POST')
    def create(self):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        valid_params = ["sep_dir", "wiki"]
        params = request.params.mixed()

        if '_method' in params:
            del params['_method']
        if 'label' in params:
            label = params['label']
            del params['label']
        else:
            abort(400)
        for k in params.keys():
            if k not in valid_params:
                abort(400)

        school_of_thought = SchoolOfThought(name, **params)
        Session.add(school_of_thought)
        Session.flush()

        # Issue an HTTP success
        response.status_int = 302
        response.headers['location'] = h.url(controller='school_of_thought',
                                                 action='view', id=school_of_thought.ID)
        return "Moved temporarily"

