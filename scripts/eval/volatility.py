#!/usr/bin/python
from sqlalchemy import func
import inphosite.lib.model as m
import numpy

import networkx as nx
import re
from math import log

import sys
# open answer set program
filename = sys.argv[1]
f = open(filename)
f = f.read()

regex = re.compile("instance\-of\((.+), (.+)\)")
regex_links = re.compile("link\-to\((.+), (.+)\)")

instances = frozenset(regex.findall(f))
links = frozenset(regex_links.findall(f))

# create directed graph on the instances
G = nx.DiGraph()
G.add_edges_from(instances)
nodes = frozenset(G.nodes())

def siblings(id):
    sibs = {} 
    for s in G.successors(id):
        if id in classes:
            sibs.update({s : subclasses(s)})
        else:
            sibs.update({s : ins(s)})
    return sibs

def subclasses(id):
    return [n for n in G.predecessors(id) if n in classes]

def ins(id):
    return [n for n in G.predecessors(id) if n not in classes]

# parse edges file for entropy calculation
entropy = {}
f = open("output.txt")
l = f.readline()

tokens = 0
lines = 0

# count co-occurences for each pair that actually occur in candidate taxonomy.
while l:
    t = l.split()
    t = nodes.intersection(t)
    for idea in t:
        entropy.setdefault(idea, {})
        for i2 in t:
            entropy[idea].setdefault(i2, 0)
            entropy[idea][i2] += 1
    tokens += len(t)
    lines += 1
    l = f.readline()

def prob(node):
    try:
        num_x = entropy[node][node]
        px = float(num_x) / tokens
    except KeyError:
       px = -1 
    return px


def sim_lin(x, y, c):
    pc0 = prob(c)
    pc1 = prob(x)
    pc2 = prob(y)
    if pc0 == -1 or pc1 == -1 or pc2 == -1:
        #print "error", x, y ,c
        return 0
    else:
        return ((2.0 * log(pc0)) / (log(pc1) + log(pc2)))



e = {}
for node in G.nodes_iter():
    px = prob(node) 
    if px >= 0:
        e.setdefault(node, {})
        for (k, num_xy) in entropy[node].items():
            if k == node:
                e[node][k] = -1 * px * log(px)
            else:
                pxy = float(num_xy) / tokens
                e[node][k] = -1 * pxy * log((pxy/px))

s = {}
for node in G.nodes_iter():
    s.setdefault(node, {})
    
    sim_class = []
    for x in subclasses(node):
        s[node][x] = sim_lin(x, node, node)
        if s[node][x] != 0:
            sim_class.append(s[node][x])

    s[node]['cmean'] = numpy.mean(sim_class)
    s[node]['cstd'] = numpy.std(sim_class)

    sim_ins = []
    for x in ins(node):
        s[node][x] = sim_lin(x, node, node)
        if s[node][x] != 0:
            sim_ins.append(s[node][x])
    
    s[node]['imean'] = numpy.mean(sim_ins)
    s[node]['istd'] = numpy.std(sim_ins)

    


# 679 = ethics, 715 = metaethics
# 679, 715 = G | S
# 715, 679 = S | G 
#print e['679']['679'], e['715']['715'], e['679']['715'], e['715']['679']
#print entropy['679']['679'], entropy['715']['715'], entropy['679']['715'], entropy['715']['679']

# get all shortest paths and all top-level nodes
paths = nx.all_pairs_shortest_path(G)
top_level = [node for node in G.nodes_iter() if G.out_degree(node) == 0]
leaves = [node for node in G.nodes_iter() 
                   if G.out_degree(node) >= 1 and G.in_degree(node) == 0 and
                       node not in classes]
to_root = [paths[l][t] for t in top_level for l in leaves if t in paths[l]]

# for normalizing jweight and entropy
jw = [float(a[0]) for a in m.meta.Session.query(m.IdeaGraphEdge.jweight).all()]
avg_jw = numpy.mean(jw)
std_jw = numpy.std(jw)

flat_e = []
for i in e.values():
    for j in i.values():
        flat_e.append(j)
avg_e = numpy.mean(flat_e)
std_e = numpy.std(flat_e)

#ent = [float(a[0]) for a in m.meta.Session.query(m.Idea.entropy).all()]
#avg_ent = numpy.mean(ent)
#std_ent = numpy.std(ent)

# initialize values
sviolation = 0
snum = 0
eviolation = 0
enum = 0

# create query object
edge_query = m.meta.Session.query(m.IdeaGraphEdge)
idea_query = m.meta.Session.query(m.Idea)
ideas = idea_query.all()
#newid = {}
#for idea in ideas:
#    newid.update({idea.oldID : idea.ID})


for snode in G.nodes_iter():
    if snode in classes:
        continue
    # select connected nodes and iterate over them
    # remember that connected nodes are only those above
    p = paths[snode]
    
    for parent in G.successors(snode):
        if s[parent][snode] == 0:
            continue

        if snode in classes:
            avg = s[parent]['cmean']
            std = s[parent]['cstd']
        else:
            avg = s[parent]['imean']
            std = s[parent]['istd']

        if std == 0:
            sv = 0
        else:
            sv = (s[parent][snode] - avg) / std

            # add to the total sviolation and increment num of violations calc'd
            sviolation += abs(sv)
            snum += 1
        #print sv, parent, snode, avg, std, s[parent][snode], sviolation, snum

    for gnode in p.keys():
        try:
            c_gs = (e[gnode][snode] - avg_e) / std_e
            c_sg = (e[snode][gnode] - avg_e) / std_e

            #if c_gs > c_sg:
            #    continue
            #else:
            ev = c_sg - c_gs
            eviolation += ev 
            enum += 1
            #print "eviolation of %f on %s > %s" % (ev, gnode, snode)


        except KeyError:
            continue



    #calculate eviolation, but only for non-classes
    """
    if snode in classes:
        print "moving along"
        continue

    idea = idea_query.get(node)
    if idea:
        gen = 5 # calculate dynamically, maxdist is 2x depth
        for top in top_level:
            if top in p:
                # change to average path len
                gen = min(gen, len(p[top]))

        # convert entropy to standard score
        ent = (float(idea.entropy) - avg_ent) / std_ent
        # invert entropy so entropy-depth semantics are the same
        ent = 1 - ent

        # eviolation calc. 5.0 is maxdepth of tree.
        ev = abs(ent - (gen / 5.0))

        eviolation += ev
        enum += 1

    else:
        print "Could not find idea %s" % node
    """
    # using conditional entropy
        


sviolation = sviolation / snum
eviolation = eviolation / enum

print filename, sviolation, snum, eviolation, enum


"""
Normalize path length based on depth of each subtree.

Common node 
How many children each end node has
Z = commonAncestor(X,Y)
max_depth(path(X,Z))
max_depth(path(Y,Z))

Assumption is that the leaf nodes are equiv. specificity

do all leaf nodes have the same entropy?
do all depths have the same entropy?
"""
