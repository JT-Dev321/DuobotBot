#!/bin/bash
cd /home/deepforce/DuobotBot/web
source /home/deepforce/.venvs/discord/bin/activate
exec gunicorn -w 4 -b 0.0.0.0:8000 app:app