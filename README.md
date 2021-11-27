# pi-humidity

Tools for logging DHT22 temperature and humidity and generating
plots, intended for use from cron.

## required config file

* `sensors`: list of sensor specifications
  * `led_pin` and `sensor_pin`: GPIO pins
  * `location`: human-readable description
* `data_directory`: "/home/adam/FILTER",
* `mail_to`: list of e-mail addresses
* `mail_from`: e-mail address
* `averaging`: string used as `freq` argument of `pandas.Grouper` for 
   smoothing (averaging) the readings before plotting
* `days_smoothed`: how many days back to cover in the main plot
* `days_ranged`: how many days back to cover in the daily summary plot

## origin of DHT22.py code:

https://github.com/joan2937/pigpio/blob/master/EXAMPLES/Python/DHT22_AM2302_SENSOR/DHT22.py
