@echo off
set DOCKER_HOST=npipe:////./pipe/docker_engine
echo DOCKER_HOST установлен в %DOCKER_HOST%
python main.py
pause