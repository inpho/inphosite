import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect

# import decorators
from pylons.decorators import validate
from pylons.decorators.cache import beaker_cache
from inphosite.lib.rest import restrict, dispatch_on

from inphosite.lib.base import BaseController, render

from inphosite.model import Idea, Entity
from inphosite.model.thinker import *
from inphosite.model.meta import Session
import inphosite.lib.helpers as h

from sqlalchemy import or_
from sqlalchemy.sql.expression import func

import re
log = logging.getLogger(__name__)
unary_vars = {
    'nationality' : {'object' : Nationality, 
                     'property' : 'nationalities'},
    'profession' : {'object' : Profession, 
                    'property' : 'professions'}
}
binary_vars = {
    'has_influenced' : {'object' : ThinkerInfluencedEvaluation, 
                        'reverse' : False, 'maxdegree' : 4},
    'influenced_by' : {'object' : ThinkerInfluencedEvaluation, 
                       'reverse' : True, 'maxdegree' : 4},
    'teacher_of' : {'object' : ThinkerTeacherEvaluation, 
                        'reverse' : False, 'maxdegree' : 1},
    'student_of' : {'object' : ThinkerTeacherEvaluation, 
                        'reverse' : True, 'maxdegree' : 1}
}

class ThinkerController(BaseController):
    #@beaker_cache(expire=300, type='memory', query_args=True)
    def list(self, filetype='html', redirect=False):
        thinker_q = Session.query(Thinker)
        c.query = ''
        c.sep = ''
        
        if request.params.get('sep_filter'):
            idea_q = idea_q.filter(Idea.sep_dir != '')
        
        # check for query
        if request.params.get('q'):
            c.query = request.params['q']
            thinker_q = thinker_q.filter(Thinker.name.like(u'%'+request.params['q']+'%'))
            # if only 1 result, go ahead and view that thinker
            if redirect and thinker_q.count() == 1:
                return self.view(thinker_q.first().ID, filetype)
        
        if request.params.get('sep'):
            thinker_q = thinker_q.filter(Thinker.sep_dir == request.params['sep'])
            c.sep = request.params['sep']
            # if only 1 result, go ahead and view that thinker
            if redirect and thinker_q.count() == 1:
                return self.view(thinker_q.first().ID, filetype)

        c.thinkers = thinker_q.all()
        return render('thinker/thinker-list.' + filetype)

    def list_json(self):
        response.content_type = 'application/json'
        return self.list('json')

    #@beaker_cache(expire=60, type='memory', query_args=True)
    def view(self, id, filetype='html'):
        sep_filter = request.params.get('sep_filter', False) 
        c.sep_filter = sep_filter

        c.thinker = h.fetch_obj(Thinker, id, new_id=True)
        return render('thinker/thinker.%s' % filetype)
    
    def graph(self, id, filetype='html', limit=False):
        sep_filter = request.params.get('sep_filter', False) 
        c.sep_filter = sep_filter

        c.thinker = h.fetch_obj(Thinker, id, new_id=True)
        return render('thinker/graph.%s' % filetype)
    
    def _list_property(self, property, id, filetype='html', limit=False,
    sep_filter=False, type='thinker'):
        c.thinker = h.fetch_obj(Thinker, id)
         
        limit = request.params.get('limit', limit)
        sep_filter = request.params.get('sep_filter', sep_filter)
        property = getattr(c.thinker, property)
        if sep_filter:
            property = property.filter(Entity.sep_dir != '')
        if limit:
            property = property[0:limit-1]
        
        c.thinkers = property
        return render('%s/%s-list.%s' %(type, type, filetype))

    def hyponyms(self, id=None, filetype='html', limit=20, sep_filter=False):
        return self._list_property('hyponyms', id, filetype, limit, sep_filter)

    def related(self, id=None, filetype='html', limit=20, sep_filter=False):
        return self._list_property('related', id, filetype, limit, sep_filter)
    
    def influenced(self, id=None, filetype='html', limit=20, sep_filter=False):
        return self._list_property('influenced', id, filetype, limit, sep_filter)

    def related_ideas(self, id=None, filetype='html', limit=20, sep_filter=False):
        return self._list_property('related_ideas', id, filetype, limit, sep_filter)

    def occurrences(self, id=None, filetype='html', limit=20, sep_filter=False):
        return self._list_property('occurrences', id, filetype, limit, sep_filter)
    
    def idea_occurrences(self, id=None, filetype='html', limit=20, sep_filter=False):
        return self._list_property('idea_occurrences', id, filetype, limit, sep_filter)



    # update teacher_of
    @restrict('POST')
    def teacher_of(self, id=None, id2=None, degree=1):
        if not h.auth.is_logged_in():
            abort(401)

        return _thinker_evaluate(ThinkerTeacherEvaluation,
                                 id, id2, degree)

    # render the editing GUI
    def edit(self, id=None):
        if not h.auth.is_logged_in():
            abort(401)

        c.thinker = h.fetch_obj(Thinker, id)
        
        return render('thinker/thinker-edit.html')
    
    #UPDATE
    def update(self, id=None):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        thinker = h.fetch_obj(Thinker, id)
        terms = ['sep_dir', 'wiki'] 

        h.update_obj(thinker, terms, request.params)

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
        if 'name' in params:
            name = params['name']
            del params['name']
        else:
            abort(400)
        for k in params.keys():
            if k not in valid_params:
                abort(400)

        thinker = Thinker(name, **params)
        Session.add(thinker)
        Session.flush()

        # Issue an HTTP success
        response.status_int = 302
        response.headers['location'] = h.url(controller='thinker',
                                                 action='view', id=thinker.ID)
        return "Moved temporarily"






    def _thinker_evaluate(self, evaltype=None, id=None, id2=None, 
                            uid=None, username=None,
                            degree=1, maxdegree=1):
        """
        Private method to handle generic evaluations. See ``teacher_of`` and ``has_influenced``
        for use.
        """
        id2 = request.params.get('id2', id2)
        uid = request.params.get('uid', uid)
        username = request.params.get('username', username)
        evaluation = self._get_evaluation(evaltype, id, id2, uid, username)

        try:
            evaluation.degree = int(request.params.get('degree', degree))
        except TypeError:
            abort(400)

        # Create and commit evaluation
        Session.flush()

        # Issue an HTTP success
        response.status_int = 200
        return "OK"

    def _get_evaluation(self, evaltype, id, id2, uid=None, username=None, 
                        autoCreate=True):
        thinker1 = h.fetch_obj(Thinker, id)
        thinker2 = h.fetch_obj(Thinker, id2)

        # Get user information
        if uid:
            uid = h.fetch_obj(User, uid).ID
        elif username:
            user = h.get_user(username)
            uid = user.ID if user else abort(404)
        else:
            uid = h.get_user(request.environ['REMOTE_USER']).ID

        evaluation_q = Session.query(evaltype)
        evaluation = evaluation_q.filter_by(ante_id=id, cons_id=id2, 
                                            uid=uid).first()

        # if an evaluation does not yet exist, create one
        if autoCreate and not evaluation:
            evaluation = evaltype(id, id2, uid)
            Session.add(evaluation)

        return evaluation
    
    @restrict('DELETE')
    def _delete_evaluation(self, evaltype, id, id2, uid=None, username=None):
        id2 = request.params.get('id2', id2)
        uid = request.params.get('uid', uid)
        username = request.params.get('username', username)
        evaluation = self._get_evaluation(evaltype, id, id2, uid, username, 
                                          autoCreate=False)
        
        if not evaluation:
            abort(404)

        current_uid = h.get_user(request.environ['REMOTE_USER']).ID
        if evaluation.uid != current_uid and not h.auth.is_admin():
            abort(401)

        h.delete_obj(evaluation)

        response.status_int = 200
        return "OK"



    @dispatch_on(DELETE='_delete_unary')
    @restrict('POST', 'PUT')
    def unary(self, type, id, id2=None):
        thinker = h.fetch_obj(Thinker, id)

        id2 = request.params.get('id2', id2)
        obj = h.fetch_obj(unary_vars[type]['object'], id2)
        
        if obj not in getattr(thinker, unary_vars[type]['property']): 
            getattr(thinker, unary_vars[type]['property']).append(obj)

        Session.commit()

        response.status_int = 200
        return "OK"
    
    @restrict('DELETE')
    def _delete_unary(self, type, id, id2=None):
        thinker = h.fetch_obj(Thinker, id)

        id2 = request.params.get('id2', id2)
        obj = h.fetch_obj(unary_vars[type]['object'], id2)

        if obj in getattr(thinker, unary_vars[type]['property']):
            getattr(thinker, unary_vars[type]['property']).remove(obj)

        Session.commit()

        response.status_int = 200
        return "OK"

    @dispatch_on(DELETE='_delete_binary')
    @restrict('POST', 'PUT')
    def binary(self, type, id, id2, degree=1):
        if not h.auth.is_logged_in():
            abort(401)
        
        type = binary_vars[type]
        if type['reverse']:
            return self._thinker_evaluate(type['object'], id2, id, 
                                          degree=degree, 
                                          maxdegree=type['maxdegree'])
        else:
            return self._thinker_evaluate(type['object'], id, id2, 
                                          degree=degree, 
                                          maxdegree=type['maxdegree'])

    @restrict('DELETE')
    def _delete_binary(self, type, id, id2, degree=1):
        if not h.auth.is_logged_in():
            abort(401)

        type = binary_vars[type]

        if type['reverse']:
            return self._delete_evaluation(type['object'], id2, id)
        else:
            return self._delete_evaluation(type['object'], id, id2)
        
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
            # if only 1 result, go ahead and view that thinker
            if redirect and entity_q.count() == 1:
                print "have a q, entityq count = 1"
                c.thinker = h.fetch_obj(Thinker, entity_q.first().ID)
                c.found = True
                id = c.thinker.ID
                c.message = 'Entity edit page for thinker ' + c.thinker.name
                if request.params.get('entry_sep_dir'):
                        entry_sep_dir = request.params['entry_sep_dir']
                        if not (c.thinker.sep_dir):
                            c.thinker.sep_dir = request.params['entry_sep_dir']
                            c.sepdirnew = True
                        else:
                            c.alreadysepdir = True
                            c.entry_sep_dir = request.params['entry_sep_dir']
                return render('admin/thinker-edit.html')
            else: 
                print "That didn't work."

        if id is None:
            print "I am here"
            c.message = "Please input an entity label using the search bar to the left."
            return render ('admin/thinker-edit.html')
        else:
            c.thinker = h.fetch_obj(Thinker, id)
            c.found = True
            c.message = 'Entity edit page for thinker ' + c.thinker.name
            if request.params.get('entry_sep_dir'):
                entry_sep_dir = request.params['entry_sep_dir']
                if not (c.thinker.sep_dir):
                    c.thinker.sep_dir = request.params['entry_sep_dir']
                    c.sepdirnew = True
                else:
                    c.alreadysepdir = True 
                    c.entry_sep_dir = request.params['entry_sep_dir']
                    
            return render ('admin/thinker-edit.html') 
    
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
            thinker_add = Thinker(label)
            thinker_add.label = label
            
            #setup search string and search pattern
            lastname = thinker_add.label.split(' ').pop()
            lastname_q = Session.query(Entity)
            o = Entity.searchstring.like(lastname)
            lastname_q = lastname_q.filter(o).order_by(func.length(Entity.label))
            if lastname_q.count() == 0:
                #if there's no match currently to last name, can use last name alone as searchpattern/searchstring
                thinker_add.searchpatterns.append(lastname)
                thinker_add.searchstring = lastname
            else:
                #otherwise, we need to use the whole name for both, and reset the other pattern to full name too
                thinker_add.searchpatterns.append(label)
                thinker_add.searchstring = label
                #reset old thinker pattern to whole name too to avoid conflict
                oldthinker = h.fetch_obj(Thinker, lastname_q.first().ID)
                oldthinker.searchpatterns = [oldthinker.label]
                oldthinker.searchstring = oldthinker.label
                Session.add(oldthinker)

            if sep_dir:
                thinker_add.sep_dir = sep_dir
            c.thinker = thinker_add
            Session.add(thinker_add)
            Session.flush()
            Session.commit()
            c.found = True
            c.message = "Thinker " + c.thinker.label + " added successfully."
            return render ('admin/thinker-edit.html')
        elif action=="Modify":
            c.thinker = h.fetch_obj(Thinker, id)
            c.found = True
            changed = False
            
            searchpatterns = []
            for k, v in values.items():
                key = ""
                
                if k.startswith('searchpatterns'):
                    varname, num = k.split('.')
                    key = 'delsearchpattern.%s'%(num)
                    keyval = request.params.get(key, False)
                    if not keyval:
                        searchpatterns.append(v)
            
            if values['newsearchpattern']:
                searchpatterns.append(values['newsearchpattern'])
                changed = True
                
            #do manually edited searchpatterns first, so we don't write over them with the new default ones if the searchstring has been changed
            if c.thinker.searchpatterns != searchpatterns:
                c.thinker.searchpatterns = searchpatterns
                changed = True
            
            #set values from form
            if c.thinker.name != values['name']:
                c.thinker.name = values['name']
                changed = True
            if c.thinker.label != values['label']:
                c.thinker.name = values['label']
                changed = True
            if c.thinker.searchstring != values['searchstring']:
                c.thinker.searchstring = values['searchstring']
                changed = True
            if c.thinker.sep_dir != values['sep_dir']:
                c.thinker.sep_dir = values['sep_dir']
                changed = True
            
            if c.thinker.wiki != values['wiki']:
                c.thinker.wiki = values['wiki']
                changed = True

            if c.thinker.birth_day != values['birth_day']:
                c.thinker.birth_day = values['birth_day']
                changed = True
            c.thinker.birth_day = values['birth_day']

            if c.thinker.death_day != values['death_day']:
                c.thinker.death_day = values['death_day']
                changed = True
            
            if c.thinker.birth_month != values['birth_month']:
                c.thinker.birth_month = values['birth_month']
                changed = True
            
            if c.thinker.death_month != values['death_month']:
                c.thinker.death_month = values['death_month']
                changed = True
            
            if not (c.thinker.birth_year == values['birth_year'] + " " + values['bornbc']):
                if c.thinker.birth_year != values['birth_year']:
                    c.thinker.birth_year = values['birth_year']
                    changed = True
                if c.thinker.birth_year and values['bornbc'] and not re.search("(BC)|(AD)",c.thinker.birth_year):
                    c.thinker.birth_year = c.thinker.birth_year + " " + values['bornbc']
                    changed = True
            
            if not (c.thinker.death_year == values['death_year'] + " " + values['diedbc']):
                if c.thinker.death_year != values['death_year']:
                    c.thinker.death_year = values['death_year']
                    changed = True
                if c.thinker.death_year and values['diedbc']and not re.search("(BC)|(AD)",c.thinker.death_year):
                    c.thinker.death_year = c.thinker.death_year + " " + values['diedbc']
                    changed = True

            #commit changes
            Session.flush()
            Session.commit()
            if changed:
                c.message = "Thinker " + c.thinker.label + " modified successfully."
            else:
                c.message = "No changes detected.  Thinker " + c.thinker.label + " not modified."
            return render ('admin/thinker-edit.html')
                    
        elif action == "Delete":
            c.thinker = h.fetch_obj(Thinker, values['ID'])
            c.message = "Thinker # " + values['ID'] + " ("+ c.thinker.label + ") deleted; please search for a new entity label on the left."
            h.delete_obj(c.thinker)
            Session.flush()
            Session.commit()
            c.found = False
            return render('admin/thinker-edit.html')
    
        
    

    
