import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
import re
# import plotly.plotly as py
# import plotly.graph_objs as go
from operator import itemgetter
import itertools
import os

from core.plot import *
from core.tshock_analysis import *
from core.ptc_analysis import *


# py.sign_in('sjbrun','v1jdPUhNoRgRBpAOOx7Y')


#### TSHOCK
def import_data_with_date_index(datapath, ambient_channel_number, regex_temp, date_format, sep, file_extension):
    ''' Main import function with date index (for plotting) '''
    print('Prepare for plotting...')
    ls_df_all = []
    ls_file = os.listdir(datapath)
    ls_file.sort()

    for filename in ls_file:
        filepath = filename
        df = read_data_for_plot(datapath + '\\' + filepath, date_format, sep, file_extension)
        channels = get_channels(df, regex_temp)
        df = drop_errors(df, channels)
        ls_df_all.append(df)

    df_plot = pd.concat(ls_df_all)
    channels = get_channels(df, regex_temp)
    amb = set_ambient(channels, ambient_channel_number)

    return df_plot, channels, amb


def import_data_without_date_index(df, ambient_channel_number, regex_temp, sep):
    ''' Main import function without date index (for analysis using sweep #) '''
    channels = get_channels(df, regex_temp)
    amb = set_ambient(channels, ambient_channel_number)
    return channels, amb



################################################
############### Helper functions ###############
################################################
def read_data_for_plot(datapath, date_format, sep, file_extension):
    ''' Returns a dataframe of the agilent temperature data '''
    date_parser = lambda x: pd.datetime.strptime(x, date_format)
    if file_extension == 'csv':
        return pd.read_csv(datapath, parse_dates={'Date Time': [1]}, date_parser=date_parser, 
                           index_col='Date Time', engine='python', sep=sep)
    elif file_extension == 'txt':
        return pd.read_csv(datapath, parse_dates={'Date Time': [0,1]}, date_parser=date_parser, 
                           index_col='Date Time', engine='python', sep=sep)
    else:
        raise


###############################################################################
def build_dataframe(datapath):
    print('Building dataframe...')
    ls_df_all = []
    ls_file = os.listdir(datapath)
    ls_file.sort()

    for filename in ls_file:
        filepath = filename
        regex_temp, date_format, sep, file_extension = define_test_parameters(filepath)
        df = pd.read_csv(datapath + '\\' + filepath, sep=sep)
        ls_df_all.append(df)
    return ls_df_all
    #mod_list = os.path.getmtime(datapath) 
###############################################################################


def get_channels(df, regular_expression):
    ''' Find valid TC channel headers in dataframe '''
    return [df.columns[i] for i in range(len(df.columns)) if re.search(regular_expression, df.columns[i])]

def set_ambient(channels, ambient_channel_number):
    ''' Sets the ambient TC from user input integer '''
    for channel in channels:
        if str(ambient_channel_number) in channel:
            return channel

def drop_errors(df, channels):
    ''' Get rid of outrage data and output error list '''
    df_copy = df
    for channel in channels:
        df = df[df[channel] < 150]
        df = df[df[channel] > -100]
    errors = df_copy[~df_copy.index.isin(df.index.tolist())]
    return df

def define_test_parameters(filepath):
    file_extension = filepath.split('.')[-1]
    if file_extension == 'csv':
        regex_temp = '^Chan\s[0-9][0-9][0-9]'
        date_format = '%m/%d/%Y %H:%M:%S:%f'
        sep = ','
    elif file_extension == 'txt':
        regex_temp = 'TC[1-4]$'
        date_format = '%m/%d/%Y %I:%M:%S %p'
        sep = '\t'
    else:
        raise
    return regex_temp, date_format, sep, file_extension
