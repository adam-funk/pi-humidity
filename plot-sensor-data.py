import matplotlib, numpy
import matplotlib.pyplot as plt
from matplotlib import dates

data_file = 'home-data.tsv'

timestamps = []
temperatures = []
humidities = []

days = dates.DayLocator(interval=1)
daysFmt = dates.DateFormatter('%Y-%m-%d')

with open(data_file, 'r') as f:
    for line in f.readlines():
        line_data = line.rstrip().split('\t')
        epoch = int(line_data[0])
        temp = float(line_data[3])
        hum = float(line_data[4])
        if (-10 < temp < 150) and (-1 < hum < 101):
            nepoch = numpy.datetime64(epoch, 's')
            timestamps.append(nepoch)
            temperatures.append(temp)
            humidities.append(hum)
        else:
            print("Rejected", epoch, temp, hum)

plt.ion()

fig, ax = plt.subplots()

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
