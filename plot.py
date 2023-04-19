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
        warnings.filterwarnings(action='ignore', category=RuntimeWarning, message='All-NaN slice encountered')
        result = round(np.nanmean(x), 1)
    return result


def medianr(x):
    # ignore NaN (blank fields in the CSV) and averages over missing times
    with warnings.catch_warnings():
        warnings.filterwarnings(action='ignore', category=RuntimeWarning, message='Mean of empty slice')
        warnings.filterwarnings(action='ignore', category=RuntimeWarning, message='All-NaN slice encountered')
        result = round(np.nanmedian(x), 1)
    return result


def minr(x):
    m = min(x)
    if np.isnan(m):
        return np.nan
    return round(m)


def maxr(x):
    m = min(x)
    if np.isnan(m):
        return np.nan
    return round(m)


def generate_mail(location0: str, dataframe0: pd.DataFrame, config1: dict, verbose: bool):
    message = EmailMessage()
    message.set_charset('utf-8')
    message['To'] = ','.join(config1['mail_to'])
    message['From'] = config1['mail_from']
    message['Subject'] = f'temperature & humidity: {location0}'
    # https://docs.python.org/3/library/email.examples.html

    buffers, html = generate_plots(dataframe0, config1, verbose)
    for buffer in buffers:
        buffer.seek(0)
        img_data = buffer.read()
        message.add_attachment(img_data, maintype='image',
                               disposition='inline',
                               subtype=imghdr.what(None, img_data))
    message.add_attachment(html.encode('utf-8'), disposition='inline',
                           maintype='text', subtype='html')
    basic_message = f'{datetime.datetime.now().isoformat().split("T")[0]}\n{platform.node()}'
    message.add_attachment(basic_message.encode('utf-8'),
                           disposition='inline',
                           maintype='text', subtype='plain')
    p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
    p.communicate(message.as_bytes())
    return


def produce_plot(dataframe0: pd.DataFrame, column: str, color: str, minor: bool) -> BytesIO:
    days_locator = dates.DayLocator(interval=1)
    days_format = dates.DateFormatter('%d')
    buffer0 = BytesIO()
    fig0, ax0 = plt.subplots(figsize=FIG_SIZE)
    ax0.xaxis.set_major_locator(days_locator)
    if minor:
        minor_locator = dates.HourLocator(byhour=[0, 6, 12, 18])
        ax0.xaxis.set_minor_locator(minor_locator)
        ax0.grid(True, which='minor', color='lightgray')
    ax0.xaxis.set_major_formatter(days_format)
    ax0.format_xdata = days_format
    ax0.grid(True, which='major', color='gray')
    ax0.plot(dataframe0.index, dataframe0[column], color)
    # autofmt needs to happen after data
    fig0.autofmt_xdate(rotation=60)
    plt.savefig(buffer0, dpi=200, format='png')
    plt.close(fig0)
    return buffer0


def generate_plots(dataframe0: pd.DataFrame, config1: dict, verbose: bool):
    agg_columns = [minr, meanr, medianr, maxr]
    with warnings.catch_warnings():
        warnings.filterwarnings(action='ignore', message='All-NaN slice encountered')
        date_data = dataframe0.groupby('date').agg({'temperature': agg_columns,
                                                    'humidity': agg_columns,
                                                    'pressure': agg_columns,
                                                    'resistance': agg_columns}).rename(
            columns={'minr': 'min', 'meanr': 'mean', 'medianr': 'mdn', 'maxr': max})
    html = date_data.to_html()

    pngs = []
    averaged = dataframe0.drop(labels=['iso_time', 'location', 'date'],
                               axis=1).groupby(pd.Grouper(key='timestamp', freq=config1['averaging'])).mean()
    cutoff_time = sensorutils.get_cutoff_time(config1['days_smoothed'])
    averaged = averaged[averaged.index >= cutoff_time]
    if verbose:
        print('Smoothed df', averaged.shape)

    columns = [min, meanr, medianr, max]
    dated = dataframe0.groupby('date').agg({'temperature': columns, 'humidity': columns,
                                            'pressure': columns, 'resistance': columns}).rename(
        columns={'meanr': 'mean', 'medianr': 'mdn'})
    cutoff_date = sensorutils.get_cutoff_date(config1['days_ranged'])
    dated = dated[dated.index >= cutoff_date]
    if verbose:
        print('Dated df', dated.shape)

    pngs.append(produce_plot(averaged, 'temperature', '-b', True))
    pngs.append(produce_plot(averaged, 'humidity', '-g', True))
    pngs.append(produce_plot(averaged, 'pressure', '-b', True))
    pngs.append(produce_plot(averaged, 'resistance', '-r', True))
    pngs.append(produce_plot(dated, 'temperature', '-', False))
    pngs.append(produce_plot(dated, 'humidity', '-', False))
    pngs.append(produce_plot(dated, 'pressure', '-', False))
    pngs.append(produce_plot(dated, 'resistance', '-', False))
    return pngs, html


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

location = config['location']
data_location = sensorutils.DataLocation(config['data_directory'], options.verbose)

max_days_ago = max(config['days_smoothed'], config['days_ranged'])
if options.verbose:
    print('max days ago', max_days_ago)

dataframe = data_location.get_dataframe(max_days_ago, location)
generate_mail(location, dataframe, config, options.verbose)
