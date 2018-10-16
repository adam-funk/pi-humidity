#!/usr/bin/env python3

import json
import os
import time

import maya
from bottle import post, request
from bottledaemon import daemon_run


@post('/data')
def take_data():
    j = request.json
    # Log the ISO time (just to the second), then the data.
    print(maya.now().iso8601().split('.')[0])
    print(j)

    with open(data_filename, 'a') as f:
        line = '%s\t%s\t%s\t%s\t%s\n' % (j['epoch'], j['date_time'],
                                         j['identifier'], j['temperature'], j['humidity'])
        f.write(line)
    return 'OK'


HERE=os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(HERE, 'server.json')) as f:
    config = json.load(f)

directory = config['directory']
data_filename = os.path.join(directory, config['data_file'])

pid_filename = '/tmp/sensors-server.pid'

# log file name includes timestamp to prevent clobbering
log_filename = os.path.join(directory, 'sensors-server-%d.log' % round(time.time()))

# 0.0.0.0 makes it available on the LAN
daemon_run(host='0.0.0.0', port=config['port'],
           pidfile=pid_filename, logfile=log_filename)
