import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect

from inphosite.lib.base import BaseController, render

from inphosite.model.idea import IdeaEvaluation
from inphosite.model.taxonomy import *
from inphosite.model.meta import Session
import inphosite.lib.helpers as h
from collections import defaultdict

log = logging.getLogger(__name__)

class TaxonomyController(BaseController):
    def list(self, filetype='html', redirect=False):
        node_q = Session.query(Node)
            
        # check for query
        if request.params.get('q'):
            node_q = node_q.filter(Node.name.like(u'%'+request.params['q']+'%'))
            # if only 1 result, go ahead and view that node
            if redirect and node_q.count() == 1:
                h.redirect(h.url(controller='taxonomy', action='view',
                                 id=node_q.first().ID, filetype=filetype))
                
        if filetype=='html':
            c.nodes = Session.query(Node).filter(Node.parent_id == None).order_by("name").all()
            return render('taxonomy/node-list.html')
        else:
            c.nodes = node_q.all()
            return render('taxonomy/node-list.%s' % filetype)

    def view(self, id=None, filetype='html'):
        c.node = h.fetch_obj(Node, id, new_id=True)
        c.idea = c.node.idea

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

        return render('taxonomy/node.%s' % filetype)
        #if filetype=='html':
        #    c.idea = c.node.idea
        #    return render('idea/idea.html')
        #else:
        #    return render('taxonomy/node.%s' % filetype)
    
    def graph(self, id=None, filetype='josn'):
        abort(404)
