"""Setup the InPhOSite application"""
import logging
import pylons.test

from inphosite import model
from inphosite.config.environment import load_environment

log = logging.getLogger(__name__)



def setup_app(command, conf, vars):
    """Place any commands to setup inphosite here"""
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    from inphosite.model import meta
    meta.metadata.bind = meta.engine
    #meta.metadata.create_all(bind=meta.engine)

    meta.metadata.create_all(checkfirst=True)

