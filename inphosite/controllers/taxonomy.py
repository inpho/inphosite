from inphosite.lib.partialDelegate import PartialDelegate
from inphosite.lib.rest import restrict, dispatch_on
import pystache

import logging
from collections import defaultdict

from pylons import request, response, session, config, tmpl_context as c
from pylons.controllers.util import abort, redirect

from inphosite.controllers.entity import EntityController
from inphosite.lib.base import BaseController, render
import inphosite.lib.helpers as h
from inpho.model.idea import IdeaEvaluation
from inpho.model.taxonomy import *
from inpho.model import Session

log = logging.getLogger(__name__)

partials = PartialDelegate(config['mustache_path'])
renderer = pystache.Renderer(file_encoding='utf-8',string_encoding='utf-8',partials=partials)

class TaxonomyController(EntityController):
    _type = Node
    _controller = 'taxonomy'
    
    def __before__(self):
        response.headers['Access-Control-Allow-Origin'] = '*' 
        response.headers['Access-Control-Allow-Methods'] = '*'
        response.headers['Access-Control-Allow-Headers'] =\
            'origin, c-csrftoken, content-type, authorization, accept'
        response.headers['Access-Control-Max-Age'] = '1000'

    def view(self, id=None, filetype='html'):
        c.node = h.fetch_obj(Node, id, new_id=True)
        c.entity = c.node.idea

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

        if filetype=='json':
            response.content_type = 'application/json'
       
        # create breadcrumb html
        breadcrumbs = list()
        current = c.node.parent
        while current:
                breadcrumbs.append({'label': h.titlecase(current.label), 'url': current.url()})
                current = current.parent
        path = {'path': breadcrumbs, 'head': {'label': h.titlecase(c.node.label), 'url': c.node.url()}} 
        pathhtml = renderer.render_path(config['mustache_path']+'breadcrumbs.mustache', path)

        struct = { 'ID' : c.entity.ID, 
                  'type' : 'node',
                  'label' : h.titlecase(c.entity.label), 
                  'sep_dir' : c.entity.sep_dir,
                  'url' : c.entity.url(),
                  'wiki': c.entity.wiki,
                  'breadcrumbs': pathhtml
                  }
 
        content = {'content': renderer.render_path(config['mustache_path']+"taxonomy.mustache", struct), 'sidebar': True} 
        return renderer.render_path(config['mustache_path']+'base.mustache', content)
  
    def list(self, filetype='html'):
        c.nodes = Session.query(Node).all()
        
        entity_q = Session.query(Node)
        entity_q = entity_q.limit(request.params.get('limit', None))
        
        c.query = request.params.get('q', '')
        c.sep = request.params.get('sep', '')

        if request.params.get('sep_filter', False):
            entity_q = entity_q.filter(Entity.sep_dir != '')
        
        if c.sep:
            entity_q = entity_q.filter(Entity.sep_dir == c.sep) 

        if c.query:
            o = or_(Entity.label.like(c.query+'%'), Entity.label.like('% '+c.query+'%'))
            entity_q = entity_q.filter(o).order_by(func.length(Entity.label))
        
        if filetype=='json':
            response.content_type = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*' 

        c.entities = entity_q.all()
        if request.params.get('redirect', False) and len(c.entities) == 1: 
            h.redirect(h.url(controller=self._controller, action='view', 
                             filetype=filetype, id=c.entities[0].ID), 
                       code=302)
        else:
            return render('{type}/{type}-list.'.format(type=self._controller) 
                          + filetype)


        

    def graph(self, id=None, filetype='josn'):
        abort(404)
