from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

from recipes.models import Recipe
from recipes.view_helpers import _recipes

#//////////////////////////////////////////////////////////////////////////////
# RECIPE
#//////////////////////////////////////////////////////////////////////////////

@login_required
def ajax_recipe_edit_rating(request, recipe_slug):
    if not request.method == "POST":
        return JsonRespone();

    newRating = float(request.POST["rating"]);
    r = get_object_or_404(Recipe, slug=recipe_slug)
    r.rating = newRating
    r.save()
    return JsonResponse({"tags": r.rating})

@login_required
def recipe(request, recipe_slug):
    r = get_object_or_404(Recipe, slug=recipe_slug)
    return render(request, 'recipe.html', {'recipe': r})

@login_required
def recipes_like(request):
    return recipes(request, True)

@login_required
def recipes(request, onlyLiked=False, ncols=1, order_by="name_asc"):
    ncols = int(ncols)
    if onlyLiked:
        r = Recipe.objects.filter(rating__gt=1)
    else:
        r = Recipe.objects.all()

    return _recipes(r, request, ncols, order_by, "recipes.html")

@login_required
def recipesList(request):
    r = Recipe.objects.all().order_by("name")
    return render(request, 'all-recipes.html', {'recipes': r})

@login_required
def schedule_a_recipe(request, recipe_slug):
    if request.method == 'POST':
        r = get_object_or_404(Recipe, slug=recipe_slug)
        form = ScheduleARecipeForm(request.POST) # A form bound to the POST data
        if form.is_valid():
            s = ScheduledRecipe(recipe = r, multiplier=form.cleaned_data['multiplier'], scheduled = timezone.now())
            s.save()
            return HttpResponseRedirect('/recipes/upcoming')
    else:
        f = ScheduleARecipeForm(initial={'multiplier': 1.0, 'date': date.today()})
        r = get_object_or_404(Recipe, slug=recipe_slug)
        return render_to_response('schedule_a_recipe.html', \
            {'recipe': r, 'form': f, 'mode': 'add'},
            context_instance=RequestContext(request))
