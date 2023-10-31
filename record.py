#!/usr/bin/env python3
import argparse
import datetime
import json
import time

import bme680

import sensorutils

CUT_THRESHOLD = 0.01


def elapsed(start):
    return time.time() - start


def get_data(sensor0, timeout0):
    start = time.time()
    temperature0 = None
    humidity0 = None
    pressure0 = None
    resistance0 = None
    previous_resistance = None
    while elapsed(start) <= timeout0:
        if sensor0.get_sensor_data():
            temperature0 = round(sensor0.data.temperature, 1)
            humidity0 = round(sensor0.data.humidity, 1)
            pressure0 = round(sensor0.data.pressure, 1)
            break
        time.sleep(1)

    now0 = datetime.datetime.now()
    epoch0 = int(time.time())
    cut_high = False
    cut_low = False

    if options.verbose:
        print(f'Measurements {temperature0}°C {humidity0}% {pressure0} hPa at {elapsed(start)}')

    while elapsed(start) <= timeout0:
        # Note: get_sensor_data() is required here or heat_stable will never be True!
        if sensor0.get_sensor_data() and sensor0.data.heat_stable:
            resistance0 = sensor0.data.gas_resistance
            if previous_resistance:
                change = resistance0 / previous_resistance - 1.0
                if 0.0 <= change < CUT_THRESHOLD:
                    cut_high = True
                if - CUT_THRESHOLD < change <= 0.0:
                    cut_low = True
            if options.verbose:
                print(f'{resistance0} <- {previous_resistance} {cut_low} {cut_high}')
            if cut_high and cut_low:
                break
            previous_resistance = resistance0
        time.sleep(1)

    # change Ω to kΩ
    resistance0 = round(resistance0 / 1000, 1)
    elapsed_time0 = round(elapsed(start), 1)
    if options.verbose:
        print(f'Measurements {temperature0}°C {humidity0}% {pressure0} hPa {resistance0} kΩ at {elapsed_time0}')
    return epoch0, now0, temperature0, humidity0, pressure0, resistance0, elapsed_time0


oparser = argparse.ArgumentParser(description="Record sensor data",
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
timeout = config.get('timeout', 180)

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

epoch, now, temperature, humidity, pressure, resistance, elapsed_time = get_data(sensor, timeout)
data_location.record(epoch, now, location, temperature, humidity, pressure, resistance, elapsed_time)
