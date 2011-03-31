from scripts.environment import load
import re

if __name__ == "__main__":
    import sys
    config = load(sys.argv[-1])
    from scripts.model import *
    from mako.template import Template
    from sqlalchemy.sql.expression import and_

    def calc(type=Idea, graph_type=IdeaGraphEdge):
        q = meta.Session.query(type)
        edgeq = meta.Session.query(graph_type).\
                     join((type, type.ID==graph_type.cons_id)).\
                     filter(type.sep_dir != '')
        sep_ideas = q.filter(type.sep_dir != '').all()
        
        for ante in sep_ideas:
            f = ante.get_filename(config['app_conf']['corpus'])
            if not f:
                continue
        
            f = open(f) 
            txt = f.read()
            edges = edgeq.filter(graph_type.ante == ante).all()
            for edge in edges:
                try:
                    # find how many times term occurs in article
                    edge.occurs_in = len(re.findall(edge.cons.searchpattern, txt))
                    print "<%s, %s> = %d" % (ante.label, edge.cons.label, edge.occurs_in)
                except:
                    continue
    
            f.close()
        
        meta.Session.commit()
    
    calc(Idea, IdeaGraphEdge)
    calc(Entity, IdeaThinkerGraphEdge)
    calc(Thinker, ThinkerGraphEdge)

else:
    raise Exception("Must be called from command line")
