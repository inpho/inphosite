import logging
import time
import re
from urllib import unquote

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect

# import decorators
from pylons.decorators import validate
from inphosite.lib.rest import restrict, dispatch_on

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

    def data_integrity(self, filetype='html', redirect=False):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        journal_q = Session.query(Journal)
        
        # check for query
        if request.params.get('q'):
            journal_q = journal_q.filter(Journal.name.like(u'%'+request.params['q']+'%'))
        
        # get the list of journals
        c.journals = list(journal_q)

        c.missing_issn = []
        c.bad_issn = []
        for journal in c.journals:
            # Missing ISSN
            if not getattr(journal, 'ISSN') or journal.ISSN == '':
                c.missing_issn.append(journal)
            # Journal has bad ISSN format (xxxx-xxxx is good format)
            elif not re.match(r'[0-9]{4}-[0-9]{4}', journal.ISSN):
                c.bad_issn.append(journal)

        # Duplicates
        # It is set up for pairs. If there is more than 2 of the same journal it will have multiples
        c.duplicate = []
        c.sorted_journals = sorted(c.journals, key=lambda journal: journal.label)
        for i in range(len(c.sorted_journals) - 1):
            if c.sorted_journals[i].label == c.sorted_journals[i+1].label:
                c.duplicate.append(c.sorted_journals[i])
                c.duplicate.append(c.sorted_journals[i+1]) 

        # re-get the list of journals (only ones accessed in last 4 weeks)
        # Magic constant of 2419200 corresponds to 4 weeks in seconds
        c.journals = list(journal_q.filter(Journal.last_accessed < (time.time() -2419200)))

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
        
        return render('journal/data_integrity.' + filetype)

    def graph(self, id=None, filetype='json'):
        abort(404)


    #UPDATE
    def update(self, id=None):
        terms = ['label', 'sep_dir', 'last_accessed', 'language', 'openAccess', 'active', 'student', 'ISSN']

        URL = request.params.get('URL', None)
        if URL is not None:
            journal = h.fetch_obj(Journal, id)
            if URL == 'none' or URL == 'None':
                journal.URL = None
            else:
                journal.URL = unquote(URL)
                journal.check_url()
            Session.commit()

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
    
    def _delete_abbrs(self, id):
        c.entity = h.fetch_obj(Journal, id, new_id=True)

        # add a new search pattern
        pattern = request.params.get('pattern', None)
        if pattern is None:
            abort(400)
   
        # rudimentary input sanitization
        pattern = pattern.strip() 
        if pattern in c.entity.abbrs:
            c.entity.abbrs.remove(pattern)

            Session.commit()

        return "OK"

    @dispatch_on(DELETE='_delete_abbrs')
    def abbrs(self, id):
        c.entity = h.fetch_obj(Journal, id, new_id=True)

        # add a new search pattern
        pattern = request.params.get('pattern', None)
        if pattern is None:
            abort(400)

        # rudimentary input sanitization
        pattern = pattern.strip() 
        if pattern not in c.entity.abbrs:
            c.entity.abbrs.append(unicode(pattern))

            Session.commit()

        return "OK"
    
    def _delete_queries(self, id):
        c.entity = h.fetch_obj(Journal, id, new_id=True)

        # add a new search pattern
        pattern = request.params.get('pattern', None)
        if pattern is None:
            abort(400)

        # rudimentary input sanitization
        pattern = pattern.strip() 
        if pattern in c.entity.queries:
            c.entity.queries.remove(pattern)

            Session.commit()

        return "OK"

    @dispatch_on(DELETE='_delete_queries')
    def queries(self, id):
        c.entity = h.fetch_obj(Journal, id, new_id=True)

        # add a new search pattern
        pattern = request.params.get('pattern', None)
        if pattern is None:
            abort(400)

        pattern = unicode(pattern) 
        if pattern not in c.entity.queries:
            c.entity.queries.append(unicode(pattern))

            Session.commit()

        return "OK"
