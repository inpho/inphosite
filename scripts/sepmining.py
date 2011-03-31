import os.path
from BeautifulSoup import BeautifulSoup

import datamining as dm
from inphosite.model import *
from inphosite.model.meta import Session

def extract_article_body(filename):
    f=open(filename)
    doc=f.read()
    soup=BeautifulSoup(doc)

    # rip out bibliography
    biblio_root = soup.findAll('h2', text='Bibliography')
    if biblio_root:
        biblio_root = biblio_root[-1].findParent('h2')
        biblio = [biblio_root]
        biblio.extend(biblio_root.findNextSiblings())
        biblio = [elm.extract() for elm in biblio]

    # grab modified body 
    body=soup.find("div", id="aueditable")

    return body.text

def process_articles(entity_type=Idea, filename='output.txt'):
    # process entities
    ideas = Session.query(entity_type)
    # do not process Nodes or Journals
    ideas = ideas.filter(and_(Entity.typeID!=2, Entity.typeID!=4))
    ideas = ideas.all()

    articles = Session.query(entity_type).filter(entity_type.sep_dir!='').all()
    corpus_root = config['app_conf']['corpus']

    with open(filename, 'w') as f:
        for article in articles:
            filename = article.get_filename(corpus_root)
            if filename and os.path.isfile(filename):
                print "processing:", article.sep_dir
                try: 
                    doc = extract_article_body(filename)
                    lines = dm.prepare_apriori_input(doc, ideas, article)
                    f.writelines(lines)
                except:
                    print "ERROR PROCESSING:", article.sep_dir
            else:
                print "BAD SEP_DIR:", article.sep_dir

import subprocess

def complete_mining(entity_type=Idea, filename='graph.txt', root='./'):
    occur_filename = root + "graph-" + filename
    edge_filename = root + "edge-" + filename
    sql_filename = root + "sql-" + filename

    print "processing articles..."
    process_articles(entity_type, occur_filename)

    print "running apriori miner..."
    dm.apriori(occur_filename, edge_filename)
    
    print "processing edges..."
    edges = dm.process_edges(occur_filename, edge_filename)
    ents = dm.calculate_node_entropy(edges)
    edges = dm.calculate_edge_weight(edges, ents)
    
    print "creating sql files..."

    with open(sql_filename, 'w') as f:
        for edge, props in edges.iteritems():
            ante,cons = edge
            row = "%s::%s" % edge
            row += "::%(confidence)s::%(jweight)s::%(weight)s\n" % props
            f.write(row)

    print "updating term entropy..."

    for term_id, entropy in ents.iteritems():
        term = Session.query(Idea).get(term_id)
        if term:
            term.entropy = entropy

    Session.flush()
    Session.commit()

