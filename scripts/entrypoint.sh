#!/bin/sh

set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

uwsgi --socket :8000 --master --enable-threads --module Doomstein98.wsgi &
daphne -b 0.0.0.0 -p 8001 Doomstein98.asgi:application &
python manage.py runworker game_engine