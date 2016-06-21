#! /bin/bash

APP=rpapp

echo "[RESET] Resetting the application..."
rm -rf tmp
rm -rf db.sqlite3
rm -rf $APP/migrations
python manage.py makemigrations $APP
python manage.py migrate
echo "[RESET] Creating superuser 'admin' with password 'pass'..."
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'pass')" | python manage.py shell > /dev/null 2> /dev/null
