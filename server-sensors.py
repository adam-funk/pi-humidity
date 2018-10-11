#!/usr/bin/env python3

from bottle import run, post, request
from bottledaemon import daemon_run
import time

data_file = '/home/adam/sensors-data.tsv'

pid_filename = '/tmp/sensors-server-%d.pid' % time.time()

log_filename = '/home/adam/sensors-server.log'

@post('/data')
def take_data():
    j = request.json
    print(j) # to the log?

    with open(data_file, 'a') as f:
        line = '%s\t%s\t%s\t%s\t%s\n' % (j['epoch'], j['date_time'],
                                         j['id'], j['temperature'], j['humidity'])
        f.write(line)
    return 'OK'


# 0.0.0.0 makes it available on the LAN
# run(host='0.0.0.0', port=8089, debug=True)
daemon_run(host='0.0.0.0', port=8089, pidfile=pid_filename, logfile=log_filename)
