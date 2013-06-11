import logging

from pylons import request, response, session, config, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from inphosite.lib.base import BaseController, render

import os.path

import json

log = logging.getLogger(__name__)

class PageController(BaseController):
    def options(self):
        response.headers['Access-Control-Allow-Methods'] = '*'
        response.headers['Access-Control-Allow-Headers'] =\
            'origin, c-csrftoken, content-type, authorization, accept, cookie, user-agent, referer, host'
        response.headers['Access-Control-Max-Age'] = '1000'
        response.status = 200
        return ''


    def amt_taxonomy(self):
        redirect('http://inpho2.cogs.indiana.edu/amt_taxonomy/')

    def index(self):
        return render('index.html')
    
    def about(self):
        return render('about.html')

    def scimap(self):
        return render('scimap.html')

    def papers(self):
        with open(os.path.join(config['pylons.paths']['root'], 'templates/publications.json')) as publications: 
            c.papers = json.load(publications)
        return render('papers.html')

    def owl(self):
        return render('owl.html')
    
    def json(self):
        return render('json.html')

    def docs(self):
        return render('docs.html')
    
    def graph(self):
        return render('graph.html')

    def privacy(self):
        return render('privacy.html')
