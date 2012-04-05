import logging
import time
from urllib import unquote

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect

# import decorators
from pylons.decorators import validate
from inphosite.lib.rest import restrict

# import inphosite information
from inphosite.lib.base import BaseController, render

from inpho.model import Journal, Entity
from inpho.model import Session
import inphosite.lib.helpers as h
from inphosite.controllers.entity import EntityController

log = logging.getLogger(__name__)

class JournalController(EntityController):
    _type = Journal
    _controller = 'journal'

    def list_stale_url(self, filetype='html', redirect=False):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        journal_q = Session.query(Journal)
        
        # check for query
        if request.params.get('q'):
            journal_q = journal_q.filter(Journal.name.like(u'%'+request.params['q']+'%'))
        
        # Magic constant of 2419200 corresponds to 4 weeks in seconds
        journal_q = journal_q.filter(Journal.last_accessed < (time.time() - 2419200))

        # get the list of journals
        c.journals = list(journal_q)

        # filter out results into different chunks
        # Valid URL, not found
        c.broken = [journal for journal in c.journals if journal.URL]
        
        # Journal is active, no URL set
        c.missing = [journal for journal in c.journals 
                     if journal.URL is None and journal.active]
        
        # Journal is active, URL is set to blank
        c.blank = [journal for journal in c.journals 
                   if journal.URL == '' and journal.active]
        
        # Jornal is inactive and missing URL
        c.inactive = [journal for journal in c.journals 
                      if journal.URL is None and not journal.active]

        return render('journal/stale-url-list.' + filetype)

    def graph(self, id=None, filetype='json'):
        abort(404)


    #UPDATE
    def update(self, id=None):
        terms = ['label', 'sep_dir', 'URL', 'last_accessed', 'language', 'openAccess', 'active', 'student', 'ISSN']

        URL = request.params.get('URL', None)
        if URL is not None:
            journal = h.fetch_obj(Journal, id)
            if URL == 'none' or URL == 'None':
               journal.URL = None
            else:
                journal.URL = unquote(URL)
            journal.check_url()
            Session.commit()
        else:
            super(JournalController, self).update(id, terms)

    @restrict('GET')
    def url(self, id=None, url=None):
        # Get entity and render template
        entity = h.fetch_obj(self._type, id, new_id=True)

        if entity.check_url():
            return "200 OK"
        else:
            abort(404)

    @restrict('DELETE')
    def delete(self, id=None):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        journal = h.fetch_obj(Journal, id)
        
        h.delete_obj(journal)

        # Issue an HTTP success
        response.status_int = 200
        return "OK"

    @restrict('POST')
    def create(self):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        valid_params = ["ISSN", "noesisInclude", "URL", "source", 
                        "abbr", "language", "student", "active"]
        params = request.params.mixed()

        if '_method' in params:
            del params['_method']
        
        if 'label' in params:
            label = params['label']
            del params['label']
        elif 'name' in params:
            label = params['name']
            del params['name']
        else:
            abort(400)
        
        for k in params.keys():
            if k not in valid_params:
                abort(400)

        journal = Journal(label, **params)
        Session.add(journal)
        Session.flush()

        # Issue an HTTP success
        response.status_int = 302
        response.headers['location'] = h.url(controller='journal',
                                                 action='view', id=journal.ID)
        return "Moved temporarily"
    
