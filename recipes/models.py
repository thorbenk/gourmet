from collections import defaultdict
import re
import os

from django.db import models
from django.template.defaultfilters import slugify
from django.db.models import permalink
from django.urls import reverse
from cooking_units import unitFromString
import synonyms
import wordnet

#//////////////////////////////////////////////////////////////////////////////

class UnsavedForeignKey(models.ForeignKey):
    # A ForeignKey which can point to an unsaved object
    allow_unsaved_instance_assignment = True

#//////////////////////////////////////////////////////////////////////////////

class RecipeTag(models.Model):
    name = models.CharField(max_length=128, null=False)
    slug = models.SlugField(max_length=128, null=False)

    @classmethod
    def add(self, name):
        o = RecipeTag.objects.filter(name = name)
        if len(o) > 0:
            return o[0]
        else:
            assert name
            newTag = RecipeTag(name = name, slug=slugify(name))
            newTag.save()
            return newTag

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tag', args=[self.slug])

#//////////////////////////////////////////////////////////////////////////////

class Source(models.Model):
    slug  = models.SlugField()
    name  = models.CharField(max_length=256)
    label = models.CharField(max_length=256)
    image = models.ImageField(upload_to=".")

    def __unicode__(self):
        return self.name

    def dataEqual(self, o):
        return o.slug  == self.slug and \
               o.name  == self.name and \
               o.label == self.label and \
               o.image == self.image

    def thumb(self):
        return str(self.image)[0:-4] + "_sq_320.jpg"

    def get_recipes(self):
        return Recipe.objects.filter(source=self).order_by('name')

    def num_recipes(self):
        return Recipe.objects.filter(source=self).count()

    def get_absolute_url(self):
        return reverse('source', args=[self.slug])

#//////////////////////////////////////////////////////////////////////////////

class Ingredient(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128)

    def __str__(self):
        return self.name

    def get_specializations(self):
        ingredient_name = synonyms.uniqueWord(self.name)
        d = wordnet.descendants(ingredient_name)

        specializations = set()

        for i, descendant in enumerate(d):
            try:
                dbDescendant = Ingredient.objects.get(name = descendant)
            except:
                continue
            specializations.add(dbDescendant)
        return specializations

    def get_absolute_url(self):
        return reverse('ingredient', args=[self.slug])

#//////////////////////////////////////////////////////////////////////////////

class Preparation(models.Model):
    how = models.CharField(max_length=256)

    def __unicode__(self):
        return self.how

#//////////////////////////////////////////////////////////////////////////////

class Recipe(models.Model):
    name        = models.CharField(max_length=512)
    subtitle    = models.CharField(max_length=512, null=True)
    filename    = models.CharField(max_length=512, null=False)
    slug        = models.SlugField(max_length=191) #see https://code.djangoproject.com/ticket/18392
    pdf         = models.CharField(max_length=256, null=True)

    #date
    initialDate = models.DateTimeField('date published', null=True)
    updateDate  = models.DateTimeField('date updated', null=True)

    #images
    imageSquare = models.CharField(max_length=512)

    #source
    source      = models.ForeignKey(Source, null=True)
    page        = models.IntegerField(null = True)
    url         = models.URLField(null = True)

    #nutrition
    kcal        = models.FloatField(null=True)
    carbs       = models.FloatField(null=True)
    fat         = models.FloatField(null=True)
    proteins    = models.FloatField(null=True)
    portions    = models.CharField(max_length=255, null=True)

    #time
    duration    = models.CharField(max_length=255, null=True)

    #metadata
    tags        = models.ManyToManyField(RecipeTag)
    rating      = models.FloatField(null=True)

    #actual recipe
    ingredients = models.ManyToManyField(Ingredient, through='MeasuredIngredient')
    preparation = models.TextField(null=True)

    @property
    def thumb(self):
        return self.imageSquare.replace("sq", "sq_320").replace("png", "jpg")

    def hasBug(self):
      return any([t.name == "bug" for t in self.tags.all()])

    def get_tags(self):
        return self.tags.all().order_by("name")

    def get_steps(self):
        lines = self.preparation.split("\n")
        steps = defaultdict(list)
        i = 0
        while(i < len(lines)):
            l = lines[i].strip()
            if l == "":
                i+=1
                continue
            m = re.search("^([0-9]+)\.", l)
            if m is not None:
                step = int(m.group(1))
            elif l.startswith("- "):
                steps[step].append(l[2:].strip())
            i+=1

        return steps.items()

    def add_tag(self, tag):
        allTags = [tag.name for tag in self.tags.all()]
        if tag not in allTags:
            newTag = RecipeTag.add(tag)
            self.tags.add(newTag)

    def scheduled(self):
        return ScheduledRecipe.objects.filter(recipe=self).order_by('scheduled')

    def get_images(self):
        return RecipeImage.objects.filter(recipe = self)

    def get_ingredients(self):
        return MeasuredIngredient.objects.filter(recipe = self).order_by('textIngredient')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('recipe', args=[self.slug])

    @permalink
    def get_tags_edit_url(self):
        return reverse('recipes.views.recipe_edit_tags', args=[{'recipe_slug': self.slug}])

#//////////////////////////////////////////////////////////////////////////////

class IngredientInPantry(models.Model):
    ingredient   = UnsavedForeignKey(Ingredient)
    amount       = models.CharField(max_length=256)

    def formattedAmount(self):
        return unitFromString(self.amount)

    def __str__(self):
        return "'%s' of '%s'" % (self.amount, self.ingredient)

#//////////////////////////////////////////////////////////////////////////////

class MeasuredIngredient(models.Model):
    ingredient     = UnsavedForeignKey(Ingredient)
    recipe         = UnsavedForeignKey(Recipe)
    amount         = models.CharField(max_length=64)
    textIngredient = models.CharField(max_length=256)
    textAmount     = models.CharField(max_length=64)

    def formattedAmount(self):
        return unitFromString(self.amount)

    def __str__(self):
        return u"%s %s %s" % (self.amount, self.ingredient.name, self.textIngredient)

#//////////////////////////////////////////////////////////////////////////////

class RecipeImage(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='images')
    image = models.CharField(max_length=512)

    def __unicode__(self):
        return self.image

#//////////////////////////////////////////////////////////////////////////////

class ScheduledRecipe(models.Model):
    recipe = models.ForeignKey(Recipe)
    multiplier = models.FloatField()
    scheduled = models.DateField()
