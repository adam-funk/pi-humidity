#!/usr/bin/env python3
import argparse
import shutil

import pandas as pd

import sensorutils


def process(filename):
    backup = filename + '.BAK'
    print(f'backing up {filename} -> {backup}')
    shutil.copy(filename, backup)
    dataframe = pd.read_csv(filename, index_col=False, names=sensorutils.COLUMNS)
    print(f'data: {dataframe.shape}')
    dataframe['resistance'] = round(dataframe['resistance'] / 1000)
    print(f'writing {filename}')
    dataframe.to_csv(filename, index=False, header=False)
    return


parser = argparse.ArgumentParser(description="Client for temperature logging",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('files', metavar='FILE(S)', nargs='*',
                    help='files')

options = parser.parse_args()

for data_file in options.files:
    process(data_file)