# pi-humidity

Tools for logging BME680 air data and generating
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
* CSV
* columns: 
  * epoch time
  * readable time
  * location
  * temperature °C
  * humidity %
  * pressure hPa
  * resistance Ω
  * time required to make readings

## TODO
* change Ω to kΩ
* temporary script to convert existing files
