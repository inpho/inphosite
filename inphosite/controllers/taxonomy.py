import logging
from collections import defaultdict

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect

from inphosite.controllers.entity import EntityController
from inphosite.lib.base import BaseController, render
import inphosite.lib.helpers as h
from inpho.model.idea import IdeaEvaluation
from inpho.model.taxonomy import *
from inphosite.model import Session

log = logging.getLogger(__name__)

class TaxonomyController(EntityController):
    _type = Node
    _controller = 'taxonomy'

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

        return render('taxonomy/node.%s' % filetype)
        #if filetype=='html':
        #    c.entity = c.node.idea
        #    return render('idea/idea.html')
        #else:
        #    return render('taxonomy/node.%s' % filetype)
    
    def graph(self, id=None, filetype='josn'):
        abort(404)
