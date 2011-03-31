from scripts.environment import load
import re
import sys

if __name__ == "__main__":
    print "Loading configuration ..."
    config = load(sys.argv[-1])

    #TODO: Figure out why this is even necessary.
    print config['app_conf']
    app = config['app_conf']
    print app['sep.databases']
    
    from scripts.model import *
    from mako.template import Template
    import inphosite.lib.sepparse as sepparse
    import inphosite.lib.searchstring as searchstring

    print "Getting entries ..."
    sepparse.getentries(app['sep.databases'])
    print "Building add list ..."
    list = sepparse.addlist()
    print "fuzzy matching ..."
    searchstring.fuzzymatchall(list)

else:
    raise Exception("Must be called from command line")
