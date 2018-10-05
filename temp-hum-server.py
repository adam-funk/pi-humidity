#!/usr/bin/env python3

from bottle import route, run, post, request, static_file, response, template

import datetime, json

data_file = '/home/adam/home-data.tsv'


@post('/data')
def take_data():
    j = request.json
    print(j)

    with open(data_file, 'a') as f:
        line = '%s\t%s\t%s\t%s\t%s\n' % (j['epoch'], j['date_time'],
                                         j['id'], j['temperature'], j['humidity'])
        f.write(line)
    return 'OK'


run(host='0.0.0.0', port=8089, debug=True)
