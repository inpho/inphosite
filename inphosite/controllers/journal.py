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
        if 'name' in params:
            name = params['name']
            del params['name']
        else:
            abort(400)
        for k in params.keys():
            if k not in valid_params:
                abort(400)

        journal = Journal(name, **params)
        Session.add(journal)
        Session.flush()

        # Issue an HTTP success
        response.status_int = 302
        response.headers['location'] = h.url(controller='journal',
                                                 action='view', id=journal.ID)
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
                c.journal = h.fetch_obj(Journal, entity_q.first().ID)
                c.found = True
                id = c.journal.ID
                c.message = 'Entity edit page for journal ' + c.journal.name
                if request.params.get('entry_sep_dir'):
                        entry_sep_dir = request.params['entry_sep_dir']
                        if not (c.journal.sep_dir):
                            c.journal.sep_dir = request.params['entry_sep_dir']
                            c.sepdirnew = True
                        else:
                            c.alreadysepdir = True
                            c.entry_sep_dir = request.params['entry_sep_dir']
                            
                return render('admin/journal-edit.html')
            else: 
                print "That didn't journal."

        if id is None:
            print "I am here"
            c.message = "Please input an entity label using the search bar to the left."
            return render ('admin/idea-edit.html')
        else:
            c.journal = h.fetch_obj(Journal, id)
            c.found = True
            c.message = 'Entity edit page for journal ' + c.journal.name
            if request.params.get('entry_sep_dir'):
                entry_sep_dir = request.params['entry_sep_dir']
                if not (c.journal.sep_dir):
                    c.journal.sep_dir = request.params['entry_sep_dir']
                    c.sepdirnew = True
                else:
                    c.alreadysepdir = True
                    c.entry_sep_dir = request.params['entry_sep_dir']
                    
            return render ('admin/journal-edit.html') 
    
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
        URL = request.params.get('URL', None)
        language = request.params.get('language', None)
        queries = [request.params.get('queries', None)]
        openAccess = request.params.get('openAccess', None)
        active = request.params.get('active', None)
        student = request.params.get('student', None)
        ISSN = request.params.get('ISSN', None)
        
        action = request.params.get('action', None)
        action2 = request.params.get('action2', None)
        if action2:
            action = action2
        
        values = dict(request.params)
        #abbrs = [request.params.get('abbrs', None)]
        abbrs = []
        queries = []
        for k, v in values.items():
            key = ""
            
            if k.startswith('abbrs'):
                varname, num = k.split('.')
                key = 'delabbr.%s'%(num)
                keyval = request.params.get(key, False)
                if not keyval:
                    abbrs.append(v)
            elif k.startswith('queries'):
                varname, num = k.split('.')
                key = 'delquer.%s'%(num)
                keyval = request.params.get(key, False)
                if not keyval:
                    queries.append(v)

        
        if action=="Add":
            journal_add = Journal()
            journal_add.label = label
            
            #setup search string and search pattern
            journalname = journal_add.label
            journalname_q = Session.query(Entity)
            o = Entity.searchpattern.like('( '+ journalname + ' )')
            journalname_q = journalname_q.filter(o).order_by(func.length(Entity.label))
            if journalname_q.count() == 0:
                journal_add.searchpattern = "( " + journalname + " )"
                journal_add.searchstring = journalname
            else:
                journal_add.searchpattern = "( " + label + " )"
                journal_add.searchcstring = label
                #reset old journal pattern to whole name too to avoid conflict
                oldjournal = h.fetch_obj(Journal, journalname_q.first().ID)
                oldjournal.searchpattern = "( " + oldjournal.label + " )"
                oldjournal.searchstring = oldjournal.label
                Session.add(oldjournal)

            if sep_dir:
                journal_add.sep_dir = sep_dir
            c.journal = journal_add
            Session.add(journal_add)
            Session.flush()
            Session.commit()
            c.found = True
            c.message = "Journal " + c.journal.label + " added successfully."
            return render ('admin/journal-edit.html')
        elif action=="Modify":
            c.journal = h.fetch_obj(Journal, id)
            c.found = True
            changed = False
            
            #set values from form
            if c.journal.label != label:
                c.journal.label = label
                changed = True
            if c.journal.sep_dir != sep_dir:
                c.journal.sep_dir = sep_dir
                changed = True
            if c.journal.URL != URL:
                c.journal.URL = URL
                changed = True
            if c.journal.language != language:
                c.journal.language = language
                changed = True
            if c.journal.abbrs != abbrs:
                c.journal.abbrs = abbrs
                changed = True
            if c.journal.queries != queries:
                c.journal.queries = queries
                changed = True
            if c.journal.openAccess != openAccess:
                c.journal.openAccess = openAccess
                changed = True
            if c.journal.active != active:
                c.journal.active = active
                changed = True
            if c.journal.student != student:
                c.journal.student = student
                changed = True
            if c.journal.ISSN != ISSN:
                c.journal.ISSN = ISSN
                changed = True
            
            if values['newabbr']:
                c.journal.abbrs.append(values['newabbr'])
                changed = True
                
            if values['newquery']:
                c.journal.queries.append(values['newquery'])
                changed = True
            
            #commit changes
            Session.flush()
            Session.commit()
            if changed:
                c.message = "Journal " + c.journal.label + " modified successfully."
            else:
                c.message = "No change required; Journal " + c.journal.label + " not modified."
            return render ('admin/journal-edit.html')

        elif action == "Delete":
            c.journal = h.fetch_obj(Journal, values['ID'])
            c.message = "Journal # " + values['ID'] + " ("+ c.journal.label + ") deleted; please search for a new entity label on the left."
            h.delete_obj(c.journal)
            Session.flush()
            Session.commit()
            c.found = False
            return render('admin/journal-edit.html')
    
