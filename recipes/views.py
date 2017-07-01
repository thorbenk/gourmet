# -*- coding: utf-8 -*-

#Python
import os
import sys
import socket
import math
import time
import calendar
from datetime import date, datetime, timedelta
from collections import defaultdict

#Django
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connection
from django.db.models import Count, Q
from django.template import Context, loader, RequestContext
from django.shortcuts import get_object_or_404, render_to_response, render
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.forms.models import modelformset_factory
import django.contrib.auth
from django.contrib.auth.decorators import login_required
from django import forms
from django.http import Http404, JsonResponse
from django.core.exceptions import ObjectDoesNotExist

import wordnet
import synonyms
from cooking_units import unitFromString

from cookingsite.settings import RECIPES_COLLECTION_PREFIX

from recipes.models import Source, Recipe, Ingredient, ScheduledRecipe, \
                           MeasuredIngredient, RecipeTag,  IngredientInPantry
from recipes.db2file import db2file

from .view_helpers import recipesMatchingIngredients, tagJsList, _recipes

from .view.v_tags import tag, tags, ajax_recipe_edit_tags
from .view.v_sources import source, sources
from .view.v_recipes import schedule_a_recipe, recipe, recipes, recipes_like, recipesList, ajax_recipe_edit_rating
from .view.v_ingredients import ingredient, ingredients, my_ingredients, search_ingredients, ingredient_minrating, ingredients_like, all_ingredient_chains

@login_required
def ajax_recipe_scheduled_toggle(request, recipe_slug):
    if request.is_ajax():
        isScheduled = True if request.POST["isScheduled"] == u"true" else False

        try:
            r = Recipe.objects.get(slug=recipe_slug);
        except ObjectDoesNotExist:
            return JsonResponse()

        if not isScheduled:
            s = ScheduledRecipe(recipe = r, multiplier=1.0, scheduled = timezone.now())
            s.save()
        else:
            s = ScheduledRecipe.objects.filter(recipe=r).delete()
        s = ScheduledRecipe.objects.filter(recipe=r)

        print("changing from", isScheduled)
        return JsonResponse({'scheduled': [t.scheduled.isoformat() for t in s]})
    else:
        return JsonResponse()

@login_required
def json_recipe(request, recipe_slug):
    try:
        r = Recipe.objects.get(slug=recipe_slug);
    except ObjectDoesNotExist:
        return JsonResponse()

    d = {
        "scheduled": [t.scheduled.isoformat() for t in ScheduledRecipe.objects.filter(recipe=r)],
        "tags": [t.name for t in r.get_tags()],
        "allTags": list(set([t.name for t in RecipeTag.objects.all()])),
        "rating": r.rating,
        "preparation": r.preparation
    }

    return JsonResponse(d)

#/////////////////////////////////////////////////////////////////////////////
# Authentication
#/////////////////////////////////////////////////////////////////////////////

def login(request):
    state = "Please log in ..."
    username = password = ''
    c = {}
    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = django.contrib.auth.authenticate(username=username,
                                                password=password)
        if user is not None:
            if user.is_active:
                django.contrib.auth.login(request, user)
                return HttpResponseRedirect(reverse('home'))
            else:
                state = "Account inactive!"
        else:
            state = "Username or password wrong."
    c.update({'state': state,
              'username': username})
    return render(request, 'login.html', c)

@login_required
def logout(request):
    django.contrib.auth.logout(request)
    return HttpResponseRedirect(reverse('home'))

#/////////////////////////////////////////////////////////////////////////////

class ScheduleARecipeForm(forms.Form):
    multiplier = forms.FloatField(required=True, max_value=10.0, min_value=0.1)

#/////////////////////////////////////////////////////////////////////////////

class AddIngredientToPantryForm(forms.Form):
    amount = forms.CharField(required=True)

    def clean_amount(self):
        data = self.cleaned_data['amount']
        try:
            unitFromString(data)
        except:
            raise forms.ValidationError(u"Not a valid amount: %s" % data)
        return data

#/////////////////////////////////////////////////////////////////////////////
# HOME
#/////////////////////////////////////////////////////////////////////////////

@login_required
def home(request):
    return render(request, 'home.html', {'page_group': 'home'})

@login_required
def search(request, ncols=1, order_by="name_asc"):
    c = {}
    if "q" in request.GET:
        q = request.GET['q']

        ncols = int(ncols)
        r = Recipe.objects.filter(Q(name__icontains=q) | Q(subtitle__icontains=q))

        params = request.GET.copy()
        if 'page' in params:
            del params['page']
        baseurl = params.urlencode()
        baseurl = "?" + baseurl
        if len(params) > 0:
            baseurl = baseurl + "&"

        return _recipes(r, request, ncols, order_by, "search-result.html", baseurl=baseurl, page_group="search", add_dict={"q": q})

    else:
        return render(request, 'search.html',
            {'page_group': 'search'})

#/////////////////////////////////////////////////////////////////////////////
# PANTRY
#/////////////////////////////////////////////////////////////////////////////

@login_required
def pantry(request):
    ings = list(IngredientInPantry.objects.all().order_by('ingredient__name'))
    return render_to_response('pantry.html', {'ingredients': ings, 'nextpage': 'pantry'})

@login_required
def pantry_ingredient_edit(request, ingredient_slug, nextpage):
    i = get_object_or_404(Ingredient, slug=ingredient_slug)
    try:
        iip = IngredientInPantry.objects.get(ingredient__slug=ingredient_slug)
        mode = "edit"
    except:
        mode = "add"

    if request.method == 'POST':
        i = get_object_or_404(Ingredient, slug=ingredient_slug)
        form = AddIngredientToPantryForm(request.POST) # A form bound to the POST data
        if form.is_valid():
            try:
                iig = IngredientInPantry.objects.get(ingredient__slug=ingredient_slug)
            except:
                iig = IngredientInPantry(ingredient = i, amount=form.cleaned_data['amount'])
            iig.amount = form.cleaned_data['amount']
            iig.save()

            if nextpage == "upcoming":
                return HttpResponseRedirect("/recipes/upcoming")
            elif nextpage == "pantry":
                return HttpResponseRedirect("/pantry")
            else:
                raise RuntimeError("unknown nextpage")
        else:
            return render_to_response('add_ingredient_to_pantry.html', \
                {'ingredient': i, 'form': form, 'mode': mode, 'nextpage': nextpage}, \
                context_instance=RequestContext(request))

    #we have not submitted yet
    try:
        iip = IngredientInPantry.objects.get(ingredient__slug=ingredient_slug)
        form = AddIngredientToPantryForm(initial={'amount': iip.amount})
        mode = "edit"
    except:
        form = AddIngredientToPantryForm()
        mode = "add"
    return render(request, 'add_ingredient_to_pantry.html', \
        {'ingredient': i, 'form': form, 'mode': mode, 'nextpage': nextpage})

@login_required
def pantry_ingredient_delete(request, ingredient_slug, nextpage):
    i = IngredientInPantry.objects.get(ingredient__slug = ingredient_slug)
    i.delete()

    if nextpage == "upcoming":
        return HttpResponseRedirect("/recipes/upcoming")
    elif nextpage == "pantry":
        return HttpResponseRedirect("/pantry")
    else:
        raise RuntimeError("unknown nextpage")

@login_required
def edit_scheduled_recipe(request, recipe_id):
    if request.method == 'POST':
        sr = get_object_or_404(ScheduledRecipe, id=recipe_id)
        form = ScheduleARecipeForm(request.POST) # A form bound to the POST data
        if form.is_valid():
            sr.multiplier = form.cleaned_data['multiplier']
            sr.save()
            return HttpResponseRedirect('/recipes/upcoming')
    else:
        sr = get_object_or_404(ScheduledRecipe, id=recipe_id)
        f = ScheduleARecipeForm(initial={'multiplier': sr.multiplier})

        r = get_object_or_404(Recipe, id=sr.recipe.id)
        return render(request, 'schedule_a_recipe.html', \
                {'recipe': r, 'form': f, 'mode': 'edit', 'scheduledRecipeId': sr.id})

#/////////////////////////////////////////////////////////////////////////////
# upcoming
#/////////////////////////////////////////////////////////////////////////////

@login_required
def upcoming_recipes(request):
    scheduledRecipes = ScheduledRecipe.objects.all()

    allIngredients = defaultdict(list)
    totalAmounts  = dict()

    recipes = [] #hold tuples (<number>, <recipe>)

    for i, scheduledRecipe in enumerate(scheduledRecipes):
        ings = scheduledRecipe.recipe.get_ingredients()
        recipes.append( (i+1, scheduledRecipe) )

        multiplier = scheduledRecipe.multiplier

        for ing in ings:

            amount = unitFromString(ing.amount)
            allIngredients[ing.ingredient].append((amount, i+1, scheduledRecipe.recipe))
            if ing.ingredient not in totalAmounts:
                totalAmounts[ing.ingredient] = amount
            else:
                totalAmounts[ing.ingredient] += amount

    categorizedIngs = defaultdict(list)
    for ingredient in allIngredients.keys():
        g = wordnet.generalize(ingredient.name)
        if g == []:
            g = [ingredient]

        try:
            iip = IngredientInPantry.objects.get(ingredient__name = ingredient.name)
        except:
            iip = None

        if iip:
            try:
                amountInPantry = str( unitFromString(iip.amount) )
                if amountInPantry == "":
                    amountInPantry = "ja"
            except:
                raise RuntimeError("not a valid amount: '%s' of ingredient %s in pantry" % (iip.amount, iip.ingredient.name))
        else:
            amountInPantry = ""
        categorizedIngs[ g[-1] ].append((ingredient, allIngredients[ingredient], totalAmounts[ingredient], amountInPantry))

    categorizedIngs = dict(categorizedIngs) #django can only deal with dict, not defaultdict

    return render(request, 'upcoming.html', {
        'scheduledRecipes':       recipes,
        'page_group': 'plan',
        'categorizedIngredients': categorizedIngs
        })

@login_required
def upcoming_recipes_delete(request, recipe_id):
    r = ScheduledRecipe.objects.get(id = recipe_id)
    r.delete()
    return HttpResponseRedirect('/recipes/upcoming')
