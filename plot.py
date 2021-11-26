#!/usr/bin/python3

import argparse
import datetime
import imghdr
import os
import platform
import smtplib
import json
import time
from collections import defaultdict
from email.message import EmailMessage

import numpy as np
import pandas as pd

# https://matplotlib.org/gallery/text_labels_and_annotations/date.html
# https://matplotlib.org/api/_as_gen/matplotlib.pyplot.subplots.html#matplotlib.pyplot.subplots
# https://matplotlib.org/api/dates_api.html#matplotlib.dates.MonthLocator
# https://matplotlib.org/api/_as_gen/matplotlib.pyplot.plot.html#matplotlib.pyplot.plot
# https://matplotlib.org/tutorials/introductory/pyplot.html

import sensorutils

FIGSIZE = (7, 2)


def generate_mail(location, dataframe, config):
    mail = EmailMessage()
    mail.set_charset('utf-8')
    mail['To'] = ' '.join(config['mail_to'])
    mail['From'] = config['mail_from']
    mail['Subject'] = 'temperature & humidity'





# MAIN
def read_and_plot(options):
    output_dir = '/tmp/sensor-plots-%i' % int(time.time())
    os.mkdir(output_dir)
    f0 = os.path.join(output_dir, 'tem_7_days_smoothed.png')
    f1 = os.path.join(output_dir, 'hum_7_days_smoothed.png')
    f2 = os.path.join(output_dir, 'tem_12_days_ranged.png')
    f3 = os.path.join(output_dir, 'hum_12_days_ranged.png')

    general_data = read_raw_data(options.data_file)

    # https://stackoverflow.com/questions/15713279/calling-pylab-savefig-without-display-in-ipython
    if options.visual:
        plt.ion()
    else:
        plt.ioff()

    days_locator = dates.DayLocator(interval=1)
    # days_format = dates.DateFormatter('%Y-%m-%d')
    days_format = dates.DateFormatter('%d')

    # smoothed plot
    all_timestamps, all_temperatures, all_humidities = average_data(general_data, max_days=7)

    fig0, ax0 = plt.subplots(figsize=FIGSIZE)
    ax0.xaxis.set_major_locator(days_locator)
    ax0.xaxis.set_major_formatter(days_format)
    # ax0.xaxis.set_minor_locator(days)
    ax0.format_xdata = days_format
    ax0.grid(True, which='both')
    ax0.plot(all_timestamps, all_temperatures, 'b,-')
    # autofmt needs to happen after data
    fig0.autofmt_xdate(rotation=60)
    plt.savefig(f0, dpi=200)
    if not options.visual:
        plt.close(fig0)

    fig1, ax1 = plt.subplots(figsize=FIGSIZE)
    ax1.xaxis.set_major_locator(days_locator)
    ax1.xaxis.set_major_formatter(days_format)
    # ax1.xaxis.set_minor_locator(days)
    ax1.format_xdata = days_format
    ax1.grid(True, which='both')
    ax1.plot(all_timestamps, all_humidities, 'g,-')
    # autofmt needs to happen after data
    fig1.autofmt_xdate(rotation=60)
    plt.savefig(f1, dpi=200)
    if not options.visual:
        plt.close(fig1)

    # ranged plot
    datestamps, tmin, tmean, tmax, hmin, hmean, hmax = daily_data(general_data, max_days=20)

    if options.debug_days:
        mail_log.append('\nDay data:')
        for stuff in zip(datestamps, tmin, tmean, tmax, hmin, hmean, hmax):
            mail_log.append(' '.join([str(x) for x in stuff]))

    fig2, ax2 = plt.subplots(figsize=FIGSIZE)
    ax2.xaxis.set_major_locator(days_locator)
    ax2.xaxis.set_major_formatter(days_format)
    # ax2.xaxis.set_minor_locator(days)
    ax2.format_xdata = days_format
    ax2.grid(True, which='both')
    ax2.plot(datestamps, tmin, 'b-',
             datestamps, tmean, 'b-',
             datestamps, tmax, 'b-',
             )
    fig2.autofmt_xdate(rotation=60)
    plt.savefig(f2, dpi=200)
    if not options.visual:
        plt.close(fig2)

    fig3, ax2 = plt.subplots(figsize=FIGSIZE)
    ax2.xaxis.set_major_locator(days_locator)
    ax2.xaxis.set_major_formatter(days_format)
    # ax2.xaxis.set_minor_locator(days)
    ax2.format_xdata = days_format
    ax2.grid(True, which='both')
    ax2.plot(datestamps, hmin, 'g-',
             datestamps, hmean, 'g-',
             datestamps, hmax, 'g-'
             )
    fig3.autofmt_xdate(rotation=60)
    plt.savefig(f3, dpi=200)
    if not options.visual:
        plt.close(fig3)

    return f0, f1, f2, f3


oparser = argparse.ArgumentParser(description="Plotter for temperature and humidity log",
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

max_days_ago = config['max_days_ago']

dataframe_map = data_location.get_dataframes(max_days_ago)

for location, dataframe in dataframe_map.items():
    generate_mail(location, dataframe, config)

if not options.visual:
    import matplotlib

    matplotlib.use('Agg')

import matplotlib.pyplot as plt
from matplotlib import dates

# mail_log = ['Now = %s' % datetime.datetime.now().isoformat(timespec='seconds')]
# honeydew uses python 3.5: no timespec

basic_message = 'Now = %s\nServer = %s' % (datetime.datetime.now().isoformat(),
                                           platform.node())
mail_log = []

plot_files = read_and_plot(options)

mail = EmailMessage()
mail.set_charset('utf-8')
mail['To'] = ', '.join(options.mail)
mail['From'] = 'potsmaster@ducksburg.com'
mail['Subject'] = 'temperature & humidity'

mail.add_attachment(basic_message.encode('utf-8'),
                    disposition='inline',
                    maintype='text', subtype='plain')

# https://docs.python.org/3/library/email.examples.html
for file in plot_files:
    with open(file, 'rb') as fp:
        img_data = fp.read()
    mail.add_attachment(img_data, maintype='image',
                        disposition='inline',
                        subtype=imghdr.what(None, img_data))

mail.add_attachment('\n'.join(mail_log).encode('utf-8'),
                    disposition='inline',
                    maintype='text', subtype='plain')

with smtplib.SMTP('localhost') as s:
    s.send_message(mail)

