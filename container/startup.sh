#!/bin/bash
mkdir /run/lock
cd /home/www/analytics-for-spotify/
#export MIGRATIONS='true'
#python3 setup.py
#export MIGRATIONS='false'
exec "$@"
