import os
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = "cookingsite.settings"

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
