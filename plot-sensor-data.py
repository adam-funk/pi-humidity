#!/usr/bin/python3

import argparse
import datetime
import imghdr
import os
import smtplib
import time
from collections import defaultdict
from email.message import EmailMessage

import matplotlib.pyplot as plt
import numpy
from matplotlib import dates

# https://matplotlib.org/gallery/text_labels_and_annotations/date.html
# https://matplotlib.org/api/_as_gen/matplotlib.pyplot.subplots.html#matplotlib.pyplot.subplots
# https://matplotlib.org/api/dates_api.html#matplotlib.dates.MonthLocator
# https://matplotlib.org/api/_as_gen/matplotlib.pyplot.plot.html#matplotlib.pyplot.plot
# https://matplotlib.org/tutorials/introductory/pyplot.html

default_data_file = '/home/adam/home-data.tsv'
default_output_dir = '/tmp/sensor-plots-%i' % int(time.time())


def round_down_date(timestamp):
    d = datetime.date.fromtimestamp(timestamp)
    dt = datetime.datetime.combine(d, datetime.time(0, 0, 0))
    return int(dt.timestamp())


def read_raw_data(data_file):
    # TODO filter by identifer (col 2)
    global mail_log
    # time -> (temp, hum)
    data_to_use = dict()
    # collect all the valid data from the file
    with open(data_file, 'r') as f:
        for line in f.readlines():
            line_data = line.rstrip().split('\t')
            epoch = int(line_data[0])
            temp = float(line_data[3])
            hum = float(line_data[4])
            if (-10 < temp < 150) and (-1 < hum < 101):
                data_to_use[epoch] = (temp, hum)
            else:
                mail_log.append("Rejected %i %s %f %f" % (epoch, line_data[1], temp, hum))
    return data_to_use


def average_data(data_to_use):
    raw_times = list(data_to_use.keys())
    raw_times.sort()
    timestamps = []
    temperatures = []
    humidities = []
    prev_epoch = raw_times[0]
    prev_temp = data_to_use[prev_epoch][0]
    prev_hum = data_to_use[prev_epoch][1]
    # Use average of each pair of adjacent measurements
    for epoch in raw_times[1:]:
        timestamps.append(numpy.datetime64((prev_epoch + epoch) // 2, 's'))
        temp = data_to_use[epoch][0]
        hum = data_to_use[epoch][1]
        temperatures.append((prev_temp + temp) / 2)
        humidities.append((prev_hum + hum) / 2)
        prev_epoch = epoch
        prev_temp = temp
        prev_hum = hum
    return timestamps, temperatures, humidities


def daily_data(data_to_use):
    daily_temperatures = defaultdict(list)
    daily_humidities = defaultdict(list)
    for timestamp, (temp, hum) in data_to_use.items():
        rounded_timestamp = round_down_date(timestamp)
        daily_temperatures[rounded_timestamp].append(temp)
        daily_humidities[rounded_timestamp].append(hum)
    timestamps = []
    temp_max = []
    temp_min = []
    temp_mean = []
    hum_max = []
    hum_min = []
    hum_mean = []
    for timestamp in daily_humidities.keys():
        timestamps.append(numpy.datetime64(timestamp, 's'))
        temp_min.append(min(daily_temperatures[timestamp]))
        temp_mean.append(numpy.mean(daily_temperatures[timestamp]))
        temp_max.append(max(daily_temperatures[timestamp]))
        hum_min.append(min(daily_humidities[timestamp]))
        hum_mean.append(numpy.mean(daily_humidities[timestamp]))
        hum_max.append(max(daily_humidities[timestamp]))
    return timestamps, temp_min, temp_mean, temp_max, hum_min, hum_mean, hum_max


# MAIN
def read_and_plot(options):
    os.mkdir(default_output_dir)
    f0 = os.path.join(default_output_dir, 'time.png')
    f1 = os.path.join(default_output_dir, 'date.png')

    general_data = read_raw_data(options.data_file)
    all_timestamps, all_temperatures, all_humidities = average_data(general_data)

    # https://stackoverflow.com/questions/15713279/calling-pylab-savefig-without-display-in-ipython
    if options.visual:
        plt.ion()
    else:
        plt.ioff()

    days = dates.DayLocator(interval=1)
    days_format = dates.DateFormatter('%Y-%m-%d')

    fig0, ax0 = plt.subplots()
    ax0.xaxis.set_major_locator(days)
    ax0.xaxis.set_major_formatter(days_format)
    ax0.format_xdata = days_format
    ax0.plot(all_timestamps, all_temperatures, 'b,-',
             all_timestamps, all_humidities, 'g,-')
    # autofmt needs to happen after data
    fig0.autofmt_xdate(rotation=60)
    plt.savefig(f0, dpi=200)
    if not options.visual:
        plt.close(fig0)

    datestamps, tmin, tmean, tmax, hmin, hmean, hmax = daily_data(general_data)

    fig1, ax1 = plt.subplots()
    ax1.xaxis.set_major_locator(days)
    ax1.xaxis.set_major_formatter(days_format)
    ax1.format_xdata = days_format
    ax1.plot(datestamps, tmin, 'b-',
             datestamps, tmean, 'b-',
             datestamps, tmax, 'b-',
             datestamps, hmin, 'g-',
             datestamps, hmean, 'g-',
             datestamps, hmax, 'g-'
             )
    fig1.autofmt_xdate(rotation=60)
    plt.savefig(f1, dpi=200)
    if not options.visual:
        plt.close(fig1)

    return f0, f1


oparser = argparse.ArgumentParser(description="Plotter for temperature and humidity log",
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter)

oparser.add_argument("-d", dest="data_file",
                     default=default_data_file,
                     metavar="TSV",
                     help="TSV input file")

oparser.add_argument("-v", dest="visual",
                     default=False,
                     action='store_true',
                     help="show plots")

oparser.add_argument("-m", dest="mail",
                     default=None,
                     type=str,
                     metavar='USER@EXAMPLE.COM',
                     help="send mail to this address")

options = oparser.parse_args()

mail_log = []

f0, f1 = read_and_plot(options)

if options.mail:
    mail = EmailMessage()
    mail.set_charset('utf-8')
    mail['To'] = options.mail
    mail['From'] = 'potsmaster@ducksburg.com'
    mail['Subject'] = 'temperature & humidity'
    mail.preamble = '\n'.join(mail_log)
    # https://docs.python.org/3/library/email.examples.html
    for file in [f0, f1]:
        with open(file, 'rb') as fp:
            img_data = fp.read()
        mail.add_attachment(img_data, maintype='image',
                            subtype=imghdr.what(None, img_data))
    with smtplib.SMTP('localhost') as s:
        s.send_message(mail)