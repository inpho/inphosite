import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons import url
import re

from inphosite.lib.base import BaseController, render

import inphosite.model as model
from inphosite.model.meta import Session
import inphosite.lib.helpers as h
from sqlalchemy import or_
from sqlalchemy.sql.expression import func

log = logging.getLogger(__name__)

class EntityController(BaseController):
    def list(self, filetype='html'):
        redirect = request.params.get('redirect', False)
        limit = request.params.get('limit', None)
        entity_q = model.meta.Session.query(model.Entity)
        entity_q = entity_q.filter(model.Entity.typeID != 2)
        
        c.nodes = model.meta.Session.query(model.Node).filter(model.Node.parent_id == None).order_by("name").all()
        c.query = '' 
        c.sep = ''

        if filetype=='json':
            response.content_type = 'application/json'

        if request.params.get('sep_filter'):
            entity_q = entity_q.filter(model.Entity.sep_dir != '')
        
        if request.params.get('sep'):
            entity_q = entity_q.filter(model.Entity.sep_dir == request.params['sep'])
            c.sep = request.params['sep']
            # if only 1 result, go ahead and view that entity
            if redirect and entity_q.count() == 1:
                h.redirect(h.url(controller='entity', action='view',
                filetype=filetype, id=entity_q.first().ID), code=302)

        # Check for query
        if request.params.get('q'):
            q = request.params['q']
            c.query = q
            o = or_(model.Entity.label.like(q+'%'), model.Entity.label.like('% '+q+'%'))
            entity_q = entity_q.filter(o).order_by(func.length(model.Entity.label))
            # if only 1 result, go ahead and view that idea
            if redirect and entity_q.count() == 1:
                return self.view(entity_q.first().ID, filetype)
            else:
                c.entities = entity_q.limit(limit)
                return render('entity/entity-list.' + filetype)

        c.entities = entity_q.limit(limit)
        return render('entity/entity-list.' + filetype)
    
    def search_with(self, id, id2):
        c.entity = h.fetch_obj(model.Entity, id)
        c.entity2 = h.fetch_obj(model.Entity, id2)
        return render('entity/search.html')
    def search2(self, id, id2):
        c.entity = h.fetch_obj(model.Entity, id)
        c.entity2 = h.fetch_obj(model.Entity, id2)
        return render('entity/search2.html')
    
    def search(self, id):
        c.entity = h.fetch_obj(model.Entity, id)
        return render('entity/search-one.html')

    def view(self, id=None, filetype='html'):
        c.entity = h.fetch_obj(model.Entity, id, new_id=True)
        redirect(c.entity.url(filetype), code=303)
        #c.nodes = model.meta.Session.query(model.Node).order_by("Name").all()
        #return render('entity/entity.' + filetype)

    def graph(self, id=None, id2=None, filetype='json'):
        c.entity = h.fetch_obj(model.Entity, id, new_id=True)
        if not id2:
            redirect(c.entity.url(filetype, action="graph"), code=303)
        else:
            c.entity2 = h.fetch_obj(model.Entity, new_id=True)
            redirect(c.entity.url(filetype, action="graph"), code=303)

            


    def admin(self, id=None):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        redirect = request.params.get('redirect', False)
        add = request.params.get('add', False)
        limit = request.params.get('limit', None)
        sep_dir = request.params.get('sep_dir', "")
        entity_q = Session.query(model.Entity)
        c.found = False    
        c.custom = False
        c.new = False
        c.sep_dir = sep_dir
        c.sepdirnew = False
        c.alreadysepdir = False

        if request.params.get('q'):
            q = request.params['q']
            o = model.Entity.label.like(q)
            entity_q = entity_q.filter(o).order_by(func.length(model.Entity.label))
            # if only 1 result, go ahead and view that entity
            if redirect and entity_q.count() == 1:
                c.entity = h.fetch_obj(model.Entity, entity_q.first().ID)
                
                #now get type and route to correct edit page
                #first, if it is an idea, typeID = 1
                if c.entity.typeID == 1:
                    print "have an idea, q, entityq count = 1"
                    c.idea = h.fetch_obj(model.Idea, entity_q.first().ID)
                    c.found = True
                    id = c.idea.ID
                    c.message = 'Entity edit page for idea ' + c.idea.label
                    #set up c.search_string_list which will be used to structure intersection/union search pattern option
                    if request.params.get('sep_dir'):
                            sep_dir = request.params['sep_dir']
                            if not (c.idea.sep_dir):
                                c.idea.sep_dir = request.params['sep_dir']
                                c.sepdirnew = True
                            else:
                                c.alreadysepdir = True
                                c.entry_sep_dir = request.params['sep_dir']
                    c.search_string_list = c.idea.setup_SSL()
                    if re.search(' and ', c.idea.label):
                        c.search_pattern_list = ['union', 'intersection']
                    return render ('admin/idea-edit.html') 
                
                #thinkers
                elif c.entity.typeID == 3:
                    print "have a thinker, q, entityq count = 1"
                    c.thinker = h.fetch_obj(model.Thinker, entity_q.first().ID)
                    c.found = True
                    id = c.thinker.ID
                    c.message = 'Entity edit page for thinker ' + c.thinker.label
                    if request.params.get('sep_dir'):
                            sep_dir = request.params['sep_dir']
                            if not (c.thinker.sep_dir):
                                c.thinker.sep_dir = request.params['sep_dir']
                                c.sepdirnew = True
                            else:
                                c.alreadysepdir = True
                                c.entry_sep_dir = request.params['sep_dir']
                    return render ('admin/thinker-edit.html')
                
                
                elif c.entity.typeID == 4:
                    print "have a journal, q, entityq count = 1"
                    c.journal = h.fetch_obj(model.Journal, entity_q.first().ID)
                    c.found = True
                    id = c.journal.ID
                    c.message = 'Entity edit page for journal ' + c.journal.label
                    if request.params.get('sep_dir'):
                            sep_dir = request.params['sep_dir']
                            if not (c.journal.sep_dir):
                                c.journal.sep_dir = request.params['sep_dir']
                                c.sepdirnew = True
                            else:
                                c.alreadysepdir = True
                                c.entry_sep_dir = request.params['sep_dir']
                    return render ('admin/journal-edit.html')

                elif c.entity.typeID == 5:
                    print "have a work, q, entityq count = 1"
                    c.work = h.fetch_obj(model.Work, entity_q.first().ID)
                    c.found = True
                    id = c.work.ID
                    c.message = 'Entity edit page for work ' + c.work.label
                    if request.params.get('sep_dir'):
                            sep_dir = request.params['sep_dir']
                            if not (c.work.sep_dir):
                                c.work.sep_dir = request.params['sep_dir']
                                c.sepdirnew = True
                            else:
                                c.alreadysepdir = True
                                c.entry_sep_dir = request.params['sep_dir']
                    return render ('admin/work-edit.html')
                
                elif c.entity.typeID == 6:
                    print "have a school_of_thought, q, entityq count = 1"
                    c.school_of_thought = h.fetch_obj(model.SchoolOfThought, entity_q.first().ID)
                    c.found = True
                    id = c.school_of_thought.ID
                    c.message = 'Entity edit page for school_of_thought ' + c.school_of_thought.label
                    if request.params.get('sep_dir'):
                            sep_dir = request.params['sep_dir']
                            if not (c.school_of_thought.sep_dir):
                                c.school_of_thought.sep_dir = request.params['sep_dir']
                                c.sepdirnew = True
                            else:
                                c.alreadysepdir = True
                                c.entry_sep_dir = request.params['sep_dir']
                    return render ('admin/school_of_thought-edit.html')
            
            
            elif redirect and entity_q.count() == 0:
                c.message = "No match found for your search; if you would like to add your idea, please enter its label and sepdir into the field below."
                c.new = True
                c.prevvalue = q
                return render ('admin/entity-add.html') 

            else:
                return ('No exact match for your search; please click "back" and try again.')

        if id is None:
            print "I am here"
            c.message = "Please input an idea using the search bar to the left."
            return render ('admin/idea-edit.html')
        else:
            c.entity = h.fetch_obj(model.Entity, id)
            c.found = True
            c.message = 'Entity edit page for entity ' + c.entity.label
            
            #get sep_dir if present--from admin.py action addentry
            if request.params.get('sep_dir'):
                sep_dir = request.params['sep_dir']
                if not (c.entity.sep_dir):
                    c.entity.sep_dir = sep_dir
                else:
                    c.message = c.message + "WARNING:  entity already has a sep_dir [" + c.entity.sep_dir + "].  Not replacing with [" + sep_dir + "].  If you would like to do so, please do so manually in the form below."
            
            if request.params.get('entry_sep_dir'):
                entry_sep_dir = request.params['entry_sep_dir']
                if not (c.entity.sep_dir):
                    c.entity.sep_dir = entry_sep_dir
                else:
                    c.message = c.message + "WARNING:  entity already has a sep_dir [" + c.entity.sep_dir + "].  Not replacing with [" + sep_dir + "].  If you would like to do so, please do so manually in the form below."
            
                    
            #set up c.search_string_list which will be used to structure intersection/union search pattern option
            if c.entity.typeID == 1:
                c.idea = h.fetch_obj(model.Idea, c.entity.ID)
                c.search_string_list = c.idea.setup_SSL()
                return render ('admin/idea-edit.html')
            elif c.entity.typeID == 3:
                c.thinker = h.fetch_obj(model.Thinker, c.entity.ID)
                return render('admin/thinker-edit.html')
            elif c.entity.typeID == 4:
                c.journal = h.fetch_obj(model.Journal, c.entity.ID)
                return render('admin/journal-edit.html')
            elif c.entity.typeID == 5:
                c.work = h.fetch_obj(model.Work, c.entity.ID)
                return render('admin/work-edit.html')
            elif c.entity.typeID == 6:
                c.school_of_thought = h.fetch_obj(model.SchoolOfThought, c.entity.ID)
                return render('admin/school_of_thought-edit.html')
        
        
        c.entity = h.fetch_obj(model.Entity, id, new_id=True)
        redirect(c.entity.url(action='admin'), code=303)
        
    def process(self, entity_type = '1', id=None):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        q = request.params.get('q', None)
        label = request.params.get('label', None)
        sep_dir = request.params.get('sep_dir', None)
        action = request.params.get('action', None)
        
                
        type = request.params.get("entity_type", '1')
        if type == '1':
            redirect(url(controller='idea', action='process', q = q, label = label, sep_dir = sep_dir, action2 = action), code=303)
        elif type == '3':
            print "hi der m tryin to process ur thinker"
            redirect(url(controller = 'thinker', action='process', q = q, label = label, sep_dir = sep_dir, action2 = action), code=303)
        elif type == '4':
            print "hi der m tryin to process ur journal"
            redirect(url(controller = 'journal', action='process', q = q, label = label, sep_dir = sep_dir, action2 = action), code=303)
        elif type == '5':
            print "hi der m tryin to process ur work"
            redirect(url(controller = 'work', action='process', q = q, label = label, sep_dir = sep_dir, action2 = action), code=303)
        elif type == '6':
            print "hi der m tryin to process ur school_of_thought"
            redirect(url(controller = 'school_of_thought', action='process', q = q, label = label, sep_dir = sep_dir, action2 = action), code=303)
