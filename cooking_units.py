#!/usr/bin/env python
# -*- coding: utf-8 -*-

import units
from units import unit, scaled_unit
import types

g  = unit('g') 
l  = unit('l')
kg = scaled_unit('kg', 'g', 1000)
ml = scaled_unit('ml', 'l', 1/1000.0)
cl = scaled_unit('cl', 'l', 1/100.0)
El = scaled_unit('El', 'ml', 15.0)
Tl = scaled_unit('Tl', 'ml', 5.0)
m  = unit('m')
Msp = unit('Msp')
Prise = unit('Prise')

import math
#http://stackoverflow.com/questions/3018758/determine-precision-and-scale-of-particular-number-in-python
def precision_and_scale(x):
    max_digits = 14
    int_part = int(abs(x))
    magnitude = 1 if int_part == 0 else int(math.log10(int_part)) + 1
    if magnitude >= max_digits:
        return (magnitude, 0)
    frac_part = abs(x) - int_part
    multiplier = 10 ** (max_digits - magnitude)
    frac_digits = multiplier + int(multiplier * frac_part + 0.5)
    while frac_digits % 10 == 0:
        frac_digits /= 10
    scale = int(math.log10(frac_digits))
    return (magnitude + scale, scale)

def num2str(n):
    if isinstance(n, int):
        return u"%d" % n
    elif isinstance(n, float):
        p, s = precision_and_scale(n)
        if s > 0:
            w = u"%%.%df" % s
            return w % n 
        else:
            return "%d" % n 
    else:
        raise RuntimeError("unknown type")

def parseNumber(s):
    s = s.replace(",", ".")
    try:
        return int(s)
    except:
        pass
    try:
        return float(s)
    except:
        pass
    s = s.replace(u"\xbd", u"1/2")
    s = s.replace(u"\xbc", u"1/4")
    if s.find("/") >= 0:
        s = s.split("/")
        assert len(s) == 2
        try:
            a = int(s[0])
            b = int(s[1])
            return a/float(b)
        except:
            return None
    return None
        
class UnspecifiedUnit:
    def __init__(self, x):
        pass
    def __str__(self):
        return ""
    def __add__(self, x):
        return self 

class CountingUnit:
    def __init__(self, x):
        self.x = x
    def __str__(self):
        return num2str(self.x)
    def __add__(self, other):
        if isinstance(other, SloppyUnit):
            s = SloppyUnit(self)
            return s + other
        else:
            self.x += other.x
            return self
    def __repr__(self):
        return u"{CountingUnit: count=%d}" % self.x

class SloppyUnit:
    def __init__(self, u=None):
        self._d = dict()
        if u is not None:
            self += u
    def __add__(self, other):
        if other.__class__ is SloppyUnit: 
            for k, v in other._d.items():
                if k in self._d:
                    self._d[k] += v
                else:
                    self._d[k] = v
        else:
            if other.__class__ in self._d:
                self._d[other.__class__] += other
            else:
                self._d[other.__class__] = other
        return self
    def __str__(self):
        s = u""
        for i, v in enumerate(self._d.values()):
            if hasattr(v, 'get_unit'):
                s += num2str(v.get_num()) + " " + str(v.get_unit())
            else:
                s += str(v)
            if i < len(self._d.values())-1:
                s += " + "
        return s
    def __repr__(self):
        s = u"{SloppyUnit:"
        for i, (k, v) in enumerate(self._d.items()):
            s += v.__repr__()
            if i < len(self._d.values())-1:
                s += " + "
        return s+"}"

class NamedUnit:
    def __init__(self, num, nameSingular, namePlural):
        self._num = num
        self._nameSingular = nameSingular
        self._namePlural = namePlural
    def __str__(self):
        if self._num == 1:
            return u"1 %s" % self._nameSingular
        else:
            return u"%s %s" % (num2str(self._num), self._namePlural)
    def __add__(self, other):
        if isinstance(other, NamedUnit) and other._namePlural == self._namePlural:
            self._num += other._num
            return self
       
        s = SloppyUnit(self)
        return s + other

def normalizeUnit(u):
    return u
        
def unitFromString(s):
    s = s.strip()

    n = parseNumber(s)
    if n is not None:
        return SloppyUnit(CountingUnit(n))
   
    if s in [u"None", u""]:
        return UnspecifiedUnit(1)

    try:
        w = s.find(" ")
        
        n = parseNumber(s[:w])
        u = s[w+1:]
    except:
        raise RuntimeError("bad unit string: '%s'" % s)

    if u == "x":
        ret = CountingUnit(n)
    elif u == "g":
        ret = g(n)
    elif u == "kg":
        ret = kg(n)
    elif u == "l":
        ret = l(n)
    elif u == "ml":
        ret = ml(n)
    elif u == "cl":
        ret = cl(n)
    elif u == "El":
        ret = El(n)
    elif u in ["EL", "Tbsp"]:
        ret = El(n)
    elif u in ["Tl", "Tsp"]:
        ret = Tl(n)
    elif u == "m":
        ret = m(n)
    elif u == "Msp":
        ret = Msp(n)
    elif u == "":
        ret = UnspecifiedUnit(n)
    elif u == "count":
        ret = CountingUnit(n)
    else:
        raise RuntimeError(u"unknown unit: %r" % u)
    return SloppyUnit(ret)
