import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons import url
import re

from inphosite.lib.base import BaseController, render

import inphosite.model as model
from inphosite.model.meta import Session
from inphosite.model import Entity, Node, Idea
import inphosite.lib.helpers as h
from sqlalchemy import or_
from sqlalchemy.sql.expression import func

from inphosite.lib.multi_get import multi_get
from urllib import quote_plus
import urllib
import simplejson

from xml.etree.ElementTree import parse
from xml.etree import ElementTree as ET

log = logging.getLogger(__name__)

class EntityController(BaseController):
    _type = Entity
    _controller = 'entity'

    def list(self, filetype='html'):
        entity_q = Session.query(self._type)
        entity_q = entity_q.limit(request.params.get('limit', None))
        #TODO: Remove the following line when Nodes are eliminated
        entity_q = entity_q.filter(Entity.typeID != 2)
        
        c.nodes = Session.query(Node).filter(Node.parent_id == None)
        c.nodes = c.nodes.order_by("name").all()

        c.query = request.params.get('q', '')
        c.sep = request.params.get('sep', '')

        if request.params.get('sep_filter', False):
            entity_q = entity_q.filter(Entity.sep_dir != '')
        
        if c.sep:
            entity_q = entity_q.filter(Entity.sep_dir == c.sep) 

        if c.query:
            o = or_(Entity.label.like(q+'%'), Entity.label.like('% '+q+'%'))
            entity_q = entity_q.filter(o).order_by(func.length(Entity.label))
        
        if filetype=='json':
            response.content_type = 'application/json'
        
        c.entities = entity_q.all()
        if request.params.get('redirect', False) and len(c.entities) == 1: 
            h.redirect(h.url(controller=self._controller, action='view', 
                             filetype=filetype, id=c.entities[0].ID), 
                       code=302)
        else:
            return render('entity/entity-list.' + filetype)
    

    def search(self, id, id2=None):
        # Grab ID(s) from database and get their search string(s).
        if id2 is None:
            c.entity = h.fetch_obj(Entity, id)
            c.entity2 = None
        else:
            c.entity = h.fetch_obj(Entity, id)
            c.entity2 = h.fetch_obj(Entity, id2)

        # Run searches
        c.sep = EntityController._search_sep(c.entity, c.entity2)
        c.noesis = EntityController._search_noesis(c.entity, c.entity2)
        return render('entity/search.html')

    @staticmethod
    def _search_sep(entity, entity2):
        # Build search string
        if entity2 is None:
            searchstr = c.entity.web_search_string()
            c.sep_searchstr = quote_plus(searchstr.encode('utf8'))
        else:
            searchstr = entity.web_search_string() + " + " + \
                        entity2.web_search_string()
            c.sep_searchstr = quote_plus(searchstr.encode('utf8'))

        # Put together URL string
        url = "http://plato.stanford.edu/search/xmlSearcher.py?query=" + \
              c.sep_searchstr

        # Get results and parse the XML
        results = multi_get([url])[0][1]
        if results:
            tree = ET.ElementTree(ET.fromstring(results))
            root = tree.getroot()
            json = []
            for element in root.getiterator('{http://a9.com/-/spec/opensearch/1.1/}Item'):
                dict = {}
                for iter in element.getiterator('{http://a9.com/-/spec/opensearch/1.1/}Text'):
                    dict['Text'] = iter.text
                for iter in element.getiterator('{http://a9.com/-/spec/opensearch/1.1/}LongDescription'):
                    dict['LongDescription'] = iter.text
                for iter in element.getiterator('{http://a9.com/-/spec/opensearch/1.1/}Location'):
                    dict['URL'] = 'http://plato.stanford.edu/entries/%s/' % iter.text
                json.append(dict)

        return json

    @staticmethod
    def _search_noesis(entity, entity2):
        # Concatenate search strings for each entity
        if entity2 is None:
            searchstr = c.entity.web_search_string()
            c.noesis_searchstr = quote_plus(searchstr.encode('utf8'))
        else:
            searchstr = entity.web_search_string() + " " + \
                        entity2.web_search_string()
            c.noesis_searchstr = quote_plus(searchstr.encode('utf8'))

        # Put together URL string
        api_key = "AIzaSyAd7fxJRf5Yj1ehBQAco72qqBSK1l0_p7c"
        c.noesis_cx = "001558599338650237094:d3zzyouyz0s"
        url = "https://www.googleapis.com/customsearch/v1?" + \
              "key=" + api_key + "&cx=" + c.noesis_cx + \
              "&q=" + c.noesis_searchstr

        # Get results and parse into json
        results = multi_get([url])[0][1]
        json = simplejson.loads(results) if results else None
        return json


    def view(self, id=None, filetype='html'):
        c.sep_filter = request.params.get('sep_filter', False) 

        # Set MIME type of json files
        if filetype=='json':
            response.content_type = 'application/json'

        # Get entity and render template
        c.entity = h.fetch_obj(Entity, id, new_id=True)
        if self._type == Entity:
            h.redirect(c.entity.url(action='view', filetype=filetype), 
                       code=303)
        else:
            return render('entity/entity.' + filetype)

    def graph(self, id=None, id2=None, filetype='json'):
        c.entity = h.fetch_obj(Entity, id, new_id=True)
        if not id2:
            redirect(c.entity.url(filetype, action="graph"), code=303)
        else:
            c.entity2 = h.fetch_obj(Entity, new_id=True)
            redirect(c.entity.url(filetype, action="graph"), code=303)


    def admin(self, id=None):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        redirect = request.params.get('redirect', False)
        add = request.params.get('add', False)
        limit = request.params.get('limit', None)
        sep_dir = request.params.get('sep_dir', "")
        entity_q = Session.query(Entity)
        c.found = False    
        c.custom = False
        c.new = False
        c.sep_dir = sep_dir
        c.sepdirnew = False
        c.alreadysepdir = False

        if request.params.get('q'):
            q = request.params['q']
            o = Entity.label.like(q)
            entity_q = entity_q.filter(o).order_by(func.length(Entity.label))
            # if only 1 result, go ahead and view that entity
            if redirect and entity_q.count() == 1:
                c.entity = h.fetch_obj(Entity, entity_q.first().ID)
                
                #now get type and route to correct edit page
                #first, if it is an idea, typeID = 1
                if c.entity.typeID == 1:
                    print "have an idea, q, entityq count = 1"
                    c.idea = h.fetch_obj(model.Idea, entity_q.first().ID)
                    c.found = True
                    id = c.idea.ID
                    c.message = 'Entity edit page for idea ' + c.idea.label
                    #set up c.search_string_list which will be used to structure intersection/union search pattern option
                    if request.params.get('sep_dir'):
                            sep_dir = request.params['sep_dir']
                            if not (c.idea.sep_dir):
                                c.idea.sep_dir = request.params['sep_dir']
                                c.sepdirnew = True
                            else:
                                c.alreadysepdir = True
                                c.entry_sep_dir = request.params['sep_dir']
                    c.search_string_list = c.idea.setup_SSL()
                    if re.search(' and ', c.idea.label):
                        c.search_pattern_list = ['union', 'intersection']
                    return render ('admin/idea-edit.html') 
                
                #thinkers
                elif c.entity.typeID == 3:
                    print "have a thinker, q, entityq count = 1"
                    c.thinker = h.fetch_obj(model.Thinker, entity_q.first().ID)
                    c.found = True
                    id = c.thinker.ID
                    c.message = 'Entity edit page for thinker ' + c.thinker.label
                    if request.params.get('sep_dir'):
                            sep_dir = request.params['sep_dir']
                            if not (c.thinker.sep_dir):
                                c.thinker.sep_dir = request.params['sep_dir']
                                c.sepdirnew = True
                            else:
                                c.alreadysepdir = True
                                c.entry_sep_dir = request.params['sep_dir']
                    return render ('admin/thinker-edit.html')
                
                
                elif c.entity.typeID == 4:
                    print "have a journal, q, entityq count = 1"
                    c.journal = h.fetch_obj(model.Journal, entity_q.first().ID)
                    c.found = True
                    id = c.journal.ID
                    c.message = 'Entity edit page for journal ' + c.journal.label
                    if request.params.get('sep_dir'):
                            sep_dir = request.params['sep_dir']
                            if not (c.journal.sep_dir):
                                c.journal.sep_dir = request.params['sep_dir']
                                c.sepdirnew = True
                            else:
                                c.alreadysepdir = True
                                c.entry_sep_dir = request.params['sep_dir']
                    return render ('admin/journal-edit.html')

                elif c.entity.typeID == 5:
                    print "have a work, q, entityq count = 1"
                    c.work = h.fetch_obj(model.Work, entity_q.first().ID)
                    c.found = True
                    id = c.work.ID
                    c.message = 'Entity edit page for work ' + c.work.label
                    if request.params.get('sep_dir'):
                            sep_dir = request.params['sep_dir']
                            if not (c.work.sep_dir):
                                c.work.sep_dir = request.params['sep_dir']
                                c.sepdirnew = True
                            else:
                                c.alreadysepdir = True
                                c.entry_sep_dir = request.params['sep_dir']
                    return render ('admin/work-edit.html')
                
                elif c.entity.typeID == 6:
                    print "have a school_of_thought, q, entityq count = 1"
                    c.school_of_thought = h.fetch_obj(model.SchoolOfThought, entity_q.first().ID)
                    c.found = True
                    id = c.school_of_thought.ID
                    c.message = 'Entity edit page for school_of_thought ' + c.school_of_thought.label
                    if request.params.get('sep_dir'):
                            sep_dir = request.params['sep_dir']
                            if not (c.school_of_thought.sep_dir):
                                c.school_of_thought.sep_dir = request.params['sep_dir']
                                c.sepdirnew = True
                            else:
                                c.alreadysepdir = True
                                c.entry_sep_dir = request.params['sep_dir']
                    return render ('admin/school_of_thought-edit.html')
            
            
            elif redirect and entity_q.count() == 0:
                c.message = "No match found for your search; if you would like to add your idea, please enter its label and sepdir into the field below."
                c.new = True
                c.prevvalue = q
                return render ('admin/entity-add.html') 

            else:
                return ('No exact match for your search; please click "back" and try again.')

        if id is None:
            print "I am here"
            c.message = "Please input an idea using the search bar to the left."
            return render ('admin/idea-edit.html')
        else:
            c.entity = h.fetch_obj(Entity, id)
            c.found = True
            c.message = 'Entity edit page for entity ' + c.entity.label
            
            #get sep_dir if present--from admin.py action addentry
            if request.params.get('sep_dir'):
                sep_dir = request.params['sep_dir']
                if not (c.entity.sep_dir):
                    c.entity.sep_dir = sep_dir
                else:
                    c.message = c.message + "WARNING:  entity already has a sep_dir [" + c.entity.sep_dir + "].  Not replacing with [" + sep_dir + "].  If you would like to do so, please do so manually in the form below."
            
            if request.params.get('entry_sep_dir'):
                entry_sep_dir = request.params['entry_sep_dir']
                if not (c.entity.sep_dir):
                    c.entity.sep_dir = entry_sep_dir
                else:
                    c.message = c.message + "WARNING:  entity already has a sep_dir [" + c.entity.sep_dir + "].  Not replacing with [" + sep_dir + "].  If you would like to do so, please do so manually in the form below."
            
                    
            #set up c.search_string_list which will be used to structure intersection/union search pattern option
            if c.entity.typeID == 1:
                c.idea = h.fetch_obj(model.Idea, c.entity.ID)
                c.search_string_list = c.idea.setup_SSL()
                return render ('admin/idea-edit.html')
            elif c.entity.typeID == 3:
                c.thinker = h.fetch_obj(model.Thinker, c.entity.ID)
                return render('admin/thinker-edit.html')
            elif c.entity.typeID == 4:
                c.journal = h.fetch_obj(model.Journal, c.entity.ID)
                return render('admin/journal-edit.html')
            elif c.entity.typeID == 5:
                c.work = h.fetch_obj(model.Work, c.entity.ID)
                return render('admin/work-edit.html')
            elif c.entity.typeID == 6:
                c.school_of_thought = h.fetch_obj(model.SchoolOfThought, c.entity.ID)
                return render('admin/school_of_thought-edit.html')
        
        
        c.entity = h.fetch_obj(Entity, id, new_id=True)
        redirect(c.entity.url(action='admin'), code=303)
        
    def process(self, entity_type = '1', id=None):
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

        q = request.params.get('q', None)
        label = request.params.get('label', None)
        sep_dir = request.params.get('sep_dir', None)
        action = request.params.get('action', None)
        
                
        type = request.params.get("entity_type", '1')
        if type == '1':
            redirect(url(controller='idea', action='process', q = q, label = label, sep_dir = sep_dir, action2 = action), code=303)
        elif type == '3':
            print "hi der m tryin to process ur thinker"
            redirect(url(controller = 'thinker', action='process', q = q, label = label, sep_dir = sep_dir, action2 = action), code=303)
        elif type == '4':
            print "hi der m tryin to process ur journal"
            redirect(url(controller = 'journal', action='process', q = q, label = label, sep_dir = sep_dir, action2 = action), code=303)
        elif type == '5':
            print "hi der m tryin to process ur work"
            redirect(url(controller = 'work', action='process', q = q, label = label, sep_dir = sep_dir, action2 = action), code=303)
        elif type == '6':
            print "hi der m tryin to process ur school_of_thought"
            redirect(url(controller = 'school_of_thought', action='process', q = q, label = label, sep_dir = sep_dir, action2 = action), code=303)
