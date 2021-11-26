#!/usr/bin/python3
import argparse
import datetime
import json
import time

import pigpio
import requests

import DHT22
import sensorutils


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
    temperature = round(sensor.temperature(), 1)
    humidity = round(sensor.humidity(), 1)
    if options.verbose:
        iso_time = datetime.datetime.isoformat(now).split('.')[0]
        print('Measurement:', iso_time, temperature, humidity)
    if (temperature > -10) and (humidity > 0):
        signal_blinks(led_pin, 3, 0.5, pi)
    else:
        signal_blinks(led_pin, 9, 0.2, pi)
    return epoch, temperature, humidity, now


oparser = argparse.ArgumentParser(description="Client for temperature logging",
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter)

oparser.add_argument("-v", dest="verbose",
                     default=False,
                     action='store_true',
                     help="verbose")

oparser.add_argument("-c", dest="config_file",
                     required=True,
                     metavar="FILE",
                     help="JSON config file")

options = oparser.parse_args()

with open(options.config_file) as f:
    config = json.load(f)
pi = pigpio.pi()
data_location = sensorutils.DataLocation(config['data_directory'], options.verbose)

# Check each sensor and write results to the file.
for entry in config['sensors']:
    sensor = DHT22.sensor(pi, entry['sensor_pin'])
    led_pin = entry['led_pin']
    location = entry['location']
    epoch, temperature, humidity, now = get_data(sensor, led_pin, pi)
    data_location.record(epoch, now, location, temperature, humidity)
