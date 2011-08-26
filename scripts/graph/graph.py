#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
python graph/graph.py <TYPE>
type: ii | it | tt
"""

if __name__ == "__main__":
    import sys

    from inpho.model import *
    from mako.template import Template
    
    type = sys.argv[-1]
    if type == "ii":
        edges = Session.query(IdeaGraphEdge).all()
    elif type == "it":
        edges = Session.query(IdeaThinkerGraphEdge).all()
    elif type == "tt":
        edges = Session.query(ThinkerGraphEdge).all()
    else:
        raise Exception("unrecognized type")
    
    graph = Template(filename='graph/graph.txt', default_filters=['decode.utf8'])
    print graph.render_unicode(graph=edges).encode('utf-8','replace')

else:
    raise Exception("Must be called from command line")


