import logging

from pylons import request, response, session, tmpl_context as c
import inphosite.lib.helpers as h
from pylons.controllers.util import abort, redirect

# import decorators
from pylons.decorators import validate
from pylons.decorators.cache import beaker_cache
from inphosite.lib.rest import restrict, dispatch_on
from inphosite.lib import auth

# import inphosite information
from inphosite.lib.base import BaseController, render
from inphosite.controllers.entity import EntityController

from inpho.model import Entity
from inpho.model.idea import *
from inpho.model.taxonomy import *
from inpho.model import Session
import webhelpers.paginate as paginate

from sqlalchemy import or_
from sqlalchemy.sql.expression import func
from sqlalchemy.exc import IntegrityError
log = logging.getLogger(__name__)

import formencode
from formencode import htmlfill, validators, FancyValidator
from formencode.schema import Schema
from formencode import variabledecode
    
import simplejson
import re
import time
from collections import defaultdict
import urllib2

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

#Schema for validating form data from "edit idea" admin interface
#class IdeaSchema(Schema):
#    idea_id = validators.String(not_empty=True)
#    idea_label = validators.String(not_empty=True)
#    idea_searchpattern = validators.String()
#    idea_searchstring = validators.String()
#    idea_sep_dir = validators.String()

class IdeaController(EntityController):
    _type = Idea
    _controller = 'idea'

    def data_integrity(self, filetype="html", redirect=False):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        idea_q = Session.query(Idea)
        c.ideas = list(idea_q)

        # Missing searchstring
        c.missing_string = [idea for idea in c.ideas
                            if not getattr(idea, 'searchstring')]
        
        # Missing searchpattern
        c.missing_pattern = [idea for idea in c.ideas
                             if not getattr(idea, 'searchpattern')]
        
        # Missing sep_dir
        c.missing_sep_dir = [idea for idea in c.ideas
                             if not getattr(idea, 'sep_dir')]
            
        # Duplicates
        c.duplicate = []
        c.sorted_ideas = sorted(c.ideas, key=lambda idea: idea.label)
        for i in range(len(c.sorted_ideas) - 1):
            if c.sorted_ideas[i].label == c.sorted_ideas[i+1].label:
                c.duplicate.append(c.sorted_ideas[i])
                c.duplicate.append(c.sorted_ideas[i+1])
                    
        return render('idea/data_integrity.%s' % filetype)

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
        
        if filetype=='json':
            response.content_type = 'application/json'

        # Check for query
        if request.params.get('q'):
            q = request.params['q']
            c.query = q
            o = or_(Idea.label.like(q+'%'), Idea.label.like('% '+q+'%'))
            idea_q = idea_q.filter(o).order_by(Idea.entropy.desc())
            # if only 1 result, go ahead and view that idea
            if redirect and idea_q.count() == 1:
                h.redirect(h.url(controller='idea', action='view', id=idea_q.first().ID,filetype=filetype))
        
        #TODO: Error handling - we shouldn't have multiple results
        if request.params.get('sep'):
            idea_q = idea_q.filter(Idea.sep_dir == request.params['sep'])
            c.sep = request.params['sep']
            # if only 1 result, go ahead and view that idea
            if redirect and idea_q.count() == 1:
                h.redirect(h.url(controller='idea', action='view', id=idea_q.first().ID,filetype=filetype))
            elif idea_q.count() == 0:
                h.redirect(h.url(controller='entity', action='list', filetype=filetype, sep=request.params['sep'], redirect=redirect))
        
        '''
        ### This block of code filters out nodes and instances, reduces occurances of 'ism's
        ### It is not currently necessary and causes an error in the middle 'elif' block.
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
                # ISSUE!!! This union causes an error when executing the query!... why?
                idea_q = idea_q.union(instance_q)
        elif instance_param:
            idea_q = instance_q
        '''
        
        c.total = idea_q.count()
        c.entities = idea_q.limit(limit)

        return render('idea/idea-list.' + filetype)



    ######################
    ### PROPERTY LISTS ###
    ######################

    #@beaker_cache(expire=300, type='memory', query_args=False)
    def _list_property(self, property, id, filetype='html', limit=False, sep_filter=False, type='idea'):
        c.idea = h.fetch_obj(Idea, id)
         
        limit = int(request.params.get('limit', limit))
        start = int(request.params.get('start', 0))
        sep_filter = request.params.get('sep_filter', sep_filter)
        property = getattr(c.idea, property)
        if sep_filter:
            property = property.filter(Entity.sep_dir != '')
        
        # TODO: Fix hacky workaround for the AppenderQuery vs. Relationship
        # property issue - upgrading SQLAlchemy may fix this by allowing us to
        # use len() in a smart way.
        try:
            c.total = property.count()
        except TypeError:
            c.total = len(property)
            
         
        if limit:
            property = property[start:start+limit]
        
        c.entities = property
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

        c.entities = []
        c.entities.extend(parents)
        c.entities.extend(children)
        c.entities.extend(siblings) 

        if sep_filter:
            c.entities = [i.idea for i in c.entities if i.idea.sep_dir]
        else:
            c.entities = [i.idea for i in c.entities]

        if c.idea in c.entities: 
            c.entities.remove(c.idea)
        
        c.total = len(c.entities)

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
        
        # TODO: Fix hacky workaround for the AppenderQuery vs. Relationship
        # property issue - upgrading SQLAlchemy may fix this by allowing us to
        # use len() in a smart way.
        try:
            c.total = property.count()
        except TypeError:
            c.total = len(property)
        
        c.entities = property
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

        # IDEA GETTIN'
        c.entity = h.fetch_obj(Idea, id, new_id=True)

        if filetype=='json':
            response.content_type = 'application/json'
            return c.entity.json()

        c.count = len(c.entity.nodes) + len(c.entity.instance_of) + len(c.entity.links_to)
        c.nodes = list()
        if c.entity.nodes:
            c.nodes.extend(c.entity.nodes[:])
        for idea in c.entity.instance_of:
            for node in idea.nodes:
                c.nodes.append(node)
        for idea in c.entity.links_to:
            for node in idea.nodes:
                c.nodes.append(node)

        if c.entity.nodes:
            c.node = c.entity.nodes[0]
        elif c.entity.instance_of:
            c.node = c.entity.instance_of[0]
            # just in case of data corruption
            # instance_of points to idea, need node
            if c.node.nodes:
                c.node = c.node.nodes[0]
        elif c.entity.links_to:
            c.node = c.entity.links_to[0]
            # just in case of data corruption
            # links_to point to idea, need node
            if c.node.nodes:
                c.node = c.node.nodes[0]
        else:
            c.node = None
        
        # EVALUATION PROCESSING
        c.evaluations = defaultdict(lambda: (-1, -1))
        identity = request.environ.get('repoze.who.identity')
        if identity:
            c.uid = identity['user'].ID
            #c.evaluations = Session.query(IdeaEvaluation).filter_by(ante_id=c.entity.ID, uid=uid).all()
            eval_q = Session.query(IdeaEvaluation.cons_id, 
                                   IdeaEvaluation.generality, 
                                   IdeaEvaluation.relatedness)
            eval_q = eval_q.filter_by(uid=c.uid, ante_id=c.entity.ID)
            evals = eval_q.all()
            evals = map(lambda x: (x[0], (x[1], x[2])), evals)
            c.evaluations.update(dict(evals))

        else:
            c.uid = None

        # REDIRECTING
        if redirect and len(c.entity.nodes) == 1:
            h.redirect(h.url(controller='taxonomy', action='view',
                             id=c.entity.nodes[0].ID,filetype=filetype), code=303)

        return render('idea/idea.' + filetype)

    def panel(self, id, id2):
        evaluation = self.evaluation(id, id2)
        search = self.search(id, id2)

        # just in case evaluation gave a 501
        response.status_int = 200
        return evaluation + search

    def evaluation(self, id, id2):
        c.entity = h.fetch_obj(Idea, id)
        c.entity2 = h.fetch_obj(Entity, id2)
        if isinstance(c.entity2, Node):
            c.entity2 = c.entity2.idea
            id2 = c.entity2.ID
        if not isinstance(c.entity2, Idea):
            # no evaluation implemented
            response.status_int = 501

            return ''

        c.edit = True
        c.alert = request.params.get('alert', True)
       
        # retrieve evaluation for pair
        c.generality = int(request.params.get('generality', -1))
        c.relatedness = int(request.params.get('relatedness', -1))
        
        # retrieve user information
        identity = request.environ.get('repoze.who.identity')
        c.uid = None if not identity else identity['user'].ID
        
        #TODO: Place cookie auth here
        try:
            cookie = request.params.get('cookieAuth', 'null')
            username = h.auth.get_username_from_cookie(cookie) or ''
            user = h.get_user(username)
            if user is not None:
                c.uid = user.ID

        except ValueError:
            # invalid IP, abort
            abort(403)

        # use the user's evaluation if present, otherwise a null eval
        if c.uid and (c.generality == -1 or c.relatedness == -1):
            eval_q = Session.query(IdeaEvaluation.generality, 
                                       IdeaEvaluation.relatedness)
            eval_q = eval_q.filter_by(uid=c.uid, ante_id=id, cons_id=id2)

            c.generality, c.relatedness = eval_q.first() or\
                (int(request.params.get('generality', -1)), 
                 int(request.params.get('relatedness', -1)))


        if c.relatedness != -1:
            c.edit = request.params.get('edit', False)

        return render('idea/eval.html')

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
    def update(self, id=None):
        terms = ['sep_dir', 'searchstring', 'label', 'wiki']
        super(IdeaController, self).update(id, terms)

    @restrict('POST')
    def create(self):
        valid_params = ["sep_dir", "searchstring", "searchpattern", 'wiki']
        EntityController.create(self, entity_type=1, valid_params=valid_params)
        

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

        response.headers['Access-Control-Allow-Origin'] = '*' 

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
            uid = user.ID if user else abort(403)
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
    def _evaluate(self, evaltype, id, id2=None, uid=None, username=None,
                  degree=-1, maxdegree=4, errors=0):
        """
        Function to submit an evaluation. Takes a POST request containing the consequesnt id and 
        all or none of: generality, relatedness, hyperrank, hyporank.
        """
        id2 = request.params.get('id2', id2)
        uid = request.params.get('uid', uid)
        try:
            username = h.auth.get_username_from_cookie(request.params.get('cookieAuth', ''))
        except ValueError:
            # invalid IP, abort
            username = None

        print "grabbing eval for", username, uid

        if request.environ.get('REMOTE_USER', False):
            username = request.environ.get('REMOTE_USER', username)
            evaluation = self._get_evaluation(id, id2, None, username)
        elif username:
            evaluation = self._get_evaluation(id, id2, None, username)
        else:
            evaluation = self._get_anon_evaluation(id, id2, request.environ.get('REMOTE_ADDR', '0.0.0.0'))

        # Populate proper generality, relatedness, hyperrank and hyporank values
        evaluation.time = time.time()

        # Attempt to convert to integers, if unable, throw HTTP 400
        try: 
            setattr(evaluation, evaltype, 
                    int(request.params.get('degree', getattr(evaluation, evaltype))))
        except TypeError:
            abort(400)

        # Create and commit evaluation
        try:
            Session.flush()
            Session.commit()
        except IntegrityError:
            Session.rollback()
            if not errors:
                self._evaluate(evaltype, id, id2, username, 
                               degree, maxdegree, errors+1)

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
        #if evaluation.generality == -1 and evaluation.relatedness == -1:
        #    h.delete_obj(evaluation)
        
        Session.flush()
        Session.commit()
        response.status_int = 200
        return "OK"


        

    # The cross referencing engine
    def crossref(self, id):
        c.idea = h.fetch_obj(Idea, id, new_id=True)
        return render('idea/idea-ref.html')

