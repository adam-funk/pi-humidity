from collections import defaultdict

import matplotlib.pyplot as plt
import numpy
from matplotlib import dates

default_data_file = '/home/adam/home-data.tsv'


def read_data(data_file):
    # time -> (temp, hum)
    data_to_use = defaultdict(tuple)

    with open(data_file, 'r') as f:
        for line in f.readlines():
            line_data = line.rstrip().split('\t')
            epoch = int(line_data[0])
            temp = float(line_data[3])
            hum = float(line_data[4])
            if (-10 < temp < 150) and (-1 < hum < 101):
                data_to_use[epoch] = (temp, hum)
            else:
                print("Rejected", epoch, temp, hum)
    raw_times = list(data_to_use.keys())
    raw_times.sort()
    timestamps = []
    temperatures = []
    humidities = []
    prev_epoch = raw_times[0]
    prev_temp = data_to_use[prev_epoch][0]
    prev_hum = data_to_use[prev_epoch][1]
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


# MAIN

timestamps, temperatures, humidities = read_data(default_data_file)

plt.ion()

fig, ax = plt.subplots()

days = dates.DayLocator(interval=1)
daysFmt = dates.DateFormatter('%Y-%m-%d')

ax.xaxis.set_major_locator(days)
ax.xaxis.set_major_formatter(daysFmt)
ax.format_xdata = daysFmt

fig.autofmt_xdate()

ax.plot(timestamps, temperatures, 'b,-',
        timestamps, humidities, 'g,-')

# https://matplotlib.org/gallery/text_labels_and_annotations/date.html
# https://matplotlib.org/api/_as_gen/matplotlib.pyplot.subplots.html#matplotlib.pyplot.subplots
# https://matplotlib.org/api/dates_api.html#matplotlib.dates.MonthLocator
# https://matplotlib.org/api/_as_gen/matplotlib.pyplot.plot.html#matplotlib.pyplot.plot
# https://matplotlib.org/tutorials/introductory/pyplot.html

# TODO
# max and min for each day
# convert epoch to datetime then take ymd only
