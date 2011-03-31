import logging

from pylons import request, response, session, tmpl_context as c
import inphosite.lib.helpers as h
import inphosite.lib.searchstring as s
from pylons.controllers.util import abort, redirect

# import decorators
from pylons.decorators import validate
from pylons.decorators.cache import beaker_cache
from inphosite.lib.rest import restrict, dispatch_on
from inphosite.lib import auth

# import inphosite information
from inphosite.lib.base import BaseController, render

from inphosite.model import Entity
from inphosite.model.idea import *
from inphosite.model.taxonomy import *
from inphosite.model.meta import Session
import webhelpers.paginate as paginate

from sqlalchemy import or_
from sqlalchemy.sql.expression import func
log = logging.getLogger(__name__)

import formencode
from formencode import htmlfill, validators, FancyValidator
from formencode.schema import Schema
from formencode import variabledecode
    
import simplejson
import re
from collections import defaultdict

#Schema for validating form data from "edit idea" admin interface
#class IdeaSchema(Schema):
#    idea_id = validators.String(not_empty=True)
#    idea_label = validators.String(not_empty=True)
#    idea_searchpattern = validators.String()
#    idea_searchstring = validators.String()
#    idea_sep_dir = validators.String()

class IdeaController(BaseController):
    #@beaker_cache(expire=300, type='memory', query_args=True)
    def list(self, filetype='html'):
        redirect = request.params.get('redirect', False)
        limit = request.params.get('limit', None)
        idea_q = Session.query(Idea)
        c.query = ''
        c.sep = ''

        #c.nodes = Session.query(Node).filter(Node.parent_id == None).order_by("name").all()
        if request.params.get('sep_filter'):
            idea_q = idea_q.filter(Idea.sep_dir != '')
        
        # Check for query
        if request.params.get('q'):
            q = request.params['q']
            c.query = q
            o = or_(Idea.label.like(q+'%'), Idea.label.like('% '+q+'%'))
            idea_q = idea_q.filter(o).order_by(Idea.entropy.desc())
            # if only 1 result, go ahead and view that idea
            if redirect and idea_q.count() == 1:
                h.redirect(h.url(controller='idea', action='view', id=idea_q.first().ID,filetype=filetype))
            else:
                c.ideas = idea_q.limit(limit)
                return render('idea/idea-list.' + filetype)
        
        #TODO: Error handling - we shouldn't have multiple results
        if request.params.get('sep'):
            idea_q = idea_q.filter(Idea.sep_dir == request.params['sep'])
            c.sep = request.params['sep']
            # if only 1 result, go ahead and view that idea
            if redirect and idea_q.count() == 1:
                h.redirect(h.url(controller='idea', action='view', id=idea_q.first().ID,filetype=filetype))
            elif idea_q.count() == 0:
                h.redirect(h.url(controller='entity', action='list', filetype=filetype, sep=request.params['sep'], redirect=redirect))
            else:
                c.ideas = idea_q.limit(limit)
                return render('idea/idea-list.' + filetype)
        
        all_param = request.params.get('all', False)
        node_param = request.params.get('nodes', True)
        instance_param = request.params.get('instances', True)
        
        node_q = idea_q.join((Node,Node.concept_id==Idea.ID))
        instance_q = idea_q.join(Instance.idea)

        if all_param:
            idea_q = idea_q
            if not node_param:
                idea_q = idea_q.except_(node_q)
            if not instance_param:
                idea_q = idea_q.except_(instance_q)
        elif node_param:
            idea_q = node_q
            if instance_param:
                idea_q = idea_q.union(instance_q)
        elif instance_param:
            idea_q = instance_q

        c.ideas = idea_q.limit(limit)
        return render('idea/idea-list.' + filetype)

    def list_json(self):
        response.content_type = 'application/json'
        return self.list('json')



    ######################
    ### PROPERTY LISTS ###
    ######################

    #@beaker_cache(expire=300, type='memory', query_args=False)
    def _list_property(self, property, id, filetype='html', limit=False, sep_filter=False, type='idea'):
        c.idea = h.fetch_obj(Idea, id)
         
        limit = request.params.get('limit', limit)
        sep_filter = request.params.get('sep_filter', sep_filter)
        property = getattr(c.idea, property)
        if sep_filter:
            property = property.filter(Entity.sep_dir != '')
        if limit:
            property = property[0:limit-1]
        
        c.ideas = property
        c.nodes = Session.query(Node).filter(Node.parent_id == None).order_by("name").all()
        return render('%s/%s-list.%s' %(type, type, filetype))

    def instances(self, id=None, filetype='html', limit=False, sep_filter=False):
        return self._list_property('instances', id, filetype, limit, sep_filter)
    
    def occurrences(self, id=None, filetype='html', limit=False, sep_filter=False):
        return self._list_property('occurrences', id, filetype, limit, sep_filter)

    def links(self, id=None, filetype='html', limit=False, sep_filter=False):
        return self._list_property('links', id, filetype, limit, sep_filter)

    def hyponyms(self, id=None, filetype='html', limit=20, sep_filter=False):
        return self._list_property('hyponyms', id, filetype, limit, sep_filter)

    def related(self, id=None, filetype='html', limit=20, sep_filter=False):
        return self._list_property('related', id, filetype, limit, sep_filter)
    
    def related_thinkers(self, id=None, filetype='html', limit=20, sep_filter=False):
        return self._list_property('related_thinkers', id, filetype, limit, sep_filter)
    
    def occurrences(self, id=None, filetype='html', limit=20, sep_filter=False):
        return self._list_property('occurrences', id, filetype, limit, sep_filter)
    
    def thinker_occurrences(self, id=None, filetype='html', limit=20, sep_filter=False):
        return self._list_property('thinker_occurrences', id, filetype, limit, sep_filter)
    
    def evaluated(self, id=None, filetype='html', limit=20, sep_filter=False):
        return self._list_property('evaluated', id, filetype, limit, sep_filter)

    #@beaker_cache(expire=300, type='memory', query_args=False)
    def first_order(self, id=None, filetype='html', limit=False,
                    sep_filter=False):

        c.idea = h.fetch_obj(Idea, id)
         
        limit = request.params.get('limit', limit)
        sep_filter = request.params.get('sep_filter', sep_filter)
        children = [child for ins in c.idea.nodes 
                        for child in ins.children] 
        parents = [ins.parent for ins in c.idea.nodes if ins.parent]
        siblings = [child for ins in parents
                          for child in ins.children]

        c.ideas = []
        c.ideas.extend(parents)
        c.ideas.extend(children)
        c.ideas.extend(siblings) 

        if sep_filter:
            c.ideas = [i.idea for i in c.ideas if i.idea.sep_dir]
        else:
            c.ideas = [i.idea for i in c.ideas]

        if c.idea in c.ideas: 
            c.ideas.remove(c.idea)

        #c.nodes = Session.query(Node).filter_by(parent_id=0).order_by("Name")
        return render('idea/idea-list.' + filetype)


    #@beaker_cache(expire=300, type='memory', query_args=True)
    def classes(self, id=None, filetype='html', limit=False, sep_filter=False):
        c.idea = h.fetch_obj(Idea, id)
         
        limit = request.params.get('limit', limit)
        sep_filter = request.params.get('sep_filter', sep_filter)
        property = [child for ins in c.idea.nodes 
                        for child in ins.children] 
        if limit:
            property = property[1:limit]
        if sep_filter:
            property = [i.idea for i in property if i.idea.sep_dir]
        
        c.ideas = property
        #c.nodes = Session.query(Node).filter_by(parent_id=0).order_by("Name")
        return render('idea/idea-list.' + filetype)


    ############
    ### VIEW ###
    ############

    #@beaker_cache(expire=60, type='memory', query_args=True)
    def view(self, id=None, filetype='html'):
        if filetype == 'html':
            redirect = request.params.get('redirect', True)
        else:
            redirect = request.params.get('redirect', False)

        sep_filter = request.params.get('sep_filter', False) 
        c.sep_filter = sep_filter

        c.idea = h.fetch_obj(Idea, id, new_id=True)

        c.count = len(c.idea.nodes) + len(c.idea.instance_of) + len(c.idea.links_to)
        if len(c.idea.nodes) > 0:
            c.node = c.idea.nodes[0]
        elif len(c.idea.instance_of) > 0:
            c.node = c.idea.instance_of[0]
        else:
            c.node = None
        
        c.evaluations = defaultdict(lambda: (-1, -1))
        identity = request.environ.get('repoze.who.identity')
        if identity:
            c.uid = identity['user'].ID
            #c.evaluations = Session.query(IdeaEvaluation).filter_by(ante_id=c.idea.ID, uid=uid).all()
            eval_q = Session.query(IdeaEvaluation.cons_id, 
                                   IdeaEvaluation.generality, 
                                   IdeaEvaluation.relatedness)
            eval_q = eval_q.filter_by(uid=c.uid, ante_id=c.idea.ID)
            evals = eval_q.all()
            evals = map(lambda x: (x[0], (x[1], x[2])), evals)
            c.evaluations.update(dict(evals))

        else:
            c.uid = None


        if redirect and len(c.idea.nodes) == 1:
            h.redirect(h.url(controller='taxonomy', action='view',
            id=c.idea.nodes[0].ID,filetype=filetype), code=303)

        return render('idea/idea.' + filetype)

    def graph(self, id=None, filetype='nwb', limit=False):
        c.sep_filter = request.params.get('sep_filter', False) 
        c.n = int(request.params.get('n', 8))
        c.recur = int(request.params.get('recur', 3))
        c.thresh = float(request.params.get('thresh', 0))

        c.idea = h.fetch_obj(Idea, id, new_id=True)
        
        return render('idea/graph.' + filetype)
    
    def graph_all(self, filetype='html', limit=False):
        sep_filter = request.params.get('sep_filter', False) 
        c.sep_filter = sep_filter
        idea_q = Session.query(Idea)
        c.ideas = idea_q.all()
        
        edge_q =\
        Session.query(IdeaGraphEdge).order_by(IdeaGraphEdge.jweight.desc()).limit(3*len(c.ideas))
        c.edges = edge_q.all()
        
        return render('idea/graph_all.' + filetype)
        
    #UPDATE
    @restrict('PUT')
    def update(self, id=None):
        if not h.auth.is_logged_in():
            abort(401)

        idea = h.fetch_obj(Idea, id, new_id=True)
        terms = ['sep_dir'] 

        h.update_obj(idea, terms, request.params)

        return self.view(id)

    
    #DELETE
    @restrict('DELETE')
    def delete(self, id=None):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        idea = h.fetch_obj(Idea, id, new_id=True)
        
        h.delete_obj(idea)

        # Issue an HTTP success
        response.status_int = 200
        return "OK"

    @restrict('POST')
    def create(self):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        valid_params = ["sep_dir", "searchstring", "searchpattern"]
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

        idea = Idea(label)
        Session.add(idea)
        Session.flush()

        # Issue an HTTP success
        response.status_int = 302
        response.headers['location'] = h.url(controller='idea',
                                                 action='view', id=idea.ID)
        return "Moved temporarily"



    ##################
    ### EVALUATION ###
    ##################

    # render the editing GUI
    def evaluate(self, id=None):
        if not h.auth.is_logged_in():
            abort(401)

        c.idea = h.fetch_obj(Idea, id, new_id=True)
        node_q = Session.query(Node).filter_by(concept_id=id)
        c.node = node_q.first()
        if request.environ.get('REMOTE_USER', False):
            user = h.get_user(request.environ['REMOTE_USER'])

            sq = Session.query(IdeaEvaluation.cons_id)
            sq = sq.filter(IdeaEvaluation.ante==c.idea)
            sq = sq.filter(IdeaEvaluation.uid==user.ID)
            sq = sq.subquery()

            to_evaluate = c.idea.related.outerjoin((sq, Idea.ID==sq.c.cons_id))
            to_evaluate = to_evaluate.filter(sq.c.cons_id==None)

        else:
            to_evaluate = c.idea.related

        c.paginator = paginate.Page(
            to_evaluate,
            page=int(request.params.get('page', 1)),
            items_per_page=10,
            controller='idea',
            action='edit',
            id=id
        )


        return render('idea/idea-edit.html')

    def _get_evaluation(self, id, id2, uid=None, username=None, 
                        autoCreate=True):
        idea1 = h.fetch_obj(Idea, id, new_id=True)
        idea2 = h.fetch_obj(Idea, id2, new_id=True)

        # Get user information
        if uid:
            uid = h.fetch_obj(User, uid).ID
        elif username:
            user = h.get_user(username)
            uid = user.ID if user else abort(404)
        else:
            uid = h.get_user(request.environ['REMOTE_USER']).ID

        evaluation_q = Session.query(IdeaEvaluation)
        evaluation = evaluation_q.filter_by(ante_id=id, cons_id=id2, uid=uid).first()

        # if an evaluation does not yet exist, create one
        if autoCreate and not evaluation:
            evaluation = IdeaEvaluation(id, id2, uid)
            Session.add(evaluation)

        return evaluation
    
    def _get_anon_evaluation(self, id, id2, ip, autoCreate=True):
        idea1 = h.fetch_obj(Idea, id, new_id=True)
        idea2 = h.fetch_obj(Idea, id2, new_id=True)

        evaluation_q = Session.query(AnonIdeaEvaluation)
        evaluation = evaluation_q.filter_by(ante_id=id, cons_id=id2, ip=ip).first()

        # if an evaluation does not yet exist, create one
        if autoCreate and not evaluation:
            evaluation = AnonIdeaEvaluation(id, id2,ip)
            Session.add(evaluation)

        return evaluation


    
    @dispatch_on(DELETE='_delete_relatedness')
    @restrict('POST', 'PUT')
    def relatedness(self, id=None, id2=None, degree=1):
        return self._evaluate('relatedness', id, id2, 
                              degree=degree, maxdegree=4)

    @restrict('DELETE')
    def _delete_relatedness(self, id=None, id2=None, degree=1):
        if not h.auth.is_logged_in():
            abort(401)
        return self._delete_evaluation('relatedness', id, id2) 

    @dispatch_on(DELETE='_delete_generality')
    @restrict('POST', 'PUT')
    def generality(self, id=None, id2=None, degree=1):
        return self._evaluate('generality', id, id2, 
                              degree=degree, maxdegree=4)
    @restrict('DELETE')
    def _delete_generality(self, id=None, id2=None, degree=1):
        if not h.auth.is_logged_in():
            abort(401)
        return self._delete_evaluation('generality', id, id2) 

    # create new evaluation
    @dispatch_on(DELETE='delete_evaluation')
    @restrict('POST', 'PUT')
    def _evaluate(self, evaltype, id, id2=None, uid=None, username=None, degree=-1, maxdegree=4):
        """
        Function to submit an evaluation. Takes a POST request containing the consequesnt id and 
        all or none of: generality, relatedness, hyperrank, hyporank.
        """
        if not h.auth.is_logged_in():
            abort(401)

        id2 = request.params.get('id2', id2)
        uid = request.params.get('uid', uid)
        username = request.environ.get('REMOTE_USER', username)

        print "grabbing eval for", username, uid

        if request.environ.get('REMOTE_USER', False):
            evaluation = self._get_evaluation(id, id2, None, username)
        else:
            evaluation = self._get_anon_evaluation(id, id2, request.environ.get('REMOTE_ADDR', '0.0.0.0'))

        # Populate proper generality, relatedness, hyperrank and hyporank values
        # Attempt to convert to integers, if unable, throw HTTP 400
        try: 
            setattr(evaluation, evaltype, 
                    int(request.params.get('degree', getattr(evaluation, evaltype))))
        except TypeError:
            abort(400)


        # Create and commit evaluation
        Session.flush()
        Session.commit()

        # Issue an HTTP success
        response.status_int = 200
        return "OK"

    @restrict('DELETE')
    def _delete_evaluation(self, evaltype, id, id2, uid=None, username=None):
        if not h.auth.is_logged_in():
            abort(401)

        id2 = request.params.get('id2', id2)
        uid = request.params.get('uid', uid)
        username = request.params.get('username', username)
        evaluation = self._get_evaluation(id, id2, uid, username, autoCreate=False)
        
        if not evaluation:
            abort(404)

        current_uid = h.get_user(request.environ['REMOTE_USER']).ID
        if evaluation.uid != current_uid or not h.auth.is_admin():
            abort(401)

        setattr(evaluation, evaltype, -1)

        # Delete evaluation if this eliminates both settings, new db schema
        # will eliminate this need
        if evaluation.generality == -1 and evaluation.relatedness == -1:
            h.delete_obj(evaluation)
        else:
            # save change in evaluation
            Session.flush()
        Session.commit()
        response.status_int = 200
        return "OK"


        

    # The cross referencing engine
    def crossref(self, id):
        c.idea = h.fetch_obj(Idea, id, new_id=True)
        return render('idea/idea-ref.html')


    # The admin interface for ideas
    # fix eventually such that if there is no id, it does a list; if there is a match, it goes to the edit page
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
                c.idea = h.fetch_obj(Idea, entity_q.first().ID)
                c.found = True
                id = c.idea.ID
                c.message = 'Entity edit page for idea ' + c.idea.label
                if request.params.get('entry_sep_dir'):
                        entry_sep_dir = request.params['entry_sep_dir']
                        if not (c.idea.sep_dir):
                            c.idea.sep_dir = request.params['entry_sep_dir']
                            c.sepdirnew = True
                        else:
                            c.alreadysepdir = True
                            c.entry_sep_dir = request.params['entry_sep_dir']
                #set up c.search_string_list which will be used to structure intersection/union search pattern option
                c.search_string_list = c.idea.setup_SSL()
                if re.search(' and ', c.idea.label):
                    c.search_pattern_list = ['union', 'intersection']
                return render ('admin/idea-edit.html') 
            elif redirect and entity_q.count() == 0:
                c.message = "No match found for your search; if you would like to add your idea, please enter its label and sepdir into the field below."
                c.new = True
                c.prevvalue = q
                return render ('admin/idea-edit.html') 

            else:
                return ('No exact match for your search; please click "back" and try again.')

        if id is None:
            print "I am here"
            c.message = "Please input an idea using the search bar to the left."
            return render ('admin/idea-edit.html')
        else:
            c.idea = h.fetch_obj(Idea, id)
            c.found = True
            c.message = 'Entity edit page for idea ' + c.idea.label
            
            if request.params.get('entry_sep_dir'):
                entry_sep_dir = request.params['entry_sep_dir']
                if not (c.idea.sep_dir):
                    c.idea.sep_dir = request.params['entry_sep_dir']
                    c.sepdirnew = True
                else:
                    c.alreadysepdir = True
                    c.entry_sep_dir = request.params['entry_sep_dir']

            #set up c.search_string_list which will be used to structure intersection/union search pattern option
            c.search_string_list = c.idea.setup_SSL()
            
            print "c.idea.searchpattern is " + c.idea.searchpattern

            return render ('admin/idea-edit.html') 

    def process(self):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)
            
        c.sepdirnew = False
        c.alreadysepdir = False

        action = request.params.get('action', None)
        action2 = request.params.get('action2', None)
        if action2:
            action = action2
        q = request.params.get('label', None)
        label = q
        searchpattern = request.params.get('searchpattern', None)
        searchstring = request.params.get('searchstring', None)
        sep_dir = request.params.get('sep_dir', None)
        ioru = request.params.get('ioru', 'u')
        
        print "***"
        print "sep_dir is " 
        print sep_dir
        print "and label is "
        print q
        print "***"
        
        values = dict(request.params)
        
        c.found = values.get('found', False)
        c.custom = values.get('custom', False)
        c.new = values.get('new', False)
    
        #ADD ACTION -- add a new entity (id/label cannot already exist)
        if action=='Add':
            #lowercase label and check to see whether it is valid
            #if so commit idea with standard pluralizations as searchpattern and give user a message that add was successful
            q = q.lower()
 
            #check to see whether label already exists
            idea_q = Session.query(Idea)
            # Check for query
            o = Idea.label.like(q)
            idea_q = idea_q.filter(o)
                        
            # if 0 results, proceed to add idea
            if idea_q.count() == 0:
                print "***action add, idea q count == 0"
                #if no exact match for label, create new object with that label to add
                idea_add = Idea(q)

                #add searchstring = label
                idea_add.searchstring = q

                #add pluralizations to existing searchpatterns
                idea_add.searchpatterns = idea_add.pluralize()

                
                #setup the search string list
                c.idea = idea_add
                c.search_string_list = c.idea.setup_SSL()
                
                #setup sep_dir if present
                if sep_dir:
                    c.idea.sep_dir = sep_dir
                
                #commit
                #take user to disambiguation page if the label contains an 'and'
                #otherwise, commit idea
                Session.add(idea_add)
                Session.flush()
                Session.commit()
                c.found = True
                something = 1
                
            else:
                #already a match; give user error message that they should edit the preexisting page, and send them back to the submit idea
                #for edit page
                print "****action add, idea_q.count() not equal 0"
                c.message = "Idea with that name already exists in database; please edit the existing entry (returned below) or try a new label."
                c.idea = idea_q.first()
                c.search_string_list = c.idea.setup_SSL()
                return render('admin/idea-edit.html')
            
            c.message = "Idea added successfully."
            return render('admin/idea-edit.html')

        #Modify action -- edit an existing entry, id must exist
        elif action == 'Modify':
            #retrieve entity corresponding to id
            c.idea = h.fetch_obj(Idea, values['ID'])
            changed = False
            #generate searchpattern from searchstring if not already provided; current value stored in searchpattern, generate from searchstring if null


            #update parameters with form values
            if c.idea.sep_dir != values['sep_dir']:
                c.idea.sep_dir = values['sep_dir']
                changed = True
            
            if c.idea.label != label:
                c.idea.label = label
                changed = True
                
            if not c.custom:
                if c.idea.searchstring != s.convertSS(searchstring, ioru)[0]:
                    c.idea.searchstring = s.convertSS(searchstring, ioru)[0]
                    
                    #add default pluralizations to searchpatterns
                    for label in c.idea.pluralize():
                        if label not in c.idea.searchpatterns:
                            c.idea.searchpatterns.append(label)
                    changed = True
            else:
                
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
                    
                #do manually edited searchcpatterns first, so we don't write over them with the new default ones if the searchstring has been changed
                if c.idea.searchpatterns != searchpatterns:
                    c.idea.searchpatterns = searchpatterns
                    changed = True
                if c.idea.searchstring != searchstring:
                    c.idea.searchstring = searchstring
                    
                    #add default pluralizations for new searchstring as well
                    for label in c.idea.pluralize():
                        if label not in c.idea.searchpatterns:
                            c.idea.searchpatterns.append(label)
                    changed = True

            #make sure that searchpattern and searchstring are not shared by another entity
            #print "searchpatterns is " 
            #print searchpatterns
            #print "c.idea.searchpatterns is"
            #print c.idea.searchpatterns

            #commit changes
            Session.flush()
            Session.commit()

            #return success message
            if changed == True:
                c.message = "Idea modified successfully."
            else:
                c.message = "No change required; idea not modified."
            c.found = True
            c.search_string_list = c.idea.setup_SSL()

            #prepare form
            return render('admin/idea-edit.html')


        #Delete action -- Delete an existing entity (id must exist)
        elif action=='Delete':
            c.idea = h.fetch_obj(Idea, values['ID'])
            c.message = "Idea # " + values['ID'] + " ("+ c.idea.label + ") deleted; please search for a new entity label on the left."
            h.delete_obj(c.idea)
            Session.flush()
            Session.commit()
            return render('admin/idea-edit.html')

        #use custom searchstring action
        elif action=='Use Custom Searchstring/Searchpattern':
            #toggle the c.custom to True and re-render form with htmlfill
            c.custom = True
            c.idea = h.fetch_obj(Idea, values['ID'])
            c.found = True
            c.message = 'Enter custom searchstring for ' + c.idea.label + "."
            return render('admin/idea-edit.html')

        #use standard searchstring action
        elif action=='Use Standard Searchstring/Searchpattern':
            #toggle the c.custom to False and re-render form with htmlfill		
            c.custom = False
            c.idea = h.fetch_obj(Idea, values['ID'])
            c.found = True
            c.search_string_list = c.idea.setup_SSL()
            c.message = 'Now displaying standard searchstring options for ' + c.idea.label + "."
            return render('admin/idea-edit.html')

        else:
            raise Exception('I don\'t know how you got here, but you shouldn\'t be here...please start at the main page.  Invalid action %s'%action)
