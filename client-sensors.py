#!/usr/bin/python3
import argparse
import datetime
import json
import os
# TODO use tinyDB
import time

import pigpio
import requests

import DHT22


# led_pin = 24
# sensor_pin = 23
# identifier = 'cellar'
# log_url = 'http://192.168.123.7:8089/data'
# local_file = '/home/pi/cellar.tsv'


def signal_blinks(led_pin, nbr_blinks, pause):
    for i in range(0, nbr_blinks):
        pi.write(led_pin, 1)
        time.sleep(pause)
        pi.write(led_pin, 0)
        time.sleep(pause)
    return


def record_data(options, connection, epoch, iso, temp, hum, identifier):
    cursor = connection.cursor()
    cursor.execute('INSERT INTO data ( epoch, isotime, identifier, temp, hum, uploaded) '
                   'VALUES (?, ?, ?, ?, ?, 0)', epoch, iso, identifier, temp, hum)
    connection.commit()
    return


def process(sensor, led_pin, options, identifier):
    sensor.trigger()
    time.sleep(0.5)
    now = datetime.datetime.now()
    epoch = int(time.time())
    iso_time = datetime.datetime.isoformat(now).split('.')[0]
    t = round(sensor.temperature(), 1)
    h = round(sensor.humidity())  # this returns int
    if not options.quiet:
        print(t, h, iso_time)
    if (t > -10) and (h > 0):
        signal_blinks(led_pin, 3, 0.5)
    else:
        signal_blinks(led_pin, 10, 0.2)
    return t, h, epoch, iso_time


def log(temperature, humidity, epoch, iso_time, options, led_pin, log_url,
        identifier, local_file):
    with open(local_file, 'a') as f:
        f.write('%d\t%s\t%s\t%.1f\t%.f\n' % (epoch, iso_time, identifier, temperature, humidity))
    response = requests.post(log_url,
                             json={'id': identifier,
                                   'temperature': temperature,
                                   'humidity': humidity,
                                   'date_time': iso_time,
                                   'epoch': epoch}
                             )
    if not options.quiet:
        print(response.status_code)
        print(response.text)

    if response.status_code == 200:
        signal_blinks(led_pin, 6, 0.5)
    else:
        signal_blinks(led_pin, 20, 0.2)
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

with open(options.config_file) as f:
    config = json.load(f)

pi = pigpio.pi()

for entry in config['sensors']:
    sensor = DHT22.sensor(pi, entry['sensor_pin'])
    led_pin = entry['led_pin']
    t, h, epoch, iso_time = process(sensor, led_pin, options, entry['identifier'])
    log(t, h, epoch, iso_time, options, led_pin, config['url'], entry['identifier'], config['local_file'])
