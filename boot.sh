#!/bin/sh

source venv/bin/activate
flask db upgrade
flask translate compile
exec gunicorn -b :5000 --aceess-logfile - --error-logfile - microblog:app