import codecs
import os

from recipes.models import Recipe
from cookingsite.settings import RECIPES_COLLECTION_PREFIX

def _write_title(r, f):
    f.write(u"# " + r.name + u"\n\n")
    if r.subtitle:
        f.write(u"## " + r.subtitle + u"\n\n")

def _write_meta(r, f):
    d = {}
    d["source"] = r.source.slug
    page = r.page
    if page:
        d["source"] += "/%d" % page
    tags = sorted([x.slug for x in r.tags.all()])
    if tags:
        d["tags"]     = ", ".join(tags)
    if r.kcal:
        d["kcal"]     = str(int(r.kcal))
    if r.carbs:
        d["carbs"]    = str(int(r.carbs))
    if r.fat:
        d["fat"]      = str(int(r.fat))
    if r.proteins:
        d["proteins"] = str(int(r.proteins))
    if r.portions:
        d["serves"]   = r.portions
    if r.imageSquare:
        d["image"]    = os.path.basename(r.imageSquare.replace("_sq", ""))
    if r.initialDate:
        x = r.initialDate
        if True:
            year, weekNumber, weekday = r.initialDate.isocalendar()
            d["published"] = str("KW %02d/%04d" % (weekNumber, year))
        else:
            raise RuntimeError("did not understand datetime %r" % r.initialDate)
   
    M = max([len(k) for k in d.keys()])
    for k in sorted(d.keys()):
        v = d[k]
        if v is not None:
            f.write(k + ":" + (M-len(k))*" " + " " + v + "\n")
    f.write("\n")
    
def _write_steps(r, f):
    if r.preparation:
        f.write(r.preparation)
    
def _write_ingredients(r, f):
    ings = []
    for ing in r.get_ingredients():
        ings.append( (ing.textAmount, ing.textIngredient) )
    
    M = max( [len(x[0]) for x in ings] )
    for k, v in ings:
        f.write(k + (M-len(k))*" " + " | " + v + "\n")
    f.write("\n")

def db2file(recipeSlug):
    print(recipeSlug)
    r = Recipe.objects.get(slug=recipeSlug)
    f = codecs.open(os.path.join(RECIPES_COLLECTION_PREFIX, r.filename), 'w', 'utf-8')
    _write_title(r, f)
    _write_meta(r, f)
    _write_ingredients(r, f)
    _write_steps(r, f)
    f.close()