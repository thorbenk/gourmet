#Python
import time
import pytz
from datetime import datetime
import os, errno, sys
import codecs
import fnmatch
import re
from collections import defaultdict
import pytz
import shutil

#Django
from django.utils import timezone

#Pillow
from PIL import Image

#this project
from recipes.utils import germanslugify
from recipes.models import Ingredient, Preparation, MeasuredIngredient, \
                           Recipe, RecipeImage, Source, RecipeTag, \
                           IngredientInPantry, ScheduledRecipe
import recipe_parser as parser
import wordnet
import synonyms
from cooking_units import unitFromString

#-----------------------------------------------------------------------------

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def mkThumb(inFile, outFile, shape):
    if os.path.exists(outFile):
        return

    print("thumbnail %s -> %s" % (inFile, outFile))
    img = Image.open(inFile)
    img.thumbnail(shape)
    img.save(outFile)

#-----------------------------------------------------------------------------

class FlatRecipeParser:
    def __init__(self, prefix, dryRun=True):
        self.prefix = prefix
        self.dryRun = dryRun

        self.sources = {}
        self.ingredients = {}         # slug -> ingredient object
        self.measuredIngredients = {} # slug -> measured ingredient object
        self.recipes = {}
        self.tags = {}
        self.recipeToTags = defaultdict(set)

        bookFiles   = [os.path.join(dirpath, f) for dirpath, dirnames, files in os.walk(prefix+"/books/") \
                                                for f in fnmatch.filter(files, '*.txt')]
        recipeFiles = [os.path.join(dirpath, f) for dirpath, dirnames, files in os.walk(prefix+"/recipes/") \
                                                for f in fnmatch.filter(files, '*.txt')]
        bookFiles   = sorted(bookFiles)
        recipeFiles = sorted(recipeFiles)

        t = time.time()
        RecipeTag.objects.all().delete()
        Source.objects.all().delete()
        Ingredient.objects.all().delete()
        Preparation.objects.all().delete()
        Recipe.objects.all().delete()
        IngredientInPantry.objects.all().delete()
        MeasuredIngredient.objects.all().delete()
        RecipeImage.objects.all().delete()
        ScheduledRecipe.objects.all().delete()
        print("> clean database")
        print("  took %.4f sec" % (time.time()-t))

        self.parseBooks(bookFiles, verbose=True)
        self.parseRecipes(recipeFiles, verbose=True)

    def parseBookFile(self, bookFile, verbose=True):
        f = codecs.open(bookFile, 'r', 'utf-8')
        lines = f.readlines()
        f.close()

        d = {}
        requiredKeys= ["title", "label", "image"]

        for line in lines:
            line = line.strip()
            if ":" not in line:
                continue
            pos = line.find(":")
            key, value = line[0:pos].strip(), line[pos+1:].strip()

            assert key not in d
            d[key] = value

        for key in requiredKeys:
            if not key in d:
                print("In file '%s':" % bookFile)
                print("Required key '%s' not found" % key)
                sys.exit()

        slug = os.path.basename(bookFile)[:-4]

        s = Source(name   = d["title"],
                    label = d["label"],
                    slug  = d["label"],
                    image = d["image"])

        mkdir_p("static/images/books")
        imgSq = self.prefix+"/books/%s_sq.jpg" % slug
        assert os.path.exists(imgSq), "%s does not exist" % imgSq
        thumbSq = "static/images/books/%s_sq_320.jpg" % slug

        mkThumb(imgSq, thumbSq, (320,320))

        return s

    def parseBooks(self, bookFiles, verbose=True):
        t = time.time()
        sources = Source.objects.all()
        newSources = []
        for i, bookFile in enumerate(bookFiles):
            source = self.parseBookFile(bookFile, verbose=False)
            newSources.append(source)
        print("> created %d books" % len(newSources))
        Source.objects.bulk_create(newSources)
        self.sources = {o.slug: o for o in Source.objects.all()}
        print("  took %.4f sec" % (time.time()-t))

    def _update_tags(self):
        t = time.time()
        RecipeTag.objects.bulk_create(self.tags.values())
        print("> creating tags")
        print("  took %.4f sec." % (time.time()-t))

    def _update_recipes(self):
        t = time.time()
        recipes = Recipe.objects.all()
        newRecipes = []
        nUpdated = 0
        for rSlug, r in self.recipes.items():
            newRecipes.append(r)
        Recipe.objects.bulk_create(newRecipes)
        print("> created %d recipes" % len(newRecipes))
        sys.stdout.write("  took %.4f sec\n" % (time.time()-t))

        t = time.time()
        ThroughModel = Recipe.tags.through
        tags = {o.slug: o for o in RecipeTag.objects.all()}
        recipes = Recipe.objects.all()
        tagsThrough = []
        for r in recipes:
            recipeTags = [tags[x] for x in self.recipeToTags[r.slug]]
            tagsThrough.extend(
                [ThroughModel(recipe=r, recipetag=x) for x in recipeTags]
            )
        ThroughModel.objects.bulk_create(tagsThrough)
        sys.stdout.write("> assigning tags to recipes\n")
        sys.stdout.write("  took %.4f sec\n" % (time.time()-t))

    def _update_ingredients(self):
        t = time.time()
        print("> saving/updating %d ingredients" % (len(self.ingredients)))
        newIngredients = []
        nUpdated = 0
        for ingSlug, ing in self.ingredients.items():
            newIngredients.append(ing)
        Ingredient.objects.bulk_create(newIngredients)
        print("  created %d ingredients" % \
              (len(newIngredients)))
        print("  took %.4f sec" % (time.time()-t,))

    def _update_measured_ingredients(self):
        print("> updating measured ingredients")
        t = time.time()

        recipes     = {o.slug: o for o in Recipe.objects.all()}
        ingredients = {o.slug: o for o in Ingredient.objects.all()}

        for key, mi in self.measuredIngredients.items():
            ingSlug, rSlug = key
            mi.ingredient = ingredients[ingSlug]
            mi.recipe     = recipes[rSlug]

        MeasuredIngredient.objects.bulk_create(self.measuredIngredients.values())
        print("  took %.4f sec" % (time.time()-t))

    def parseRecipes(self, recipeFiles, verbose=True):
        for i, recipeFile in enumerate(recipeFiles):
            print("* recipe {:>4}/{:>4}: {}".format(i, len(recipeFiles), os.path.basename(recipeFile)[:-4]))
            self.parseRecipe(recipeFile, verbose=False)

        self._update_tags()
        self._update_recipes()
        self._update_ingredients()
        self._update_measured_ingredients()

    def _recipe_parse_title(self, lines, i):
        title = None
        subtitle = None
        while i < len(lines):
            l = lines[i].strip()
            if i == len(lines) - 1:
                return (i, title, subtitle)
            nextLine = lines[i+1].strip()

            if l.startswith("# "):
                title = l[1:].strip()
                if not lines[i+2].startswith("## "):
                    i+=2
                    return (i, title, subtitle)
                else:
                    i+=1
                    continue
            elif l.startswith("## "):
                subtitle = l[2:].strip()
                i+=2
                return (i, title, subtitle)
            i+=1
        return (i, title, subtitle)

    def _recipe_parse_steps(self, lines, i):
        if i >= len(lines):
            return None
        assert lines[i].strip() != ""
        return "".join(lines[i:])

    def _recipe_parse_meta(self, lines, i, d):
        while(True):
            if i == len(lines)-1:
                raise RuntimeError("End of file reached while parsing meta information")
            l = lines[i].strip()

            pos = l.find(":")
            assert pos >=0, u"file = %r, line = %r" % ("TODO", l)
            key, value = l[0:pos].strip(), l[pos+1:].strip()
            assert key not in d, u"key %r already in use" % key
            if key == "source":
                pos = value.find("/")
                if pos >= 0:
                    d["source_book"] = value[0:pos]
                    d["source_page"] = value[pos+1:]
                else:
                    d["source_book"] = value
                    d["source_page"] = 0
            elif key == "image":
                images = [x.strip() for x in value.split(",")]
            elif key == "tags":
                tags = [x.strip() for x in value.split(",")]
                tags = [x for x in tags if x]
                d["tags"] = tags
            elif key == "created":
                t = time.strptime(value, "%d.%m.%Y")
                date = datetime(t.tm_year, t.tm_mon, t.tm_mday, tzinfo=pytz.timezone("Europe/Berlin"))
                d["initialDate"] = date
            elif key == "published":
                if value.startswith("KW "):
                    week, year = value[3:].split("/")
                    X = "%04d%02d1" % (int(year), int(week))
                    date = datetime.strptime(X, '%Y%W%w')
                    berlin = pytz.timezone("Europe/Berlin")
                    date = datetime(date.year, date.month, date.day, tzinfo=berlin)
                    d["published"] = date
                else:
                    raise RuntimeError("Did not understand publish date")
            else:
                d[key] = value

            i+=1
            if lines[i].strip() == "":
                if "initialDate" not in d:
                    d["initialDate"] = datetime(2010, 1, 1, tzinfo=pytz.timezone("Europe/Berlin")) #old date
                return i+1

    def _recipe_parse_ingredients(self, lines, i, r, verbose=False):
        while(True):
            l = lines[i].strip()

            if i > len(lines)-1:
                return i

            if l == "":
                return i+1
            elif l.startswith("=="):
                i+=1
                continue

            textAmount, textIngredient, amount, ingredient = parser.parseIngredientLine(l)

            if not wordnet.knowsWord(synonyms.uniqueWord(ingredient)):
                print("wordnet does not know '%s'" % (ingredient))
                print("synonyms are '%r'" % (synonyms.uniqueWord(ingredient)))
                print("original text line was: '%s'" % l)
                raise RuntimeError("Please fix!")

            g = wordnet.generalize(ingredient)
            if len(g) == 0:
                g = [ing]
            for generalizedIngredient in g:
                if not self.dryRun:
                    slug = germanslugify(generalizedIngredient)
                    ingredientEntry = Ingredient(name=generalizedIngredient, slug=slug)
                    self.ingredients[slug] = ingredientEntry
                    #ingredient.save()
                elif verbose:
                    print("  adding ingredient '%s'" % generalizedIngredient)

            if len(g) > 0:
                ingredient = g[0]

            if verbose:
                print("  adding ingredient '%s' of '%s'" % (amount, ingredient))

            if not self.dryRun:
                ingredient = germanslugify(ingredient)
                try:
                    ingObject = self.ingredients[ingredient]
                except:
                    print(self.ingredients.keys())
                    raise RuntimeError("Could not find ingredient '%r'" % ingredient)

                mi = MeasuredIngredient(ingredient     = ingObject,
                                        recipe         = r,
                                        amount         = amount,
                                        textIngredient = textIngredient,
                                        textAmount     = textAmount)
                self.measuredIngredients[ (ingredient, r.slug) ] = mi

            i+=1

    def parseRecipe(self, recipeFile, verbose=True):
        if "noimages" in recipeFile or "pdfs" in recipeFile:
            return

        slug = os.path.basename(recipeFile)[:-4]

        dirname = os.path.dirname(recipeFile)
        dirname_rel = dirname[len(self.prefix):]

        imgSq = dirname+"/%s_sq.%%s" % slug
        imgSq_rel = dirname_rel[1:]+"/%s_sq.%%s" % slug
        imgType = None
        if os.path.exists(imgSq % "png"):
            imgType = "png"
        elif os.path.exists(imgSq % "jpg"):
            imgType = "jpg"
        else:
            raise RuntimeError("%s does not exist" % imgSq)

        f = codecs.open(recipeFile, 'r', 'utf-8')
        lines = f.readlines()
        f.close()

        d = {}
        tags = []
        r = None
        rCreated = False

        title    = None
        subtitle = None
        steps    = defaultdict(list)

        i = 0
        i, title, subtitle = self._recipe_parse_title(lines, i)
        i = self._recipe_parse_meta(lines, i, d)

        slug = os.path.basename(recipeFile)[:-4]
        r = Recipe(name=title,
                   subtitle=subtitle,
                   filename=os.path.relpath(recipeFile, self.prefix),
                   page=d["source_page"],
                   slug = slug,
                   initialDate = d["initialDate"] if "initialDate" in d else None,
                   updateDate = None,
                   rating=2,
                   imageSquare=imgSq_rel % imgType)
        if "kcal" in d:
            r.kcal = float(d["kcal"])
        if "carbs" in d:
            r.carbs = float(d["carbs"])
        if "proteins" in d:
            r.proteins = float(d["proteins"])
        if "fat" in d:
            r.fat = float(d["fat"])
        if "serves" in d:
            r.portions = d["serves"]
        if "published" in d:
            r.initialDate = d["published"]

        ref_source = self.sources[d["source_book"]]
        r.source = ref_source

        self.recipes[slug] = r
        try:
            i = self._recipe_parse_ingredients(lines, i, r)
        except Exception as e:
            print("ERROR while parsing")
            print()
            print(recipeFile)
            raise e

        steps = self._recipe_parse_steps(lines, i)

        if "kcal" in d:
            r.kcal = float(d["kcal"])
        if "carbs" in d:
            r.carbs = float(d["carbs"])
        if "proteins" in d:
            r.proteins = float(d["proteins"])
        if "portions" in d:
            r.portions = d["portions"]
        if "initialDate" in d:
            r.initialDate = d["initialDate"]

        r.preparation = steps

        p = "static/images/%s" % dirname_rel
        mkdir_p(p)

        thumbSq = "static/images/%s/%s_sq_320.jpg" % (dirname_rel, slug)
        if not os.path.exists(thumbSq):
            if os.path.exists(imgSq % "png"):
                inFile = imgSq % "png"
            elif os.path.exists(imgSq % "jpg"):
                inFile = imgSq % "jpg"
            mkThumb(inFile, thumbSq, (320,320))

        if "pdf" in d:
          pdfSource = dirname + "/" + d["pdf"]
          pdfDest = "static/images/%s/%s" % (dirname_rel, os.path.basename(d["pdf"]))
          if not os.path.exists(pdfDest):
            shutil.copy(pdfSource, pdfDest)
          r.pdf = "images/%s/%s" % (dirname_rel, os.path.basename(d["pdf"]))

        if "tags" in d:
            for tag in d["tags"]:
                slug = germanslugify(tag)
                if slug not in self.tags:
                    self.tags[slug] = RecipeTag(slug=slug, name=tag)
                self.recipeToTags[r.slug].add(slug)
