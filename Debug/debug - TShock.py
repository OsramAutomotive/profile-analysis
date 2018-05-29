
from core.tshock_analysis import *
from core.tshock_helpers import *
from core.data_import import *

from core.plot import *

#datapath = r"C:\Users\s.chen6\Desktop\test.csv"
#datapath = r"\\Chfile1\ecs_landrive\Automotive_Lighting\LED\Test Engineering\E2E Testing\Profile Program\Fast TShock (MCA)\Raw Data - Fast TShock (MCA -40 to 95).csv"
datapath = r"C:\Users\s.chen6\Desktop\profile-analysis-master\test_data\dat00002.csv"
#datapath = r"\\Chfile1\ecs_landrive\Automotive_Lighting\LED\Test Engineering\E2E Testing\Profile Program\Fast TShock (MCA)\Raw Data - Fast TShock (MCA -40 to 95).csv"


file_extension = 'csv'
test_name = 'open-tcs-test'
upper_threshold, lower_threshold = 95, -40
tolerance = 3
rate_adjustment = 0
ambient_channel_number = 1
sep = ','

## DATA IMPORT
date_format = '%m/%d/%Y %H:%M:%S:%f'
regex_temp = '^Chan\s[0-9][0-9][0-9]'


df, channels, amb = import_data_with_date_index(datapath, ambient_channel_number, regex_temp, date_format, sep, file_extension)  ## df time indexed


## PLOT
#plot_profile(TITLE, df, channels)

## ANALYSIS
## ANALYSIS
tc_channel_names = {}
for chan in channels:
    tc_channel_names[chan] = ''
#PLOT
plot_profile(upper_threshold, lower_threshold, tolerance, test_name, df, channels, tc_channel_names, gl = False)

#analyze_all_channels(df, channels, amb)
tshock_analyze_all_channels(df, channels, amb, tc_channel_names, upper_threshold, lower_threshold, tolerance, rate_adjustment, date_format, file_extension, test_name)
    
