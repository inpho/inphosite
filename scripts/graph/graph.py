#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
python graph/graph.py <PATH TO CONFIG.INI> <TYPE>
type: ii | it | tt
"""

from scripts.environment import load

if __name__ == "__main__":
    import sys
    load(sys.argv[-2])

    from scripts.model import *
    from mako.template import Template
    
    type = sys.argv[-1]
    if type == "ii":
        edges = model.meta.Session.query(model.IdeaGraphEdge).all()
    elif type == "it":
        edges = model.meta.Session.query(model.IdeaThinkerGraphEdge).all()
    elif type == "tt":
        edges = model.meta.Session.query(model.ThinkerGraphEdge).all()
    else:
        raise Exception("unrecognized type")
    
    graph = Template(filename='graph/graph.txt', default_filters=['decode.utf8'])
    print graph.render_unicode(graph=edges).encode('utf-8','replace')

else:
    raise Exception("Must be called from command line")


