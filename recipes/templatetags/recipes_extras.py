from django import template
from django.core.urlresolvers import resolve, Resolver404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404, render_to_response, render

register = template.Library()
 
def grouped(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]
 
@register.filter()
def startswith(value, arg):
    return value.startswith(arg) 

@register.filter()
def group_by(value, arg):
    return grouped(value, arg)

def recipe_list(context):
    ncols   = context["ncols"] if "ncols" in context else 1
    page    = context['request'].GET["page"] if "page" in context['request'].GET else 1
    r       = context["recipes"]
    baseurl = context["baseurl"]
    
    itemsPerPage =  {1:12, 4:12, 6:24}
    assert ncols in [1,4,6], "ncols=%d" % ncols
    paginator = Paginator(r, itemsPerPage[ncols])
    try:
        r = paginator.page(page)
    except PageNotAnInteger:
        r = paginator.page(1)
    except EmptyPage:
        r = paginator.page(paginator.num_pages)
    page_numbers = [i for i in range(1, paginator.num_pages+1)]
        
    return {'recipes': r,
            'baseurl': baseurl,
            'ncols': ncols,
            'page_numbers': page_numbers,
            'page': page}
register.inclusion_tag("recipelist.html", takes_context=True)(recipe_list)

# http://blog.scur.pl/2012/09/highlighting-current-active-page-django/
def current_url_equals(context, url_name, **kwargs):
    resolved = False
    try:
        resolved = urlresolvers.resolve(context.get('request').path)
    except:
        pass
    matches = resolved and resolved.url_name == url_name
    if matches and kwargs:
        for key in kwargs:
            kwarg = kwargs.get(key)
            resolved_kwarg = resolved.kwargs.get(key)
            if not resolved_kwarg or kwarg != resolved_kwarg:
                return False
    return matches

@register.simple_tag(takes_context=True)
def current(context, url_name, return_value='active', **kwargs):
    matches = current_url_equals(context, url_name, **kwargs)
    return return_value if matches else ''
