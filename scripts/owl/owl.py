#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scripts.environment import load

if __name__ == "__main__":
    import sys
    load(sys.argv[-1])

    from scripts.model import *
    from mako.template import Template
    
    node_q = model.meta.Session.query(model.Node)
    thinker_q = model.meta.Session.query(model.Thinker)
    profession_q = model.meta.Session.query(model.Profession)
    nationality_q = model.meta.Session.query(model.Nationality)
    
    nodes = node_q.all()
    thinkers = thinker_q.all()
    professions = profession_q.all()
    nationalities = nationality_q.all()
    
    owl = Template(filename='/Users/inpho/api/scripts/owl/owl.xml',
                   default_filters=['decode.utf8', 'u', 'x'])
    print owl.render_unicode(nodes=nodes, thinkers=thinkers, 
               professions=professions, nationalities=nationalities).encode('utf-8',
               'replace')

else:
    raise Exception("Must be called from command line")


