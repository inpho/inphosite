"""
Very small script to allow importing of the inpho Pylons environment. This is
mostly antiquated, since the primary motivation was to allow for model access,
which has been encapsulated in the inpho.model module.
"""

from paste.deploy import appconfig
from inphosite.config.environment import load_environment

def load(config_file):
    """
    Load the Pylons environment from the given configuration file. 
    Return the config dictionary.
    """
    c = appconfig('config:' + config_file)
    config = load_environment(c.global_conf, c.local_conf)

    return config
