from django.conf.urls import include, url
from cookingsite import settings

from django.contrib import admin
admin.autodiscover()

from django import template
register = template.Library()

from recipes import views

@register.filter()
def startswith(value, arg):
    return value.startswith(arg)

urlpatterns = [
    url(r'^$', views.home, name="home"),

    # AJAX
    url(r'^ajax/recipes/(?P<recipe_slug>[-\w]+)/edittags/$', views.ajax_recipe_edit_tags, name='ajax_recipe_edit_tags'),
    url(r'^ajax/recipes/(?P<recipe_slug>[-\w]+)/rate/$', views.ajax_recipe_edit_rating, name='ajax_recipe_edit_rating'),
    url(r'^ajax/recipes/(?P<recipe_slug>[-\w]+)/scheduled-toggle/$', views.ajax_recipe_scheduled_toggle, name='ajax_recipe_scheduled_toggle'),

    # JSON
    url(r'^json/recipe/(?P<recipe_slug>[-\w]+)/$', views.json_recipe, name='json_recipe'),

    # Sources
    url(r'^sources/$', views.sources, name='sources'),
    url(r'^sources/grid(?P<ncols>\d+)/$', views.sources, name='sources'),
    url(r'^sources/grid(?P<ncols>\d+)/by_name$', views.sources, {'order_by': 'name'}, name='sources'),
    url(r'^sources/grid(?P<ncols>\d+)/by_count$', views.sources, {'order_by': 'recipe_count'}, name='sources'),
    url(r'^source/(?P<source_slug>[-\w]+)/$', views.source, name='source'),

    # Search
    url(r'^search/$', views.search, name='search'),
    url(r'^search/grid(?P<ncols>\d+)/(?P<order_by>[-\w]+)/$', views.search, name='search'),

    # Recipes
    url(r'^recipes/$', views.recipes, name='recipes'),
    url(r'^recipes/grid(?P<ncols>\d+)/$', views.recipes, name='recipes'),
    url(r'^recipes/grid(?P<ncols>\d+)/(?P<order_by>[-\w]+)/$', views.recipes, name='recipes'),
    url(r'^recipes/like/$', views.recipes_like),
    url(r'^recipes/all/$', views.recipesList, name='recipes_all'),
    url(r'^recipe/(?P<recipe_slug>[-\w]+)/$', views.recipe, name='recipe'),
    url(r'^recipe/(?P<recipe_slug>[-\w]+)/add$', views.schedule_a_recipe),

    # Tags
    url(r'^tags/$', views.tags, name='tags'),
    url(r'^tags/by_name$', views.tags, {'order_by': 'name'}, name='tags'),
    url(r'^tags/by_count$', views.tags, {'order_by': 'recipe_count'}, name='tags'),
    url(r'^tag/(?P<tag_slug>[-\w]+)/$', views.tag, name='tag'),
    url(r'^tag/(?P<tag_slug>[-\w]+)/grid(?P<ncols>\d+)/$', views.tag, name='tag'),
    url(r'^tag/(?P<tag_slug>[-\w]+)/grid(?P<ncols>\d+)/(?P<order_by>[-\w]+)/$', views.tag, name='tag'),

    # Ingredients
    url(r'^ingredients/$', views.ingredients, name='ingredients'),
    url(r'^ingredients/like/$', views.ingredients_like),
    url(r'^ingredient/(?P<ingredient_slug>[-\w]+)/$', views.ingredient, name='ingredient'),
    url(r'^ingredient/(?P<ingredient_id>((\-|_)*\d+)+)/$', views.ingredient, name='ingredient'),
    url(r'^ingredient/(?P<ingredient_id>\d+)/min-rating/(?P<min_rating>\d+\.\d+)/$', views.ingredient_minrating, name='ingredient'),
    url(r'^ingredient/(?P<ingredient_id>((\-|_)*\d+)+)/min-rating/(?P<min_rating>\d+\.d+)/$', views.ingredient_minrating, name='ingredient'),
    url(r'^search-ingredients/', views.search_ingredients, name='search_ingredients'),
    url(r'^my-ingredients', views.my_ingredients),

    # Pantry
    url(r'^pantry/$', views.pantry, name='pantry'),
    url(r'^pantry/(?P<ingredient_slug>[-\w]+)/edit/(?P<nextpage>[-\w]+)/', views.pantry_ingredient_edit, name='pantry_ingredient_edit'),
    url(r'^pantry/(?P<ingredient_slug>[-\w]+)/delete/(?P<nextpage>[-\w]+)/', views.pantry_ingredient_delete, name='pantry_ingredient_delete'),

    # Plan
    url(r'^recipes/upcoming/$', views.upcoming_recipes, name='upcoming_recipes'),
    url(r'^recipes/upcoming/(?P<recipe_id>\d+)/delete/$', views.upcoming_recipes_delete, name='upcoming_recipes_delete'),
    url(r'^recipes/upcoming/(?P<recipe_id>\d+)/edit/$', views.edit_scheduled_recipe, name='edit_scheduled_recipe'),

    # Accounts/Admin
    url(r'^accounts/login/$', views.login, name='login'),
    url(r'^accounts/logout/$', views.logout),

    # Debug
    url(r'^debug/$', views.all_ingredient_chains),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # enable the admin:
    url(r'^admin/', include(admin.site.urls)),
]
