# -*- coding: utf-8 -*-

from pygraph.classes.digraph import digraph
from pygraph.algorithms.searching import depth_first_search, breadth_first_search
import codecs
import unicodedata
import os, inspect
from cookingsite.settings import RECIPES_COLLECTION_PREFIX

prefix = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
f = codecs.open(RECIPES_COLLECTION_PREFIX+"/words/wordnet.txt", 'r', "utf-8")

graph = digraph()
nodes = set()

inverseGraph = digraph()

allL = []
for l in f:
    l = l.strip()
    if l.startswith("s;"): #synonym line
        continue
    l = l.split(u"|")
    l = [n for n in l]
    for n in l:
        if n not in nodes:
            if not n:
                continue
            nodes.add(n)
            allL.append(n)
            graph.add_node(n)
            inverseGraph.add_node(n)
    
    for i,n in enumerate(l):
        if i<len(l)-1:
            try:
                graph.add_edge((l[i], l[i+1]))
            except:
                print("could not add edge %s <-> %s" % (l[i], l[i+1]))
                raise RuntimeError("fix it")
            inverseGraph.add_edge((l[i+1], l[i]))

def knowsWord(x):
    return x in nodes

def generalize(x):
    if x not in nodes:
        return []
    return breadth_first_search(graph, root=x)[1]

def dfs(x):
    if x not in nodes:
        return None
    return depth_first_search(graph, root=x)

def bfs(x):
    if x not in nodes:
        return None
    return breadth_first_search(graph, root=x)
def bfs_depth(rootNode):
    if rootNode not in graph:
        return None
    distances = {}
    visited = { rootNode : 0}
    queue = []
    queue.append(rootNode)
    while len(queue) > 0:
        node = queue.pop(0)
        depth = visited[node] + 1
        distance = distances.get(depth, [])
        for child in graph.neighbors(node):
            if not child in visited:
                visited[child] = depth
                distance.append(child)
                queue.append(child)
        distances[depth] = distance
    return visited

def descendants(x):
    if x not in nodes:
        return []
    return breadth_first_search(inverseGraph, root=x)[1][1:]
