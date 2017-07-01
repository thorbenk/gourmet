from collections import defaultdict
import functools

from django.shortcuts import render_to_response, render
from django.template import RequestContext

from recipes.models import Ingredient, MeasuredIngredient, Recipe, RecipeTag
import wordnet

def _recipes(r, request, ncols, order_by, template, baseurl="?", page_group="recipes", add_dict={}):
    if order_by == "name_asc":
        r = r.order_by("name")
    elif order_by == "name_desc":
        r = r.order_by("-name")
    elif order_by == "creation_date_asc":
        r = r.order_by("initialDate")
    elif order_by == "creation_date_desc":
        r = r.order_by("-initialDate")
        
    d = {'recipes': r,
         'baseurl': baseurl,
         'ncols': ncols,
         'page_group': page_group,
         'order_by': order_by}
    d.update(add_dict)
        
    return render(request, template, d)

def recipesMatchingIngredients(ingredientsIdsAND, min_rating):
    assert hasattr(ingredientsIdsAND, '__iter__')
    
    #find all ingredients that we are seraching for
    ings = Ingredient.objects.filter(id__in=ingredientsIdsAND).distinct().order_by("name")

    ingredientChains = [] 
    
    #for each ingredient, find its specializations
    #store all specializations in a set
    specializations = dict()
    for ing in ings:
        specializations[ing] = ing.get_specializations()
      
        sortedS = list(specializations[ing])
        sortedS.sort(key = lambda x: x.name)
     
        ic = ingChain(ing)
        if len(ic) > 0:
            ingredientChains.append( (ic, sortedS) )
    
    #find all recipes that have, for each ingredient, any of the ingredient or one of its specializations
    matchingRecipes = Recipe.objects.filter(rating__gt=min_rating)
    for ing, anyOf in specializations.items():
        anyOf.add(ing)
        #each iteration of the loop adds an 'AND' query
        #by chaining the 'filter' calls
        matchingRecipes = matchingRecipes.filter(measuredingredient__ingredient__in = anyOf).distinct() 
    matchingRecipes = matchingRecipes.distinct().order_by("name")
  
    allIngs = functools.reduce(lambda x, y : x |y, specializations.values())
    
    for r in matchingRecipes:
       m = MeasuredIngredient.objects.filter(recipe = r).filter(ingredient__in = allIngs)  
       r.ingredientsOfInterest = m 
    
    return allIngs, ingredientChains, matchingRecipes

def ingChain(ing):
    print("  finding chain for %s" % ing)

    g = wordnet.bfs_depth(ing.name)
    if g is None:
        return None

    #chain of ingredients, such as "Dose > Bohnen > Cannellini Bohnen"
    chain = defaultdict(list) 
    for ii, depth in g.items():
        try:
            ii = Ingredient.objects.get(name=ii)
            chain[depth].append((ii.name, ii.slug))
        except:
            print("could net get Ingredient for name = %s" % ii)

    c = []
    for k in sorted(chain.keys(), reverse=True):
        c.append(chain[k])
    print("built an ing chain: ", c)
    return c

def ingredientJsList():
    """create a list of all known ingredients and make a javascript array"""
    s = "[ "
    for i, l in enumerate(wordnet.allL):
        s += "'%s'" % l
        if i < len(wordnet.allL)-1:
            s += ", "
    s += " ]"
    return s

def tagJsList():
    """create a list of all known recipe tags and make a javascript array"""
    t = RecipeTag.objects.all()
    s = "[ "
    for i, l in enumerate(t):
        s += "'%s'" % t[i].name 
        if i < len(t)-1:
            s += ", "
    s += " ]"
    return s
    
def allSpecialization_name(ingredient_name):
    print("* find all specializations of '%s'" % ingredient_name)
    ingredient_name = synonyms.uniqueWord(ingredient_name)
    d = wordnet.descendants(ingredient_name)
    ids = set()
    for i, descendant in enumerate(d):
        print("  descendant %s" % descendant)
        try:
            dbDescendant = Ingredient.objects.get(name = descendant)
        except:
            continue
        ids.add(dbDescendant.id)
    #our own id
    dbDescendant = Ingredient.objects.get(name = ingredient_name)
    ids.add(dbDescendant.id)
    ids = list(ids)
    print("  --> ids = %r" % ids)
    return ids 

def allSpecialization_slug(ingredient_slug):
    dbIngredient = Ingredient.objects.get(slug = ingredient_slug)
    return allSpecialization_name(dbIngredient.name)

def allSpecialization_id(ingredient_id):
    dbIngredient = Ingredient.objects.get(id = ingredient_id)
    return allSpecialization_name(dbIngredient.name)