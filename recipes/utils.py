# -*- coding: utf-8 -*-

from django.template.defaultfilters import slugify

def germanslugify(value):
    replacements = [(u'ß', u'ss'),
                    (u'ä', u'ae'),
                    (u'Ä', u'AE'),
                    (u'ö', u'oe'),
                    (u'Ö', u'OE'),
                    (u'ü', u'ue'),
                    (u'Ü', u'UE')]
    for (s, r) in replacements:
        value = value.replace(s, r)
    return slugify(value)