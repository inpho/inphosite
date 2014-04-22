from inphosite.lib.partialDelegate import PartialDelegate
import pystache
import logging

from pylons import request, response, session, config, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from inphosite.lib.base import BaseController, render

import os.path
import glob, os

import json

log = logging.getLogger(__name__)

partials = PartialDelegate(config['mustache_path'])
renderer = pystache.Renderer(file_encoding='utf-8',string_encoding='utf-8',partials=partials)

class PageController(BaseController):
    def options(self):
        response.headers['Access-Control-Allow-Methods'] = '*'
        response.headers['Access-Control-Allow-Headers'] =\
            'origin, c-csrftoken, content-type, authorization, accept, cookie, user-agent, referer, host'
        response.headers['Access-Control-Max-Age'] = '1000'
        response.status = 200
        return ''


    def amt_taxonomy(self): # is this used???
        redirect('http://inpho2.cogs.indiana.edu/amt_taxonomy/')

    def index(self):
        content = {'content': renderer.render_path(config['mustache_path']+"index.mustache"), 'sidebar': False}
        return renderer.render_path(config['mustache_path'] + "base.mustache", content)
    
    def about(self):
        content = {'content': renderer.render_path(config['mustache_path']+"about.mustache"), 'sidebar': False}
        return renderer.render_path(config['mustache_path'] + "base.mustache", content)

    def scimap(self):
        content = {'content': renderer.render_path(config['mustache_path']+"scimap.mustache"), 'sidebar': False}
        return renderer.render_path(config['mustache_path'] + "base.mustache", content)

    def papers(self):
        # load in publications json file
        with open(os.path.join(config['pylons.paths']['root'], 'templates/publications.json')) as publications: 
            papers = json.load(publications)
        content = {'content': renderer.render_path(config['mustache_path'] + 'papers.mustache', papers), 'sidebar': False}
        return renderer.render_path(config['mustache_path'] + "base.mustache", content)

    def owl(self):
        # compile monthly archives
        files = glob.glob(os.path.join(config['owl_path'], 'db-arch_*.owl'))
        files = [os.path.split(file)[1] for file in files]
        files.sort(reverse=True)
        
        archives = {"files": []}
        for file in files:
            year = file[8:12]
            month = file[12:14]
            day = file[14:16]
            archives['files'].append({"file": file, "year": year, "month": month, "day": day})
        
        content = {'content': renderer.render_path(config['mustache_path']+"owl.mustache", archives), 'sidebar': True}
        return renderer.render_path(config['mustache_path'] + "base.mustache", content)

    def json(self): # is this used???
        return render('json.html')

    def docs(self):
        content = {'content': renderer.render_path(config['mustache_path']+"docs.mustache"), 'sidebar': False}
        return renderer.render_path(config['mustache_path'] + 'base.mustache', content)
    
    def graph(self): # is this used???
        return render('graph.html')

    def privacy(self):
        content = {'content': renderer.render_path(config['mustache_path']+"privacy.mustache"), 'sidebar': True}
        return renderer.render_path(config['mustache_path'] + "base.mustache", content)
