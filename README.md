# Gourmet - Website for managing your recipe collection

_Note_: This project is quite old and was a way for me to learn django,
javascript and web-development in general. I've recently clened it up
very slightly, squashed the history and pushed it to github.

This is a django-based web application for managing your recipe collection.

![screenshot](https://raw.githubusercontent.com/thorbenk/gourmet/master/github/screenshot_recipe_list.png)

Most importantly, `gourmet` stores your recipes as **simple text files**.
A MySQL database is only used to _cache_ the data, but never as the primary
means of storing your data. Edits to your recipe data are written directly
back to the text files (as well as cached to the database).  

This way, you can keep all your recipes in a _git repository_.
The web application will edit and commit the source text files
(such as when changing recipe tags).

## Features

- _Text-based file format_:  
  A recipe is defined in a simple, human-readable text file  
  (name, source, tags, ingredients, method)
  - human-readable ingredients can be written like  
    "250 g Spaghetti"  
    and quantity, unit and ingredient are parsed from it
  - you can define a hierarchy for ingredients
    (e.g. "carrots -> vegetables")
- recipes can be linked to their originating source
  (such as a book, magazine or a website).
  The user can then list all recipes from a certain source.
- tags (also editable via the web interface!)
- schedule a number of recipes for the week; `gourmet` will generate
  a shopping list for you
- find recipes by ingredient

## Installation

On Ubuntu 17.04, first install some dependencies:
```
sudo apt install mysql-server libmysqlclient-dev
```

We'll first create a `virtualenv` python environment, into which
we install all necessary dependencies (including Django)
```bash
virtualenv -p /usr/bin/python3.5 .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create the MySQL database for the application:
```bash
mysql -u root -p < ./scripts/create_db_user.sql
```

Next, configure `cookingsite/settings.py`.
Set the following important variables:

- `RECIPES_COLLECTION_PREFIX`: path to recipe collection
  in textual format (TODO: description of format)
- `DATABASE`: how to connect to your database 

Now, initialize the database:
```bash
python manage.py makemigrations
python manage.py migrate
```

Then, we can populate the database by reading in all recipes in 
`RECIPES_COLLECTION_PREFIX`:
```bash
./convert_files2database.py
```

Then, run
```bash
python manage.py runserver
```
and then open http://127.0.0.1:8000/
