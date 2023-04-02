#!/usr/bin/env python3
import argparse
import datetime
import json
import time

import pigpio

import bme680
import sensorutils


def get_data(sensor0):
    while True:
        if sensor0.get_sensor_data():
            temperature0 = sensor0.data.temperature
            humidity0 = sensor0.data.humidity
            pressure0 = sensor0.data.pressure
            now0 = datetime.datetime.now()
            epoch0 = int(time.time())
            break
        time.sleep(1)
    if options.verbose:
        iso_time = datetime.datetime.isoformat(now0).split('.')[0]
        print('Measurement:', iso_time, temperature0, humidity0)
    return epoch0, now0, temperature0, humidity0, pressure0


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
data_location = sensorutils.DataLocation(config['data_directory'], options.verbose)
location = config['location']

# https://learn.pimoroni.com/article/getting-started-with-bme680-breakout

sensor = bme680.BME680()

sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)

sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)

epoch, now, temperature, humidity, pressure = get_data(sensor)
data_location.record(epoch, now, location, temperature, humidity, pressure)
