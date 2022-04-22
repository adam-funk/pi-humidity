#!/usr/bin/env python3

import argparse
import datetime
import imghdr
import json
import platform
import warnings
from email.message import EmailMessage
from io import BytesIO
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

FIG_SIZE = (7, 2)


def meanr(x):
    # ignore NaN (blank fields in the CSV) and averages over missing times
    with warnings.catch_warnings():
        warnings.filterwarnings(action='ignore', category=RuntimeWarning, message='Mean of empty slice')
        result = round(np.nanmean(x), 1)
    return result


def medianr(x):
    # ignore NaN (blank fields in the CSV) and averages over missing times
    with warnings.catch_warnings():
        warnings.filterwarnings(action='ignore', category=RuntimeWarning, message='Mean of empty slice')
        result = round(np.nanmedian(x), 1)
    return result

def generate_mail(location: str, dataframe: pd.DataFrame, config1: dict, verbose: bool):
    message = EmailMessage()
    message.set_charset('utf-8')
    message['To'] = ','.join(config1['mail_to'])
    message['From'] = config1['mail_from']
    message['Subject'] = f'temperature & humidity: {location}'
    # https://docs.python.org/3/library/email.examples.html

    buffers = generate_plots(location, dataframe, config1, verbose)
    for buffer in buffers:
        buffer.seek(0)
        img_data = buffer.read()
        message.add_attachment(img_data, maintype='image',
                               disposition='inline',
                               subtype=imghdr.what(None, img_data))
    basic_message = f'{datetime.datetime.now().isoformat().split("T")[0]}\n{platform.node()}'
    message.add_attachment(basic_message.encode('utf-8'),
                           disposition='inline',
                           maintype='text', subtype='plain')
    p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
    p.communicate(message.as_bytes())
    return


def generate_plots(location: str, dataframe: pd.DataFrame, config1: dict, verbose: bool):
    days_locator = dates.DayLocator(interval=1)
    days_format = dates.DateFormatter('%d')

    pngs = []
    averaged = dataframe.groupby(pd.Grouper(key='timestamp', freq=config1['averaging'])).mean()
    cutoff_time = sensorutils.get_cutoff_time(config1['days_smoothed'])
    averaged = averaged[averaged.index >= cutoff_time]
    if verbose:
        print('Smoothed df', averaged.shape)

    columns = [min, meanr, medianr, max]
    dated = dataframe.groupby('date').agg({'temperature': columns, 'humidity': columns}).rename(
        columns={'meanr': 'mean', 'medianr': 'mdn'})
    cutoff_date = sensorutils.get_cutoff_date(config1['days_ranged'])
    dated = dated[dated.index >= cutoff_date]
    if verbose:
        print('Dated df', dated.shape)

    # smoothed temperature plot
    buffer0 = BytesIO()
    fig0, ax0 = plt.subplots(figsize=FIG_SIZE)
    ax0.xaxis.set_major_locator(days_locator)
    ax0.xaxis.set_major_formatter(days_format)
    ax0.format_xdata = days_format
    ax0.grid(True, which='both')
    ax0.plot(averaged.index, averaged['temperature'], '-b')
    # autofmt needs to happen after data
    fig0.autofmt_xdate(rotation=60)
    plt.savefig(buffer0, dpi=200, format='png')
    plt.close(fig0)
    pngs.append(buffer0)

    # smoothed humidity plot
    buffer1 = BytesIO()
    fig1, ax1 = plt.subplots(figsize=FIG_SIZE)
    ax1.xaxis.set_major_locator(days_locator)
    ax1.xaxis.set_major_formatter(days_format)
    ax1.format_xdata = days_format
    ax1.grid(True, which='both')
    ax1.plot(averaged.index, averaged['humidity'], '-g')
    # autofmt needs to happen after data
    fig1.autofmt_xdate(rotation=60)
    plt.savefig(buffer1, dpi=200, format='png')
    plt.close(fig1)
    pngs.append(buffer1)

    # temperature by day
    buffer2 = BytesIO()
    fig2, ax2 = plt.subplots(figsize=FIG_SIZE)
    ax2.xaxis.set_major_locator(days_locator)
    ax2.xaxis.set_major_formatter(days_format)
    ax2.format_xdata = days_format
    ax2.grid(True, which='both')
    ax2.plot(dated.index, dated['temperature'], '-')
    fig2.autofmt_xdate(rotation=60)
    plt.savefig(buffer2, dpi=200, format='png')
    plt.close(fig2)
    pngs.append(buffer2)

    # humidity by day
    buffer3 = BytesIO()
    fig3, ax3 = plt.subplots(figsize=FIG_SIZE)
    ax3.xaxis.set_major_locator(days_locator)
    ax3.xaxis.set_major_formatter(days_format)
    ax3.format_xdata = days_format
    ax3.grid(True, which='both')
    ax3.plot(dated.index, dated['humidity'], '-')
    fig3.autofmt_xdate(rotation=60)
    plt.savefig(buffer3, dpi=200, format='png')
    plt.close(fig3)
    pngs.append(buffer3)

    return pngs


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

data_location = sensorutils.DataLocation(config['data_directory'], options.verbose)

max_days_ago = max(config['days_smoothed'], config['days_ranged'])
if options.verbose:
    print('max days ago', max_days_ago)

dataframe_map = data_location.get_dataframes(max_days_ago)

for location0, dataframe0 in dataframe_map.items():
    generate_mail(location0, dataframe0, config, options.verbose)
