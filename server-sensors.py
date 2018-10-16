#!/usr/bin/env python3

import time

import maya
from bottle import post, request
from bottledaemon import daemon_run

data_file = '/home/adam/sensors-data.tsv'

pid_filename = '/tmp/sensors-server-%d.pid' % time.time()

# log file name includes timestamp to prevent clobbering
log_filename = '/home/adam/sensors-server-%d.log' % round(time.time())


@post('/data')
def take_data():
    j = request.json
    # print the ISO time (just to the second)
    print(maya.now().iso8601().split('.')[0])
    print(j) # to the log?

    with open(data_file, 'a') as f:
        line = '%s\t%s\t%s\t%s\t%s\n' % (j['epoch'], j['date_time'],
                                         j['id'], j['temperature'], j['humidity'])
        f.write(line)
    return 'OK'

# 0.0.0.0 makes it available on the LAN
daemon_run(host='0.0.0.0', port=8089, pidfile=pid_filename, logfile=log_filename)
