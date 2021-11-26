# common code for handling the data directory

# filename format:
# DATA_DIR/sensors-yyyy-mm-dd.tsv

# file format:
# epoch, date_time, location, temperature, humidity
import datetime
import os.path


class DataLocation:

    def __init__(self, data_directory, verbose):
        self.directory = data_directory
        self.verbose = verbose

    def get_filename(self, date: datetime.date):
        """
        Generate the correct filename for the given date.
        """
        date_string = date.isoformat()
        filename = os.path.join(self.directory, f'sensors{date_string}.tsv')
        return filename

    def find_files(self, max_days_ago: int):
        """
        Search the directory for data files up to X days ago.
        """
        date_range = [datetime.date.today() - datetime.timedelta(days=d) for d in range(0, max_days_ago)]
        look_for = [self.get_filename(d) for d in date_range]
        return [filename for filename in look_for if os.path.exists(filename)]

    def record(self, epoch: int, date_time: datetime.datetime, location:str, temperature: float, humidity: float):
        filename = self.get_filename(date_time.date())
        iso_time = datetime.datetime.isoformat(date_time).split('.')[0]
        output = f'{epoch}\t{iso_time}\t{location}\t{temperature}\t{humidity}\n'
        with open(filename, 'a', encoding='utf-8') as f:
            if self.verbose:
                print('writing to', filename)
                print(output)
            f.write(output)
        return
