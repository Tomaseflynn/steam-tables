#!/bin/sh
source .venv/bin/activate
gunicorn --workers 3 --bind 0.0.0.0:$PORT main:app
