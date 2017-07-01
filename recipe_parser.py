#!/usr/bin/env python
# -*- coding: utf-8 -*-

import units
import cooking_units
import wordnet
import synonyms
import re

def parseIngredientLine(l):
    tokens = l.split("|")
    assert len(tokens) == 2, tokens

    textAmount = tokens[0].strip()
    textIngredient = tokens[1].strip()
    attribs = []

    amount = cooking_units.unitFromString(textAmount)

    m = re.match("(.*)\[(.*)\].*", textIngredient)
    if m:
        ingredient = m.group(2).strip()
        textIngredient = m.group(1).strip()
    else:
        raise RuntimeError()

    ret = (textAmount, textIngredient, amount, ingredient)
    print(ret)
    return ret
