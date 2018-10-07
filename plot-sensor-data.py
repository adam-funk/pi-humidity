from collections import defaultdict

import matplotlib.pyplot as plt
import numpy
import datetime
from matplotlib import dates

default_data_file = '/home/adam/home-data.tsv'


def round_down_date(timestamp):
    d = datetime.date.fromtimestamp(timestamp)
    dt = datetime.datetime.combine(d, datetime.time(0, 0, 0))
    return int(dt.timestamp())


def read_raw_data(data_file):
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
                # TODO log this and add to e-mail body
                print("Rejected", epoch, temp, hum)
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
        timestamps.append(numpy.datetime64((prev_epoch + epoch)//2, 's'))
        temp = data_to_use[epoch][0]
        hum = data_to_use[epoch][1]
        temperatures.append((prev_temp + temp)/2)
        humidities.append((prev_hum + hum)/2)
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

general_data = read_raw_data(default_data_file)
all_timestamps, all_temperatures, all_humidities = average_data(general_data)

plt.ion()

fig, ax = plt.subplots()

days = dates.DayLocator(interval=1)
daysFmt = dates.DateFormatter('%Y-%m-%d')

ax.xaxis.set_major_locator(days)
ax.xaxis.set_major_formatter(daysFmt)
ax.format_xdata = daysFmt

fig.autofmt_xdate()

ax.plot(all_timestamps, all_temperatures, 'b,-',
        all_timestamps, all_humidities, 'g,-')

datestamps, tmin, tmean, tmax, hmin, hmean, hmax = daily_data(general_data)

ax.plot(datestamps, tmin, 'b-',
        datestamps, tmean, 'b-',
        datestamps, tmax, 'b-',
        datestamps, hmin, 'g-',
        datestamps, hmean, 'g-',
        datestamps, hmax, 'g-'
        )


# https://matplotlib.org/gallery/text_labels_and_annotations/date.html
# https://matplotlib.org/api/_as_gen/matplotlib.pyplot.subplots.html#matplotlib.pyplot.subplots
# https://matplotlib.org/api/dates_api.html#matplotlib.dates.MonthLocator
# https://matplotlib.org/api/_as_gen/matplotlib.pyplot.plot.html#matplotlib.pyplot.plot
# https://matplotlib.org/tutorials/introductory/pyplot.html

# TODO
# max mean min for each day
# convert epoch to datetime then take ymd only
