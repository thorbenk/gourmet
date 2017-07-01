python manage.py sqlclear recipes > /tmp/clear.sql
mysql -ucookingsite -pcookingsite_password cookingsite < /tmp/clear.sql
