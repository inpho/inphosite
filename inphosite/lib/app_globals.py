"""The application's Globals object
http://stackoverflow.com/questions/3458344/turbomail-3-with-pylons-1-0-mailnotenabledexception
"""


import atexit
from turbomail import interface
from turbomail.adapters import tm_pylons
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

class Globals(object):
    """Globals acts as a container for objects available throughout the
    life of the application

    """

    def __init__(self, config):
        """One instance of Globals is created during application
        initialization and is available during requests via the
        'app_globals' variable

        """
        self.cache = CacheManager(**parse_cache_config_options(config))
        tm_pylons.config = config 
        tm_pylons.start_extension() 
        #atexit.register(tm_pylons.shutdown_extension)
        #interface.start(tm_pylons.FakeConfigObj(config))

