#!/usr/bin/python3
import json

import DHT22
import argparse
import datetime
import pigpio
import requests
import time

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


def process(sensor, led_pin, options, identifier):
    sensor.trigger()
    time.sleep(0.5)
    now = datetime.datetime.now()
    epoch = int(time.time())
    iso_time = datetime.datetime.isoformat(now).split('.')[0]
    t = round(sensor.temperature(), 1)
    h = round(sensor.humidity())
    if not options.quiet:
        print(t, h, iso_time)
    if (t > -10) and (h > 0):
        signal_blinks(led_pin, 3, 0.5)
    else:
        signal_blinks(led_pin, 5, 0.3)
    return t, h, epoch, iso_time


def log(temperature, humidity, epoch, iso_time, options, led_pin, log_url,
        identifier, local_file):
    with open(local_file, 'a') as f:
        f.write('%d\t%s\t%f\t%f\n' % (epoch, iso_time, temperature, humidity))
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

    if response.status_code != 200:
        signal_blinks(led_pin, 20, 0.2)
    return


oparser = argparse.ArgumentParser(description="Client for temperature logging",
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter)

oparser.add_argument("-q", dest="quiet", default=False,
                     action='store_true',
                     help="quiet")

oparser.add_argument("-d", dest="database",
                     metavar="SQL",
                     help="database file")

oparser.add_argument("-c", dest="config_file",
                     metavar="JSON",
                     help="config file")

options = oparser.parse_args()

pi = pigpio.pi()

with open(options.config_file) as f:
    config = json.load(f)

for entry in config['sensors']:
    sensor = DHT22.sensor(pi, entry['sensor_pin'])
    led_pin = entry['led_pin']
    identifier = entry['identifier']
    t, h, epoch, iso_time = process(sensor, led_pin, options)
    log(t, h, epoch, iso_time, options, led_pin, config['url'], identifier, config['local_file'])
