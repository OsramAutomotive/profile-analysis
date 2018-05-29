
from core.data_import import *
from core.ptc_analysis import *
from core.ptc_helpers import *
from core.plot import *

def define_test_parameters(datapath):
    file_extension = datapath.split('.')[-1]
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



datapath = r"\\Chfile1\ecs_landrive\Automotive_Lighting\LED\Test Engineering\E2E Testing\Profile Program\PTC\PTC (A1XC -40 to 70).csv"
#datapath = r"L:\Automotive_Lighting\LED\P552 MCA Headlamp\P552 MCA Aux\ADVPR\PV Aux\TL A&B\PTC\Raw Data\20170206_184930_P552 MCA PV PTC_01_B4.txt"
#datapath = r"C:\Users\s.chen6\Desktop\test.csv"
#datapath = r"L:\Automotive_Lighting\LED\P552 MCA Headlamp\P552 MCA Aux\ADVPR\PV Aux\TL A&B\PTC\Raw Data\20170206_184930_P552 MCA PV PTC_01_B6.txt"
#datapath = r"\\Chfile1\ecs_landrive\Automotive_Lighting\LED\A1XC\DVPR\PTC\Up Level\Raw Data Agilent\20170530_034641000\dat00001.csv"
#datapath = r"C:\Users\s.chen6\Desktop\PTC (A1XC -40 to 70).csv"

regex_temp, date_format, sep, file_extension = define_test_parameters(datapath)

test_name = 'ptc'
upper_threshold, lower_threshold = 85, -40
tolerance = 3
rate_adjustment = 0
ambient_channel_number = 1

## DATA IMPORT
df, channels, amb = import_data_without_date_index(datapath, ambient_channel_number, regex_temp, sep=sep)

## ANALYSIS
tc_channel_names = {}
for chan in channels:
    tc_channel_names[chan] = ''
#PLOT
#plot_profile(test_name, df, channels, tc_channel_names)

ptc_analyze_all_channels(df, channels, amb, tc_channel_names, upper_threshold, lower_threshold, tolerance, rate_adjustment, date_format, file_extension, test_name)

