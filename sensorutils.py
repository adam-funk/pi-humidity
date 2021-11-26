# common code for handling the data directory

# filename format:
# DATA_DIR/sensors-yyyy-mm-dd.csv

# file format:
# epoch, date_time, location, temperature, humidity
import datetime


class DataLocation:

    def __init__(self, data_directory):
        self.directory = data_directory

    def get_file(self, date: datetime.date):