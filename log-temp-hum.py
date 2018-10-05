#!/usr/bin/python3

import pigpio, DHT22, time
import requests, json, datetime, time, argparse

led_pin = 24
sensor_pin = 23
identifier = 'cellar'
log_url = 'http://192.168.123.7:8089/data'
local_file = '/home/pi/cellar.tsv'


def signal(blinks, pause):
    for i in range(0, blinks):
        pi.write(led_pin, 1)
        time.sleep(pause)
        pi.write(led_pin, 0)
        time.sleep(pause)
    return


def process(sensor, options):
    sensor.trigger()
    time.sleep(0.5)
    now = datetime.datetime.now()
    epoch = int(time.time())
    iso_time = datetime.datetime.isoformat(now).split('.')[0]
    t = round(sensor.temperature(), 1)
    h = round(sensor.humidity())
    if not options.quiet:
        print(t, h, iso_time)
    if t > 0 or h > 0:
        signal(3, 0.5)
    else:
        signal(5, 0.3)
    return (t, h, epoch, iso_time)


def log(temperature, humidity, epoch, iso_time, options):
    with open(local_file, 'a') as f:
        f.write('%d\t%s\t%f\t%f\n' % (epoch, iso_time, temperature, humidity))
    response = requests.post(log_url,
                             json = {'id' : identifier,
                                     'temperature' : temperature,
                                     'humidity' : humidity,
                                     'date_time' : iso_time,
                                     'epoch' : epoch}
    )
    if not options.quiet:
        print(response.status_code)
        print(response.text)

    if response.status_code != 200:
        signal(20, 0.2)
    return


oparser = argparse.ArgumentParser(description="...",
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter)

oparser.add_argument("-q", dest="quiet", default=False,
                     action='store_true',
                     help="quiet")

options = oparser.parse_args()


pi = pigpio.pi()
sensor = DHT22.sensor(pi, sensor_pin)

t, h, epoch, iso_time = process(sensor, options)
log(t, h, epoch, iso_time, options)
