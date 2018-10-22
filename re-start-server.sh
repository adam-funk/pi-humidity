#!/bin/bash

umask 0027
cd ${HOME}/sensors/  || exit 99
./server-sensors.py  stop
rm /tmp/sensors-server.pid
./server-sensors.py  start
