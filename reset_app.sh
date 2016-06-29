#!/bin/bash

echo "resetting the application"
rm -rf tmp
rm -rf webservice/migrations
rm -rf db.sqlite3
python manage.py makemigrations webservice


echo "resetting the application"
echo "no" | python manage.py syncdb
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'pass')" | python manage.py shell
