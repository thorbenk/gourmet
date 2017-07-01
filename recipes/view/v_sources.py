import socket
import sys
import os

from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404, render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.db.models import Count

from cookingsite.settings import RECIPES_COLLECTION_PREFIX

from recipes.models import Source
from recipes.view_helpers import _recipes

#/////////////////////////////////////////////////////////////////////////////
# SOURCES
#/////////////////////////////////////////////////////////////////////////////

@login_required
def sources(request, ncols=1, order_by='name'):
    ncols = int(ncols)
    assert ncols in [1,4,6], "ncols=%d" % ncols
    itemsPerPage =  {1:12, 4:12, 6:24}
    if order_by == 'name':
        sources = Source.objects.all().annotate(recipe_count=Count('recipe')).order_by('name')
    elif order_by == 'recipe_count':
        sources = Source.objects.all().annotate(recipe_count=Count('recipe')).order_by('-recipe_count')
        
    paginator = Paginator(sources, itemsPerPage[ncols])
    page = request.GET.get('page')
    try:
        sources = paginator.page(page)
    except PageNotAnInteger:
        sources = paginator.page(1)
    except EmptyPage:
        sources = paginator.page(paginator.num_pages)
    page_numbers = [i for i in range(1, paginator.num_pages+1)]
        
    return render(request, 'sources.html',
        {'sources': sources, 
         'page_group': 'sources',
         'page_numbers': page_numbers,
         'ncols': ncols,
         'order_by': order_by})

@login_required
def source(request, source_slug):
    src = Source.objects.get(slug=source_slug)
    r = src.get_recipes()
    
    return _recipes(r, request, ncols=1, order_by="", template="source.html", baseurl="?", page_group="sources", add_dict={"source": src, "recipes": r})