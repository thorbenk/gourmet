from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.db.models import Count

from cookingsite.settings import RECIPES_COLLECTION_PREFIX

from recipes.models import Ingredient 

from recipes.view_helpers import recipesMatchingIngredients

#//////////////////////////////////////////////////////////////////////////////
# INGREDIENT
#//////////////////////////////////////////////////////////////////////////////

@login_required
def ingredient_minrating(request, ingredient_id, min_rating):
    return ingredient(request, ingredient_id, float(min_rating))

@login_required
def all_ingredient_chains(request):
    ings = Ingredient.objects.all().order_by("name")
    chains = []
    for ing in ings:
        chain = ingChain(ing)
        if chain is not None:
            chains.append(chain)
            
    return render_to_response('all-ing-chains.html',
        {'ingredientChains': chains})

@login_required
def my_ingredients(request):
    ids       = request.session['ingredient_ids_AND']
    minRating = request.session['min_rating']
    print( "my-ingredients: ingredient_ids_AND = %r" % ids)
    print( "my-ingredients: minRating          = %r" % minRating)
    
    return recipes_matching_ingredients(request, ids, min_rating = minRating)

@login_required
def ingredient(request, ingredient_slug, min_rating = 0):
    print("* showing ingredient %s" % ingredient_slug)

    i = get_object_or_404(Ingredient, slug=ingredient_slug) 
    
    #return ingredient_helper(request, ids, query, min_rating = 0)
    return recipes_matching_ingredients(request, [i.id])

@login_required
def recipes_matching_ingredients(request, ingredientsIdsAND, min_rating=0.0):
    allIngs, ingredientChains, matchingRecipes = recipesMatchingIngredients(ingredientsIdsAND, min_rating) 
    return render_to_response('ingredient.html',
        {'recipes': matchingRecipes, \
         'ingredients': allIngs, \
         'ingredientChains': ingredientChains \
         })
        
@login_required
def search_ingredients(request):
    if request.method == 'POST':
        query = request.POST["query"]
        minRating = float(request.POST["recipe_rating"])
        query = query.split(",")
        print("* SEARCHING FOR RECIPES WITH INGREDIENTS: %r, rating > %f" % (query, minRating))
        ids = []

        validQuery = []
        problems = []
        ids = []
        for i, q in enumerate(query):
            q = synonyms.uniqueWord(q)
            dbIngredient = Ingredient.objects.filter(name = q) 
            if dbIngredient:
                assert len(dbIngredient) == 1
                validQuery.append(q)
                ids.append(dbIngredient[0].id)
            else:
                problems.append(q)
        if len(problems) > 0:
            return render_to_response('ingredients-search.html',
                {'ingredients_js_list': ingredientJsList(),
                    'initialQuery': ','.join(validQuery),
                    'problems': problems},
                context_instance=RequestContext(request))
        else:
            #print ids
            #s = "_".join([str(x) for x in ids])

            request.session['ingredient_ids_AND'] = ids
            request.session['min_rating']     = minRating

            return HttpResponseRedirect('/my-ingredients')

    else:
        return render_to_response('ingredients-search.html',
            {'ingredients_js_list': ingredientJsList()},
            context_instance=RequestContext(request))
 
@login_required
def ingredients_like(request):
    return ingredients(request, True)

@login_required
def ingredients(request, onlyLiked=False):
    if onlyLiked:
        i = Ingredient.objects.filter(measuredingredient__recipe__rating__gt=1)
    else:
        i = Ingredient.objects
    i = i.annotate(num_recipes = Count('measuredingredient__recipe')).order_by("name")
    return render_to_response('ingredients.html',
        {'ingredients': i})
