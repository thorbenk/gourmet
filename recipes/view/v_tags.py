import socket
import sys
import os

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.db.models import Count

from cookingsite.settings import RECIPES_COLLECTION_PREFIX

from recipes.view_helpers import tagJsList, _recipes
from recipes.models import Recipe, RecipeTag
from recipes.db2file import db2file

@login_required
def ajax_recipe_edit_tags(request, recipe_slug):
    if not request.method == "POST":
        return JsonRespone();

    newTags = set(request.POST["recipe_tags"].split(","))
    newTags = set([x for x in newTags if x]) #remove possible empty strings

    r = get_object_or_404(Recipe, slug=recipe_slug)
    currentTags = set([x.name for x in r.tags.all()])

    toAdd = newTags.difference(currentTags)
    toDelete = currentTags.difference(newTags)

    if toAdd or toDelete:
        for tag in toAdd:
            dbTag = RecipeTag.add(tag)
            r.tags.add(dbTag)
        for tag in toDelete:
            r.tags.filter(name=tag).delete()
        r.save()

        db2file(r.slug)
        cmd =  "cd '%s'" % RECIPES_COLLECTION_PREFIX
        cmd += " && git commit -a --author=\"%s <%s>\"" % (request.user.username, request.user.email)
        cmd += " -m \"change tags of %s" % (r.slug,) + "\n\nChange via web-interface running on "+socket.gethostname()+"\""
        print >>sys.stderr, cmd
        os.system(cmd)

        if socket.gethostname() != "t570":
            cmd =  "cd '%s'" % RECIPES_COLLECTION_PREFIX
            cmd += " && git push origin master"
            print >>sys.stderr, cmd
            os.system(cmd)

    currentTags = list(set([x.name for x in r.tags.all()]))
    return JsonResponse({"tags": currentTags})

@login_required
def recipe_edit_tags(request, recipe_slug):
    if request.method == "POST":
        newTags = set(request.POST["recipe_tags"].split(","))
        newTags = set([x for x in newTags if x]) #remove possible empty strings
        
        r = get_object_or_404(Recipe, slug=recipe_slug)
        currentTags = set([x.name for x in r.tags.all()])
        
        toAdd = newTags.difference(currentTags)
        toDelete = currentTags.difference(newTags)
        
        if toAdd or toDelete:
            for tag in toAdd:
                dbTag = RecipeTag.add(tag)
                r.tags.add(dbTag)
            for tag in toDelete:
                r.tags.filter(name=tag).delete()
            r.save()
            
            db2file(r.slug)
            cmd =  "cd '%s'" % RECIPES_COLLECTION_PREFIX
            cmd += " && git commit -a --author=\"%s <%s>\"" % (request.user.username, request.user.email)
            cmd += " -m \"change tags of %s" % (r.slug,) + "\n\nChange via web-interface running on "+socket.gethostname()+"\""
            print >>sys.stderr, cmd
            os.system(cmd)
            
            if socket.gethostname() != "t570":
                cmd =  "cd '%s'" % RECIPES_COLLECTION_PREFIX
                cmd += " && git push origin master"
                print >>sys.stderr, cmd 
                os.system(cmd)
        
        return HttpResponseRedirect(reverse("recipes.views.recipe", args=(recipe_slug,)))
    else:
        r = get_object_or_404(Recipe, slug=recipe_slug)
        initialTags = ",".join(sorted([x.name for x in r.tags.all()]))
        return render_to_response('recipe-edit-tags.html', \
            {'recipe': r, 'tag_js_list': tagJsList(), 'initial_tags': initialTags }, \
            context_instance=RequestContext(request))
    
#/////////////////////////////////////////////////////////////////////////////
# TAGS
#/////////////////////////////////////////////////////////////////////////////

@login_required
def tags(request, order_by='name'):
    if order_by == 'name':
        tt = RecipeTag.objects.annotate(recipe_count=Count('recipe')).order_by(order_by)
    else:
        tt = RecipeTag.objects.annotate(recipe_count=Count('recipe')).order_by('-recipe_count')
    
    return render(request, 'tags.html',
        {'tags': tt,
         'page_group': 'tags',
         'order_by': order_by})

@login_required
def tag(request, tag_slug=None, ncols=1, order_by="name_asc"):
    ncols = int(ncols)
    
    query_tag = get_object_or_404(RecipeTag, slug=tag_slug)
    r = query_tag.recipe_set.all()
   
    return _recipes(r, request, ncols, order_by, "tag.html",
                    baseurl="?", page_group="tags", add_dict={"tag": query_tag})
