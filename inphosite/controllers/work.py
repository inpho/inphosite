import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect

# import decorators
from pylons.decorators import validate
from pylons.decorators.cache import beaker_cache
from inphosite.lib.rest import restrict, dispatch_on

from inphosite.lib.base import BaseController, render

import inphosite.model as model
import inphosite.model.meta as meta
import inphosite.lib.helpers as h
from inphosite.model import Work

from sqlalchemy import or_
from sqlalchemy.sql.expression import func

import re



log = logging.getLogger(__name__)

class WorkController(BaseController):

    #@beaker_cache(expire=300, type='memory', query_args=True)
    def list(self, filetype='html', redirect=False):
        work_q = model.meta.Session.query(model.Work)
        
        if filetype=='json':
            response.content_type = 'application/json'

        # check for query
        if request.params.get('q'):
            work_q = work_q.filter(model.Work.name.like(u'%'+request.params['q']+'%'))
            # if only 1 result, go ahead and view that thinker
            if redirect and work_q.count() == 1:
                return self.view(work_q.first().ID, filetype)
        
        if request.params.get('sep'):
            work_q = work_q.filter(model.Work.sep_dir == request.params['sep'])
            # if only 1 result, go ahead and view that thinker
            if redirect and work_q.count() == 1:
                return self.view(work_q.first().ID, filetype)

        c.works = work_q.all()
        return render('work/work-list.' + filetype)

    #@beaker_cache(expire=60, type='memory', query_args=True)
    def view(self, id, filetype='html'):
        sep_filter = request.params.get('sep_filter', False) 
        c.sep_filter = sep_filter

        if filetype=='json':
            response.content_type = 'application/json'

        c.work = h.fetch_obj(Work, id, new_id=True)
        return render('work/work.%s' % filetype)
    
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

        work = h.fetch_obj(model.Work, id)
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

        work = model.Work(name, **params)
        meta.Session.add(work)
        meta.Session.flush()

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
        entity_q = model.meta.Session.query(model.Entity)
        c.found = False    
        c.custom = False
        c.new = False

        if request.params.get('q'):
            q = request.params['q']
            o = model.Entity.label.like(q)
            entity_q = entity_q.filter(o).order_by(func.length(model.Entity.label))
            # if only 1 result, go ahead and view that idea
            if redirect and entity_q.count() == 1:
                print "have a q, entityq count = 1"
                c.work = h.fetch_obj(model.Work, entity_q.first().ID)
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
            c.work = h.fetch_obj(model.Work, id)
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
            work_add = model.Work(label)
            #work_add.label = label
            
            #setup search string and search pattern
            workname = work_add.label
            workname_q = model.meta.Session.query(model.Entity)
            o = model.Entity.label.like('( '+ workname + ' )')
            workname_q = workname_q.filter(o).order_by(func.length(model.Entity.label))
            if workname_q.count() == 0:
                work_add.searchpattern = "( " + workname + " )"
                work_add.searchstring = workname
            else:
                work_add.searchpattern = "( " + label + " )"
                work_add.searchstring = label
                #reset old work pattern to whole name too to avoid conflict
                oldwork = h.fetch_obj(model.Work, workname_q.first().ID)
                oldwork.searchpattern = "( " + oldwork.label + " )"
                oldwork.searchstring = oldwork.label
                meta.Session.add(oldwork)

            if sep_dir:
                work_add.sep_dir = sep_dir
            c.work = work_add
            meta.Session.add(work_add)
            meta.Session.flush()
            meta.Session.commit()
            c.found = True
            c.message = "Work " + c.work.label + " added successfully."
            return render ('admin/work-edit.html')
        elif action=="Modify":
            c.work = h.fetch_obj(model.Work, id)
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
            meta.Session.flush()
            meta.Session.commit()
            if changed:
                c.message = "Work " + c.work.label + " modified successfully."
            else:
                c.message = "No change required; Work " + c.work.label + " not modified."
            return render ('admin/work-edit.html')
                    
        elif action == "Delete":
            c.work = h.fetch_obj(model.Work, values['ID'])
            c.message = "Work # " + values['ID'] + " ("+ c.work.label + ") deleted; please search for a new entity label on the left."
            h.delete_obj(c.work)
            meta.Session.flush()
            meta.Session.commit()
            c.found = False
            return render('admin/work-edit.html')
    
        
    

    
