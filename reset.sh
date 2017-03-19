#!/bin/bash
echo "[RESET] Resetting the application database..."
rm -f db.sqlite3
python manage.py migrate
