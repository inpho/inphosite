"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from routes import Mapper

def make_map(config):
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    map.minimization = False 

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')
    
    # CUSTOM ROUTES HERE
    map.connect('signout', '/signout', controller='account', action='signout')
    map.connect('signin', '/signin', controller='account', action='signin')
    map.connect('register', '/register', controller='account', action='register')
    map.connect('/', controller='page', action='index')
    map.connect('/papers/', controller='page', action='papers')
    map.connect('/owl/', controller='page', action='owl')
    map.connect('/docs/', controller='page', action='docs')
    map.connect('/about/', controller='page', action='about')
    map.connect('/privacy/', controller='page', action='privacy')
    map.connect('/{controller}', action='list', 
        conditions=dict(method=["GET"]))
    map.connect('/admin', controller='admin', action='index', 
        conditions=dict(method=["GET"]))
    map.connect('/{controller}.{filetype:html|json|xml}', action='list', 
        conditions=dict(method=["GET"]))
    map.connect('/{controller}/{id:\d+}', action='view',
        conditions=dict(method=["GET"]))
    map.connect('/{controller}/{id:\d+}', action='view', filetype='html',
        conditions=dict(method=["GET"]))
    map.connect('/{controller}/{id:\d+}.{filetype:html|json|xml}', action='view', 
        conditions=dict(method=["GET"]))
    map.connect('/{controller}/{id:\d+}', action='update', 
        conditions=dict(method=["PUT"]))
    map.connect('/{controller}/{id:\d+}', action='delete', 
        conditions=dict(method=["DELETE"]))
    map.connect('/{controller}/{id:\d+}/{action}.{filetype:html|json|nwb|xml}', 
        conditions=dict(method=["GET", "POST", "PUT", "DELETE"]))
    map.connect('/{controller}/{id:\d+}/{action}', 
        conditions=dict(method=["GET", "POST", "PUT", "DELETE"]))
    map.connect('/{controller}/{id:\d+}/{type:has_influenced|influenced_by|' +
        'teacher_of|student_of}/{id2:\d+}', action='binary',
        conditions=dict(method=["POST", "PUT", "DELETE"]))
    map.connect('/{controller}/{id:\d+}/{type:nationality|profession}/{id2:\d+}', 
        action='unary', conditions=dict(method=["POST", "PUT", "DELETE"]))
    map.connect('/{controller}/{id:\d+}/{action}/{id2:\d+}',
        conditions=dict(method=["GET", "POST", "PUT", "DELETE"]))

    # Generic Routes
    map.connect('/{controller}', action='create', 
        conditions=dict(method=["POST"]))
    map.connect('/{controller}/{action:\D+}.{filetype}')
    map.connect('/{controller}/{action:\D+}')
    return map
