# common code for handling the data directory

# filename format:
# DATA_DIR/sensors-yyyy-mm-dd.tsv

# file format:
# epoch, date_time, location, temperature, humidity
import datetime
import os.path

import pandas as pd

COLUMNS = ['epoch', 'iso_time', 'location', 'temperature', 'humidity', 'pressure']


def get_cutoff_date(days_ago: int):
    return datetime.date.today() - datetime.timedelta(days=days_ago)


def get_cutoff_time(days_ago: int):
    cutoff_date = get_cutoff_date(days_ago)
    return datetime.datetime.combine(cutoff_date, datetime.time())


class DataLocation:

    def __init__(self, data_directory, verbose):
        self.directory = data_directory
        self.verbose = verbose

    def get_filename(self, date: datetime.date):
        """
        Generate the correct filename for the given date.
        """
        date_string = date.isoformat()
        filename = os.path.join(self.directory, f'sensors-{date_string}.tsv')
        return filename

    def find_files(self, max_days_ago: int):
        """
        Search the directory for data files up to X days ago.
        """
        date_range = [datetime.date.today() - datetime.timedelta(days=d) for d in range(0, max_days_ago)]
        look_for = [self.get_filename(d) for d in date_range]
        return [filename for filename in look_for if os.path.exists(filename)]

    def record(self, epoch: int, iso_time: datetime.datetime, location: str,
               temperature: float, humidity: float, pressure: float):
        filename = self.get_filename(iso_time.date())
        iso_time = datetime.datetime.isoformat(iso_time).split('.')[0]
        output = f'{epoch}\t{iso_time}\t{location}\t{temperature}\t{humidity}\t{pressure}\n'
        with open(filename, 'a', encoding='utf-8') as f:
            if self.verbose:
                print('writing to', filename)
                print(output)
            f.write(output)
        return

    def get_dataframes(self, max_days_ago: int, location: str) -> pd.DataFrame:
        filenames = self.find_files(max_days_ago)
        dataframes = []
        for fn in filenames:
            if self.verbose:
                print('Reading', fn)
            dataframes.append(pd.read_csv(fn, sep='\t', header=None, names=COLUMNS))
        big_dataframe = pd.concat(dataframes)
        big_dataframe['timestamp'] = pd.to_datetime(big_dataframe['iso_time'])
        big_dataframe['date'] = big_dataframe['timestamp'].dt.date
        # filter out error readings
        big_dataframe = big_dataframe[(big_dataframe['temperature'] > -999) & (big_dataframe['humidity'] > -999) ]
        big_dataframe = big_dataframe.sort_values(by='timestamp', axis=0)
        if self.verbose:
            print('dataframe', big_dataframe.shape)
        del dataframes
        return big_dataframe[big_dataframe['location'] == location]
