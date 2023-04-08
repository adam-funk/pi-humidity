# pi-humidity

Tools for logging DHT22 temperature and humidity and generating
plots, intended for use from cron.

## required config file

* `data_directory`: "/home/adam/FILTER",
* `mail_to`: list of e-mail addresses
* `mail_from`: e-mail address
* `averaging`: string used as `freq` argument of `pandas.Grouper` for 
   smoothing (averaging) the readings before plotting
* `days_smoothed`: how many days back to cover in the main plot
* `days_ranged`: how many days back to cover in the daily summary plot
* `location`: string used in reports
* `timeout`: in seconds

## data file format
* TSV
* columns: epoch time, readable time, location, temperature °C, humidity %, pressure hPa, resistance Ω 

## TODO
* change TSV to CSV
  * plot.py
  * record.py
  * existing data
* add column for elapsed time
* add resistance to plot.py
* tidy up empty string for None
