#!/bin/bash
cd /home/www/analytics-for-spotify/
source .venv/bin/activate
#export MIGRATIONS='true'
#python3 setup.py
#export MIGRATIONS='false'
exec "$@"
