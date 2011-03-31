import cgi

from paste.urlparser import PkgResourcesParser
from pylons import request, tmpl_context as c
from pylons.controllers.util import forward
from pylons.middleware import error_document_template
from inphosite.lib.base import render
from webhelpers.html.builder import literal

from inphosite.lib.base import BaseController

class ErrorController(BaseController):

    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """
    def document(self, filetype='html'):
        resp = request.environ.get('pylons.original_response')
        code = cgi.escape(request.GET.get('code', ''))
        content = cgi.escape(request.GET.get('message', ''))
        if resp:
            content = literal(resp.status)
            code = code or cgi.escape(str(resp.status_int))
        if not code:
            raise Exception('No status code was found')
        
        req = request.environ.get('pylons.original_request')
        routing = req.environ.get('pylons.routes_dict')
        if routing:
            c.controller = routing.get('controller', None)
            c.id = routing.get('id', None)
            c.filetype = routing.get('filetype', 'html')
            c.action = routing.get('action', 'view')
        else:
            c.controller = None
            c.id = None
            c.filetype = 'html'
            c.action = 'view'

        c.code = code
        c.message = content
        return render('error.' + c.filetype)
    
    def img(self, id):
        """Serve Pylons' stock images"""
        return self._serve_file('/'.join(['media/img', id]))

    def style(self, id):
        """Serve Pylons' stock stylesheets"""
        return self._serve_file('/'.join(['media/style', id]))

    def _serve_file(self, path):
        """Call Paste's FileApp (a WSGI application) to serve the file
        at the specified path
        """
        request.environ['PATH_INFO'] = '/%s' % path
        return forward(PkgResourcesParser('pylons', 'pylons'))
