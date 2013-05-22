from webob import Request

import zope.interface
from repoze.who.classifiers import default_request_classifier
from repoze.who.interfaces import IRequestClassifier
from pylons.controllers.util import abort
from pylons import request
import helpers as h

from hashlib import md5
import urllib2

def encrypt(password, secret=''):
    ''' Encryption function for use on passwords '''
    result = md5(password)
    result.update(secret)
    return result.hexdigest()

def is_logged_in():
    return request.environ.get('repoze.who.identity') is not None

def is_admin():
    identity = request.environ.get('repoze.who.identity')
    if identity is not None:
        return 'admin' in identity['user'].roles
    else:
        return False

def authorize(permission):
    """
    This is a decorator which can be used to decorate a Pylons controller action.
    It takes the permission to check as the only argument and can be used with
    all types of permission objects.
    """
    if permission:
        return func 
    else:
        abort(401)

def uid(request):
    if not is_logged_in():
        return None
    return request.environ.get('repoze.who.identity')['user'].username

def username(request):
    if not is_logged_in():
        return None
    return request.environ.get('repoze.who.identity')['user'].username



def user_exists(username):
    return h.get_user(username) is not None  

def get_username_from_cookie(cookie):
    """
    Takes a cookie authorization and decodes it to find the username.
    Does some validation against the requesting IP address. 
    Raises a ValueError if they do not match the request.
    """
    cookie = urllib2.unquote(cookie)
    if cookie == "null":
        return None

    decodedCookie = h.rot(cookie)
    ip = request.environ.get('REMOTE_ADDR')
    index = decodedCookie.find(ip, 0, len(ip))
    if index != -1:
        username = decodedCookie.replace(ip, '', len(ip))

        if username.isalpha():
            username = 'sep.' + username

            return username
    else:
        raise ValueError("Invalid IP for cookie value")


class UserModelPlugin(object):
    
    def authenticate(self, environ, identity):
        """Return username or None.
        """
        try:
            username = identity['login']
            password = identity['password']
        except KeyError:
            return None
       
         
        user = h.get_user(username)
        if user and encrypt(password) == user.password:
                return username
        else:
            return None
    
    def add_metadata(self, environ, identity):
        username = identity.get('repoze.who.userid')
        user = h.get_user(username)
        if user is not None:
            identity['user'] = user    

def custom_request_classifier(environ):
    """ Returns one of the classifiers 'app', 'browser' or any
    standard classifiers returned by
    repoze.who.classifiers:default_request_classifier
    """
    classifier = default_request_classifier(environ)
    if classifier == 'browser':
        # Decide if the client is a (user-driven) browser or an application
        request = Request(environ)
        if not request.accept.best_match(['application/xhtml+xml', 'text/html']):
            # In our view, any client who doesn't support HTML/XHTML is an "app",
            #   not a (user-driven) "browser".
            classifier = 'app'
    
    return classifier
zope.interface.directlyProvides(custom_request_classifier, IRequestClassifier)
