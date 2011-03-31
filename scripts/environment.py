from paste.deploy import appconfig
from inphosite.config.environment import load_environment

def load(config_file):
    c = appconfig('config:' + config_file)
    config = load_environment(c.global_conf, c.local_conf)

    return config
