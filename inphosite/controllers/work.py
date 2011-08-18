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
import inphosite.model as model
from inphosite.model import Work, Entity
from inphosite.model import Session

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
    
    #UPDATE
    def update(self, id=None):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        work = h.fetch_obj(Work, id)
        terms = ['sep_dir'] 

        h.update_obj(work, terms, request.params)

        return self.view(id)

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

        work = Work(name, **params)
        Session.add(work)
        Session.flush()

        # Issue an HTTP success
        response.status_int = 302
        response.headers['location'] = h.url(controller='work',
                                                 action='view', id=work.ID)
        return "Moved temporarily"


    def admin(self, id=None):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)
        
        c.sepdirnew = False
        c.alreadysepdir = False

        redirect = request.params.get('redirect', False)
        add = request.params.get('add', False)
        limit = request.params.get('limit', None)
        entity_q = Session.query(Entity)
        c.found = False    
        c.custom = False
        c.new = False

        if request.params.get('q'):
            q = request.params['q']
            o = Entity.label.like(q)
            entity_q = entity_q.filter(o).order_by(func.length(Entity.label))
            # if only 1 result, go ahead and view that idea
            if redirect and entity_q.count() == 1:
                print "have a q, entityq count = 1"
                c.work = h.fetch_obj(Work, entity_q.first().ID)
                c.found = True
                id = c.work.ID
                c.message = 'Entity edit page for work ' + c.work.name
                if request.params.get('entry_sep_dir'):
                        entry_sep_dir = request.params['entry_sep_dir']
                        if not (c.work.sep_dir):
                            c.work.sep_dir = request.params['entry_sep_dir']
                            c.sepdirnew = True
                        else:
                            c.alreadysepdir = True
                            c.entry_sep_dir = request.params['entry_sep_dir']
                return render('admin/work-edit.html')
            else: 
                print "That didn't work."

        if id is None:
            print "I am here"
            c.message = "Please input an entity label using the search bar to the left."
            return render ('admin/idea-edit.html')
        else:
            c.work = h.fetch_obj(Work, id)
            c.found = True
            c.message = 'Entity edit page for work ' + c.work.label
            if request.params.get('entry_sep_dir'):
                entry_sep_dir = request.params['entry_sep_dir']
                if not (c.work.sep_dir):
                    c.work.sep_dir = request.params['entry_sep_dir']
                    c.sepdirnew = True
                else:
                    c.alreadysepdir = True
                    c.entry_sep_dir = request.params['entry_sep_dir']
                    
            return render ('admin/work-edit.html') 
    
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
            work_add = Work(label)
            #work_add.label = label
            
            #setup search string and search pattern
            workname = work_add.label
            workname_q = Session.query(Entity)
            o = Entity.label.like('( '+ workname + ' )')
            workname_q = workname_q.filter(o).order_by(func.length(Entity.label))
            if workname_q.count() == 0:
                work_add.searchpattern = "( " + workname + " )"
                work_add.searchstring = workname
            else:
                work_add.searchpattern = "( " + label + " )"
                work_add.searchstring = label
                #reset old work pattern to whole name too to avoid conflict
                oldwork = h.fetch_obj(Work, workname_q.first().ID)
                oldwork.searchpattern = "( " + oldwork.label + " )"
                oldwork.searchstring = oldwork.label
                Session.add(oldwork)

            if sep_dir:
                work_add.sep_dir = sep_dir
            c.work = work_add
            Session.add(work_add)
            Session.flush()
            Session.commit()
            c.found = True
            c.message = "Work " + c.work.label + " added successfully."
            return render ('admin/work-edit.html')
        elif action=="Modify":
            c.work = h.fetch_obj(Work, id)
            c.found = True
            changed = False
            
            #set values from form
            if c.work.label != label:
                c.work.label = label
                changed = True
            if c.work.sep_dir != sep_dir:
                c.work.sep_dir = sep_dir
                changed = True
            
            #commit changes
            Session.flush()
            Session.commit()
            if changed:
                c.message = "Work " + c.work.label + " modified successfully."
            else:
                c.message = "No change required; Work " + c.work.label + " not modified."
            return render ('admin/work-edit.html')
                    
        elif action == "Delete":
            c.work = h.fetch_obj(Work, values['ID'])
            c.message = "Work # " + values['ID'] + " ("+ c.work.label + ") deleted; please search for a new entity label on the left."
            h.delete_obj(c.work)
            Session.flush()
            Session.commit()
            c.found = False
            return render('admin/work-edit.html')
    
        
    

    
