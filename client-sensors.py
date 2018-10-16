#!/usr/bin/python3
import argparse
import datetime
import json
import time

import pigpio
import requests
import tinydb

import DHT22


def signal_blinks(led_pin, nbr_blinks, pause, pi):
    for i in range(0, nbr_blinks):
        pi.write(led_pin, 1)
        time.sleep(pause)
        pi.write(led_pin, 0)
        time.sleep(pause)
    return


def get_data(sensor, led_pin, pi):
    sensor.trigger()
    time.sleep(0.5)
    now = datetime.datetime.now()
    epoch = int(time.time())
    iso_time = datetime.datetime.isoformat(now).split('.')[0]
    t = round(sensor.temperature(), 1)
    h = round(sensor.humidity())  # this returns int
    if not options.quiet:
        print('Measurement:', iso_time, t, h)
    if (t > -10) and (h > 0):
        signal_blinks(led_pin, 3, 0.5, pi)
    else:
        signal_blinks(led_pin, 10, 0.2, pi)
    return {'epoch': epoch, 'temperature': t, 'humidity': h,
            'date_time': iso_time, 'led_pin': led_pin}


def record_locally(data_chunk, local_file, database):
    with open(local_file, 'a') as f:
        f.write('{epoch}\t{date_time}\t{identifier}\ttemperature\thumidity\n'.format_map(data_chunk))
    database.insert(data_chunk)
    return


def post_data(data_chunk, log_url, pi):
    success = False
    led_pin = data_chunk['led_pin']
    if not options.quiet:
        print('Posting:', data_chunk['date_time'])
    try:
        response = requests.post(log_url, json=data_chunk)
        if not options.quiet:
            print(response.status_code)
            print(response.text)
        if response.status_code == 200:
            success = True
    except Exception as e:
        if not options.quiet:
            print(str(e))
    if success:
        signal_blinks(led_pin, 6, 0.5, pi)
    else:
        signal_blinks(led_pin, 20, 0.2, pi)
    return success


def main(options):
    with open(options.config_file) as f:
        config = json.load(f)
    pi = pigpio.pi()
    database = tinydb.TinyDB(config['database'])
    tsv = config['local_file']

    # Check each sensor and write results to the database.
    for entry in config['sensors']:
        sensor = DHT22.sensor(pi, entry['sensor_pin'])
        led_pin = entry['led_pin']
        data_chunk = get_data(sensor, led_pin, pi)
        data_chunk['identifier'] = entry['identifier']
        record_locally(data_chunk, tsv, database)

    # Try to post each item in the database but quit trying
    # after one fails.  Delete each one when successful.
    # The database contains only unPOSTed data.
    for data_chunk in iter(database):
        if post_data(data_chunk, config['url'], pi):
            database.remove(doc_ids=[data_chunk.doc_id])
        else:
            break

    if not options.quiet:
        print('Outstanding data', len(database))
    return


oparser = argparse.ArgumentParser(description="Client for temperature logging",
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter)

oparser.add_argument("-q", dest="quiet", default=False,
                     action='store_true',
                     help="quiet")

oparser.add_argument("-c", dest="config_file",
                     metavar="JSON",
                     help="config file")

options = oparser.parse_args()

main(options)
