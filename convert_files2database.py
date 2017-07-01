#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.core.wsgi import get_wsgi_application

import signal, sys, os
def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

#Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'cookingsite.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cookingsite.settings")
application = get_wsgi_application()

#this project
from cookingsite.settings import RECIPES_COLLECTION_PREFIX
from flatRecipeParser import FlatRecipeParser

if __name__ == '__main__':
    FlatRecipeParser(RECIPES_COLLECTION_PREFIX, dryRun=False)

    from django.contrib.auth.models import User
    User.objects.all().delete()
    User.objects.create_user('thorben', 'dev@thorben.net', password='thorben')
