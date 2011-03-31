import pylonsmodel as m
import numpy as np

import networkx as nx
import re
from math import log

# open answer set program
f = open("current.txt")
f = f.read()

regex = re.compile("[ins|isa]\(i(\d+),i(\d+)\)")
regex_class = re.compile("class\(i(\d+)\)")

instances = frozenset(regex.findall(f))
classes = frozenset(regex_class.findall(f))

# create directed graph on the instances
G = nx.DiGraph()
G.add_edges_from(instances)
nodes = frozenset(G.nodes())

# get all shortest paths and all top-level nodes
paths = nx.all_pairs_shortest_path(G)
top_level = [node for node in G.nodes_iter() if G.out_degree(node) == 0]
leaves = [node for node in G.nodes_iter() 
                   if G.out_degree(node) >= 1 and G.in_degree(node) == 0 and
                       node not in classes]
to_root = [paths[l][t] for t in top_level for l in leaves if t in paths[l]]


# select ideas and calculate stats
q = m.model.meta.Session.query(m.Idea)
def calc(list):
    ideas = [q.get(i) for i in list]
    ent = [float(i.entropy) for i in ideas if i and i.entropy > 0]
    return (np.mean(ent), np.std(ent))

# for printing
out = open("entropies.txt", "w")
def print_stats(name, stats):
    print >>out, "%s\nMean: %f\nStd Dev: %f\n\n" % (name, stats[0], stats[1])

# root nodes
print_stats("roots", calc(top_level))
# leaf nodes, regardless of depth
print_stats("leaves", calc(leaves))
# depth
for i in range(6):
    l = [t for t in to_root if len(t) == i]
    print_stats("depth %d" % i, calc(l))

out.flush()
out.close()
