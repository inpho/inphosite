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
    
    #UPDATE
    def update(self, id=None):
        terms = ['sep_dir']
        super(SchoolOfThoughtController, self).update(id, terms)

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


    def admin(self, id=None):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        redirect = request.params.get('redirect', False)
        add = request.params.get('add', False)
        limit = request.params.get('limit', None)
        entity_q = Session.query(Entity)
        c.found = False    
        c.custom = False
        c.new = False
        c.sepdirnew = False
        c.alreadysepdir = False

        if request.params.get('q'):
            q = request.params['q']
            o = Entity.label.like(q)
            entity_q = entity_q.filter(o).order_by(func.length(Entity.label))
            # if only 1 result, go ahead and view that idea
            if redirect and entity_q.count() == 1:
                print "have a q, entityq count = 1"
                c.school_of_thought = h.fetch_obj(SchoolOfThought, entity_q.first().ID)
                c.found = True
                id = c.school_of_thought.ID
                c.message = 'Entity edit page for school_of_thought ' + c.school_of_thought.label
                if request.params.get('entry_sep_dir'):
                        entry_sep_dir = request.params['entry_sep_dir']
                        if not (c.school_of_thought.sep_dir):
                            c.school_of_thought.sep_dir = request.params['entry_sep_dir']
                            c.sepdirnew = True
                        else:
                            c.alreadysepdir = True
                            c.entry_sep_dir = request.params['entry_sep_dir']
                return render('admin/school_of_thought-edit.html')
            else: 
                print "That didn't school_of_thought."

        if id is None:
            print "I am here"
            c.message = "Please input an entity label using the search bar to the left."
            return render ('admin/idea-edit.html')
        else:
            c.school_of_thought = h.fetch_obj(SchoolOfThought, id)
            c.found = True
            c.message = 'Entity edit page for school_of_thought ' + c.school_of_thought.label
            if request.params.get('entry_sep_dir'):
                entry_sep_dir = request.params['entry_sep_dir']
                if not (c.school_of_thought.sep_dir):
                    c.school_of_thought.sep_dir = request.params['entry_sep_dir']
                    c.sepdirnew = True
                else:
                    c.alreadysepdir = True
                    c.entry_sep_dir = request.params['entry_sep_dir']
                    
            return render ('admin/school_of_thought-edit.html') 
    
    def process(self, id=None):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)
        
        c.sepdirnew = False
        c.alreadysepdir = False

        label = request.params.get('label', None)
        id = request.params.get('ID', id)
        sep_dir = request.params.get('sep_dir', None)
        
        action = request.params.get('action', None)
        action2 = request.params.get('action2', None)
        if action2:
            action = action2
        
        values = dict(request.params)
        
        if action=="Add":
            school_of_thought_add = SchoolOfThought(label)
            #school_of_thought_add.label = label
            
            #setup search string and search pattern
            school_of_thoughtname = school_of_thought_add.label
            school_of_thoughtname_q = Session.query(Entity)
            o = Entity.label.like('( '+ school_of_thoughtname + ' )')
            school_of_thoughtname_q = school_of_thoughtname_q.filter(o).order_by(func.length(Entity.label))
            if school_of_thoughtname_q.count() == 0:
                school_of_thought_add.searchpattern = "( " + school_of_thoughtname + " )"
                school_of_thought_add.searchstring = school_of_thoughtname
            else:
                school_of_thought_add.searchpattern = "( " + label + " )"
                school_of_thought_add.searchcstring = label
                #reset old school_of_thought pattern to whole name too to avoid conflict
                oldschool_of_thought = h.fetch_obj(SchoolOfThought, school_of_thoughtname_q.first().ID)
                oldschool_of_thought.searchpattern = "( " + oldschool_of_thought.label + " )"
                oldschool_of_thought.searchstring = oldschool_of_thought.label
                Session.add(oldschool_of_thought)

            if sep_dir:
                school_of_thought_add.sep_dir = sep_dir
            c.school_of_thought = school_of_thought_add
            Session.add(school_of_thought_add)
            Session.flush()
            Session.commit()
            c.found = True
            c.message = "SchoolOfThought " + c.school_of_thought.label + " added successfully."
            return render ('admin/school_of_thought-edit.html')
        elif action=="Modify":
            c.school_of_thought = h.fetch_obj(SchoolOfThought, id)
            c.found = True
            changed = False
            
            #set values from form
            if c.school_of_thought.label != label:
                c.school_of_thought.label = label
                changed = True
            if c.school_of_thought.sep_dir != sep_dir:
                c.school_of_thought.sep_dir = sep_dir
                changed = True
            
            #commit changes
            Session.flush()
            Session.commit()
            if changed:
                c.message = "SchoolOfThought " + c.school_of_thought.label + " modified successfully."
            else:
                c.message = "No change needed; SchoolOfThought " + c.school_of_thought.label + " not modified."
            return render ('admin/school_of_thought-edit.html')
                    
        elif action == "Delete":
            c.school_of_thought = h.fetch_obj(SchoolOfThought, values['ID'])
            c.message = "SchoolOfThought # " + values['ID'] + " ("+ c.school_of_thought.label + ") deleted; please search for a new entity label on the left."
            h.delete_obj(c.school_of_thought)
            Session.flush()
            Session.commit()
            c.found = False
            return render('admin/school_of_thought-edit.html')
    
        
    

    
