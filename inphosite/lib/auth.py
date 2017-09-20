from webob import Request

import zope.interface
from repoze.who.classifiers import default_request_classifier
from repoze.who.interfaces import IRequestClassifier
from pylons.controllers.util import abort
from pylons import request

from hashlib import md5
import urllib2

from inpho.model import User
from inpho.model import Session
from sqlalchemy import or_

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


def rot(cookie=None):
    ascii_table = "".join([chr(i) for i in xrange(32,127)])
    rot_table = ascii_table[48:] + 'O' + ascii_table[:47]
    trans = string.maketrans(ascii_table, rot_table)
    decoded = str(cookie).translate(trans)
    return decoded

def get_user(login):
    """
    Returns the User object from the model.

    :rtype: :class:`inpho.model.User`
    """
    if isinstance(login,str) or isinstance(login,unicode):
        user = Session.query(User).filter(or_(User.email==login,
                                              User.username==login.lower())).first()
        return user
    else:
        raise Exception(login)


def user_exists(username):
    return get_user(username) is not None  

def get_username_from_cookie(cookie):
    """
    Takes a cookie authorization and decodes it to find the username.
    Does some validation against the requesting IP address. 
    Raises a ValueError if they do not match the request.
    """
    cookie = urllib2.unquote(cookie)
    if cookie == "null":
        return None

    decodedCookie = rot(cookie)
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
       
         
        user = get_user(username)
        if user and encrypt(password) == user.password:
                return username
        else:
            return None
    
    def add_metadata(self, environ, identity):
        username = identity.get('repoze.who.userid')
        user = get_user(username)
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
