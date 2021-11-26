#!/usr/bin/python3

import argparse
import datetime
import imghdr
import os
import platform
import json
import time
from email.message import EmailMessage
from subprocess import Popen, PIPE
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from matplotlib import dates

# https://stackoverflow.com/questions/15713279/calling-pylab-savefig-without-display-in-ipython
plt.ioff()

import numpy as np
import pandas as pd

# https://matplotlib.org/gallery/text_labels_and_annotations/date.html
# https://matplotlib.org/api/_as_gen/matplotlib.pyplot.subplots.html#matplotlib.pyplot.subplots
# https://matplotlib.org/api/dates_api.html#matplotlib.dates.MonthLocator
# https://matplotlib.org/api/_as_gen/matplotlib.pyplot.plot.html#matplotlib.pyplot.plot
# https://matplotlib.org/tutorials/introductory/pyplot.html

import sensorutils

FIGSIZE = (7, 2)


def generate_mail(location: str, dataframe: pd.DataFrame, config1: dict, verbose: bool):
    message = EmailMessage()
    message.set_charset('utf-8')
    message['To'] = ' '.join(config1['mail_to'])
    message['From'] = config1['mail_from']
    message['Subject'] = f'temperature & humidity: {location}'
    basic_message = 'Now = %s\nServer = %s' % (datetime.datetime.now().isoformat(),
                                               platform.node())
    message.add_attachment(basic_message.encode('utf-8'),
                        disposition='inline',
                        maintype='text', subtype='plain')
    # https://docs.python.org/3/library/email.examples.html

    plot_files = generate_plots(location, dataframe, config1, verbose)

    for plot_file in plot_files:
        with open(plot_file, 'rb') as fp:
            img_data = fp.read()
        message.add_attachment(img_data, maintype='image',
                            disposition='inline',
                            subtype=imghdr.what(None, img_data))
    p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
    p.communicate(message.as_bytes())
    return


def generate_plots(location: str, dataframe: pd.DataFrame, config1: dict, verbose: bool):
    output_dir = '/tmp/sensor-plots-%i' % int(time.time())
    os.mkdir(output_dir)
    f0 = os.path.join(output_dir, 'tem_7_days_smoothed.png')
    f1 = os.path.join(output_dir, 'hum_7_days_smoothed.png')
    f2 = os.path.join(output_dir, 'tem_12_days_ranged.png')
    f3 = os.path.join(output_dir, 'hum_12_days_ranged.png')

    days_locator = dates.DayLocator(interval=1)
    # days_format = dates.DateFormatter('%Y-%m-%d')
    days_format = dates.DateFormatter('%d')

    dataframe = dataframe.groupby(pd.Grouper(key='timestamp', freq=config1['averaging'])).mean()

    return []



# MAIN
def read_and_plot(options):

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

for location0, dataframe0 in dataframe_map.items():
    generate_mail(location0, dataframe0, config, options.verbose)


