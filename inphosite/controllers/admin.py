import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect as rd

# import decorators
from pylons.decorators import validate
from pylons.decorators.cache import beaker_cache
from inphosite.lib.rest import restrict, dispatch_on

# import inphosite information
from inphosite.lib.base import BaseController, render

from inpho.corpus.sep import get_title, get_titles, new_entries
import inpho.model as model
from inpho.model import *
from inpho.model import Session
import inphosite.lib.helpers as h
import inphosite.lib.sepparse as sep 
import webhelpers.paginate as paginate
from sqlalchemy import or_

log = logging.getLogger(__name__)

import formencode
from formencode import htmlfill, validators, FancyValidator
import simplejson

class AdminController(BaseController):
    def __before__(self):
        # protect entire controller for admins only
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

    def list(self, id = None):
        # sloppy workaround for routing
        return self.index(id)

    def index(self, id = None):
        #two kinds of functionality; either the entity is found or it is not
        #if found, user is given option to modify; if not found, user is given option to add
        c.found = False
        c.new = False
        c.custom = False
        
        if id is None:
            c.message = "Edit Idea Manager v1.0; please search for the idea label you would like to add or modify using the search bar to the left."
            
        return render ('admin/idea-edit.html')
    
    def addlist(self):
        #functionality for parsing through the list of entries which need to be added in light of additions to SEP
        #first step; run the genetries function to refresh the sepentries table from SEPMirror
        
        #uncomment the next line to refresh entries -- need to figure out how to coordinate with doing fuzzymatches ahead of time...maybe just look for new entries and add them?
        #sep.getentries()
        
        
        #second, get the list of entries to be added in a context objects
        addlist = new_entries()
        titles = get_titles()
        c.entries = []
        
        #perform a fuzzy match for each page and construct an appropriate link
        for sep_dir in addlist:
            #create a link for each entry in addlist()
            link = h.url(controller='admin', action='addentry', 
                               title=titles[sep_dir], sep_dir=sep_dir)
            c.entries.append({ 'sep_dir' : sep_dir, 
                               'title' : titles[sep_dir], 
                               'link' : link })
        
        c.message = "Below is a list of SEP entries lacking a corresponding entry in the entity table.  Please click on the link to edit the page for that idea.\n Note that clicking on one of these can take 2-5 minutes to fuzzymatch existing entity entries."
        return render ('admin/newentries.html')

    def addentry(self, title=None, sep_dir=None):
        #action to serve individual page addentry.html to rectify each entry without a sep_dir in the entity table
        #passed ID, title, sep_dir from previous page
        #displays a list of urls for edit pages for everything which is a fuzzymatch to the target title
        #also gives a default option to add a new entry, taking the user to the appropriate entity_add page  
        
        title = request.params.get('title', title)
        sep_dir = request.params.get('sep_dir', "")
        if title is None:
            raise Exception('I don\'t know how you got here, but you shouldn\'t be here without a "title"...please start over at the main page.')
        c.title = title
        c.sep_dir = sep_dir

        #c.linklist will contain the list of links to be displayed
        c.linklist = []
        
        entry = Session.query(SEPEntry).get(sep_dir)
        
        #get fuzzymatch list to article title
        #matchlist will now contain a set of entities which have a fuzzymatch to the title of the article
        #entity.matchvalue will contain the proportion of matched words to total--e.g. 2/3 words matched = .66
        c.message = ""

        matchlist = []
        for match in entry.fmatches:
        #for fuzzymatch in matchlist:
            try:
                entity = h.fetch_obj(Entity, match.entityID)
            except:
                raise Exception('No entity corresponds to your ID.  Invalid ID:' + match.entityID + ".  Perhaps the fuzzymatches are not done populating.")
                
            #entity.link = h.url(controller=entity, action='admin', redirect=True, q=entity.label)
            entity.link = entity.url() + "/admin?entry_sep_dir="+sep_dir
            entity.strength = match.strength
            entity.edits = match.edits
            c.linklist.append(entity)
        
        c.message = c.message + "To add the sep_dir to one of the existing entities below, click on the appropriate button in the first list. (Note that your changes will not be committed until you click 'modify' on the next page.) \n\nAlternatively if none of the existing entity entries correspond to the entry, you may add a new entity by clicking on the final button below."
        return render ('admin/addentry.html')
    
