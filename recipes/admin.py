from recipes.models import Recipe, RecipeImage, Ingredient, \
    MeasuredIngredient, Preparation, Source, ScheduledRecipe, \
    RecipeTag, IngredientInPantry
from django.contrib import admin

class RecipeImageInline(admin.TabularInline):
    model = RecipeImage
    extra = 0

class RecipeIngredientInline(admin.TabularInline):
    model = MeasuredIngredient
    extra = 0

class RecipeAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name', )}
    inlines = [ RecipeIngredientInline, RecipeImageInline, ]

admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeImage)
admin.site.register(Ingredient)
admin.site.register(Preparation)
admin.site.register(Source)
admin.site.register(ScheduledRecipe)
admin.site.register(RecipeTag)
admin.site.register(IngredientInPantry)

