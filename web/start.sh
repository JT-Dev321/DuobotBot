#!/bin/bash
cd /home/deepforce/DuobotBot/web
source /home/deepforce/.venvs/discord/bin/activate
exec gunicorn -w 4 -b 127.0.0.1:8000 app:app