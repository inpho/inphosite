import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from inphosite.lib.base import BaseController, render

log = logging.getLogger(__name__)

class PageController(BaseController):
    def amt_taxonomy(self):
        redirect('http://inpho2.cogs.indiana.edu/amt_taxonomy/')

    def index(self):
        return render('index.html')
    
    def about(self):
        return render('about.html')

    def papers(self):
        return render('papers.html')

    def owl(self):
        return render('owl.html')
    
    def json(self):
        return render('json.html')

    def docs(self):
        return render('docs.html')
    
    def graph(self):
        return render('graph.html')
