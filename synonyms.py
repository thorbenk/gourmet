# -*- coding: utf-8 -*-

from collections import defaultdict
import recipes
import codecs
import os, inspect
from cookingsite.settings import RECIPES_COLLECTION_PREFIX

d = dict()
reverseDict = defaultdict(set)
prefix = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

f = codecs.open(RECIPES_COLLECTION_PREFIX+"/words/wordnet.txt", 'r', 'utf-8')
for l in f:
    l = l.strip()
    if not l.startswith("s;"): #non-synonym line
        continue
    l = l[2:]

    l = l.split(u"|")
    assert isinstance(l, list) 
    l = [ll for ll in l]
    for ll in l:
        reverseDict[l[0]].add(ll)
    if len(l) == 1:
        continue
    for x in l[1:]:
        d[x] = l[0]
        for ll in l:
            reverseDict[x].add(ll)

def synonyms(w):
    if w in reverseDict:
        return reverseDict[w]
    else:
        return set([w])

def uniqueWord(w):
    if w in d:
        return d[w]
    else:
        return w
