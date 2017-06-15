import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
import re
from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.plotly as py
import plotly.graph_objs as go
from operator import itemgetter
import itertools


#########################
####### HELPERS #########
#########################

########### Excel writing functions
def create_wb(test_name):
    writer = pd.ExcelWriter(str(test_name)+'-output.xlsx', engine = 'xlsxwriter')
    return writer

def write_multiple_dfs(writer, df_list, worksheet_name, spaces, content_instruction):
    row = 5
    for x in range(len(df_list)):
        df_list[x].to_excel(writer, sheet_name=worksheet_name, startrow=row , startcol=0)   
        worksheet = writer.sheets[worksheet_name]
        row = row - 5
        df_instruction(worksheet, row, content_instruction[x])
        row = row + len(df_list[x].index) + spaces + 11

def df_instruction(worksheet, row, text):
    col = 0
    # Example
    options = {
        'font': {'bold': True, 'color': '#67818a'},
        'border': {'color': 'red', 'width': 3,
                   'dash_type': 'round_dot'},
        'width': 512,
        'height': 100
    }
    worksheet.insert_textbox(row, col, text, options)
    # don't save (wait for other thermocouples)


########### Soak and Ramp Analysis
def soak_analysis(channel_name, amb, ambient, df_chan_Ambient, ls_index_cold, ls_index_hot, start_index_list):
    
    df_soak_low = ambient.loc[ls_index_cold].sort_values(['Sweep_screen']).reset_index(drop=True)
    df_soak_high = ambient.loc[ls_index_hot].sort_values(['Sweep_screen']).reset_index(drop=True)

    ## replace first keypoint 0 index with 4
    #reset_start_index_list = [4 if i==0 else i for i in start_index_list]
    down_i = start_index_list[0]
    up_i = start_index_list[1]
    cold_i = start_index_list[2]
    hot_i = start_index_list[3]

    mean_temp_low, mean_temp_high = [], []
    max_temp_low, max_temp_high = [], []
    min_temp_low, min_temp_high = [], []

    number_of_cycles = int(ambient.shape[0]/4)
    
    for i in range(number_of_cycles):
        df_temp_low, df_temp_high = pd.DataFrame(), pd.DataFrame()
        if cold_i > up_i:
            up_i += 4
        if hot_i > down_i:
            down_i += 4

        cold = 4*i+cold_i
        up = 4*i+up_i
        hot = 4*i+hot_i
        down = 4*i+down_i

        if cold == ambient.shape[0]: cold = cold-1
        if up == ambient.shape[0]: up = up-1
        if hot == ambient.shape[0]: hot = hot-1
        if down == ambient.shape[0]: down = down-1
        df_temp_low = df_chan_Ambient.iloc[int(ambient.iloc[cold]['Sweep_screen']):int(ambient.iloc[up]['Sweep_screen']),[3]]
        df_temp_high = df_chan_Ambient.iloc[int(ambient.iloc[hot]['Sweep_screen']):int(ambient.iloc[down]['Sweep_screen']),[3]]

        mean_temp_low.append(df_temp_low.mean(axis=0).ix[0])
        mean_temp_high.append(df_temp_high.mean(axis=0).ix[0])
        max_temp_low.append(df_temp_low.max(axis=0).ix[0])
        max_temp_high.append(df_temp_high.max(axis=0).ix[0])
        min_temp_low.append(df_temp_low.min(axis=0).ix[0])
        min_temp_high.append(df_temp_high.min(axis=0).ix[0])

    df_soak_low['mean_temp'] = pd.Series(mean_temp_low)
    df_soak_high['mean_temp'] = pd.Series(mean_temp_high)
    df_soak_low['max_temp'] = pd.Series(max_temp_low)
    df_soak_high['max_temp'] = pd.Series(max_temp_high)
    df_soak_low['min_temp'] = pd.Series(min_temp_low)
    df_soak_high['min_temp'] = pd.Series(min_temp_high)
    return df_soak_high, df_soak_low


def ramp_analysis(ambient, df_chan_Ambient, ls_index_down, ls_index_up):
    df_transform_down = ambient.loc[ls_index_down].sort_values(['Sweep_screen']).reset_index(drop=True)
    df_transform_up =ambient.loc[ls_index_up].sort_values(['Sweep_screen']).reset_index(drop=True)
    return df_transform_down, df_transform_up


def calculate_ramp_stats(channel_name, ambient, df_chan_Ambient_loc, date_format):
    ### Adds time duration
    time = []
    for m in range(ambient.shape[0]-1):
        a1 = ambient['Time'][m+1]
        a2 = ambient['Time'][m]
        time.append((datetime.strptime(a1, date_format) - datetime.strptime(a2, date_format)).total_seconds())

    time.append(np.nan)
    ambient.insert(0,'duration',time)
    ambient['duration_minutes'] = ambient['duration']/60 ## translate duration to minutes

    # temp range difference of consecutive rows
    ambient['ramp_temp'] = pd.Series(0, index=df_chan_Ambient_loc.index)
    ambient['ramp_temp'] = ambient[channel_name].shift(-1) - ambient[channel_name]
    
    # Find ramp rates
    ambient['ramp_rate'] = pd.Series(0, index=df_chan_Ambient_loc.index)
    ambient['ramp_rate'] = ambient['ramp_temp']*60/ambient['duration']
    return ambient


########### Envelope for thresholds
def get_points_above_and_below_thresholds(df_chan_Ambient, channel, upper_threshold, lower_threshold):
    # the indices of all the points of temp out of threshold
    High_index = df_chan_Ambient[channel][df_chan_Ambient[channel] >= upper_threshold].index.tolist()
    Low_index = df_chan_Ambient[channel][df_chan_Ambient[channel] <= lower_threshold].index.tolist()
    point_index = []
    for i in range(len(Low_index)):
        point_index.append(Low_index[i])
    for i in range(len(High_index)):
        point_index.append(High_index[i]) 
    point_index = np.sort(point_index).tolist()
    return df_chan_Ambient.loc[point_index]


########### Keypoints for each cycle
def get_amb_key_points(df_chan_Ambient, channel, df_chan_Ambient_loc, upper_threshold, lower_threshold):
    ''' Get key points for ambient channel '''

    transitions = find_transition_indices(df_chan_Ambient_loc, channel, upper_threshold, lower_threshold)
    key_point = get_key_point_basedon_period(df_chan_Ambient, channel, transitions, upper_threshold, lower_threshold)
    ambient = df_chan_Ambient.loc[key_point].sort_values(['Sweep_screen']).reset_index(drop=True)
    return ambient

def get_keypoints_for_each_cycle(channel, ambient, df_chan, upper_threshold, lower_threshold):
    ''' Get get keypoints each cycle of a non-ambient channel (Thermal Shock) '''

    ls_cycle_bound = [] ## bounds rand to search each cycle for key points
    high_index = []  ## all poitns above high threshold
    low_index = []  ## all points below low threshold
    ls_cycle = [] ## list of lists --> nested list is search bounds of sweep screen
    cycle_ls = []  ## list of integers - cycles that DID reach threhold(s)
    point_cycle_index = [] ## merged low and high key points for each cycle
    key_point_cycle = []  ## list holding dataframes of key cycle points
    n_reach = []  ## list of the "not-reach" cycles' keypoint dataframes
    n_reach_cycle = []  ## list of integers - cycles that DID NOT reach threhold(s)

    number_of_ambient_cycles = ambient.shape[0]//4
    ripple_gap = (ambient.iloc[4].Sweep_screen - ambient.iloc[0].Sweep_screen)//8
    for i in range(number_of_ambient_cycles): 
        cycle_ls.append(i)
        ## find boundary to search
        if i != number_of_ambient_cycles - 1:  ## last cycle in loop
            ls_cycle_bound.append(ambient.iloc[[4*i,4*i+6]].Sweep_screen.tolist())
        else:  ## not last cycle in loop 
            ls_cycle_bound.append(ambient.iloc[[4*i,ambient.shape[0]-1]].Sweep_screen.tolist())

        if ls_cycle_bound[i][0] < int(ripple_gap): ## at beginning of profile (sweep screen smaller than 5)
            ls_cycle_bound[i][0] = 0
        else: ## not at beginning
            ls_cycle_bound[i][0] = ls_cycle_bound[i][0] - int(ripple_gap)

        if ls_cycle_bound[i][1] > ambient.Sweep_screen[ambient.shape[0]-1] - int(ripple_gap): ## at end
            ls_cycle_bound[i][1] = ambient.Sweep_screen[ambient.shape[0]-1]
        else:  ## not at end
            ls_cycle_bound[i][1] = ls_cycle_bound[i][1] + int(ripple_gap)

        ls_cycle_component = df_chan.iloc[ls_cycle_bound[i][0]:ls_cycle_bound[i][1]]
        ls_cycle_component.insert(0,'cycle#',i+1)
        ls_cycle.append(ls_cycle_component)

        #The index of all the points of temp out of threshold
        high_index = ls_cycle[i][channel][ls_cycle[i][channel] >= upper_threshold].index.tolist()
        low_index = ls_cycle[i][channel][ls_cycle[i][channel] <= lower_threshold].index.tolist()
        point_index = []
        for m in range(int(len(low_index))):
            point_index.append(low_index[m])
        for n in range(int(len(high_index))):
            point_index.append(high_index[n])   

        point_index = np.sort(point_index).tolist()
        point_cycle_index.append(point_index)
        ls_cycle[i] = ls_cycle[i].loc[point_cycle_index[i]]
        
        transitions = find_transition_indices(ls_cycle[i], channel, upper_threshold, lower_threshold)
        key_point = get_key_point_basedon_period(df_chan, channel, transitions, upper_threshold, lower_threshold)
        result_points = ls_cycle[i].loc[key_point].sort_values(['Sweep_screen'])

        if result_points.shape[0]< 5 and i!=ambient.shape[0]//4-1:
            n_reach.append(result_points)
            n_reach_cycle.append(i)
        elif result_points.shape[0]< 4 and i == ambient.shape[0]//4-1:
            n_reach.append(result_points)
            n_reach_cycle.append(i)
        elif result_points.shape[0]>3 and i ==ambient.shape[0]//4-1:
            key_point_cycle.append(result_points)
        else:
            result_points = result_points.iloc[0:4]
            key_point_cycle.append(result_points)

    for cycle in n_reach_cycle:  ## remove cycles that DID NOT reach from cycle list 
        cycle_ls.remove(cycle)

    return key_point_cycle, cycle_ls,  n_reach, n_reach_cycle


########### Determine Starting Point Case (e.g. - up-ramp, down-ramp, high-soak, low-soak)
def find_starting_point_case(amb, ambient, upper_threshold, lower_threshold):
    starting_temp = ambient.iloc[0][amb] ## temp of first key point
    temp_diff_between_first_two_key_pts = starting_temp - ambient.iloc[1][amb]

    if abs((starting_temp - upper_threshold)) < abs((starting_temp - lower_threshold)):
        ### starts at upper thresh
        if abs(temp_diff_between_first_two_key_pts) < (upper_threshold-lower_threshold)*.5:
            ### is a hot soak
            ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_high_soak(ambient)
        else:
            ### hot to cold ramp
            ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_transform_down(ambient)
    else:
        ### starts at lower thresh 
        if abs(temp_diff_between_first_two_key_pts) < (upper_threshold-lower_threshold)*.5:
            ## is a cold soak
            ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_low_soak(ambient)
        else: 
            ### cold to hot ramp
            ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_transform_up(ambient)
    return ls_index_down, ls_index_up, ls_index_cold, ls_index_hot

def set_transform_down(ambient):
    print('STARTING POINT: TRANSFORM DOWN')
    down_i, up_i, cold_i, hot_i = 0, 2, 1, 3
    return [down_i, up_i, cold_i, hot_i]

def set_transform_up(ambient):
    print('STARTING POINT: TRANSFORM UP')
    down_i, up_i, cold_i, hot_i = 2, 0, 3, 1
    return [down_i, up_i, cold_i, hot_i]

def set_high_soak(ambient):
    print('STARTING POINT: HIGH SOAK')
    down_i, up_i, cold_i, hot_i = 1, 3, 2, 0
    return [down_i, up_i, cold_i, hot_i]

def set_low_soak(ambient):
    print('STARTING POINT: LOW SOAK')
    down_i, up_i, cold_i, hot_i = 3, 1, 0, 2
    return [down_i, up_i, cold_i, hot_i]


########### Analysis Summary
def create_analysis_summary(channel, amb, df_soak_high, df_soak_low, df_transform_down, df_transform_up):

    if channel == amb:
        soak_columns_wo_cyc = [5,8,9,10]
        transform_columns_amb = [5,6,7]
        ### if ambient, concat and then add cycle# index
        result_each_cycle = pd.concat([df_soak_low.iloc[:,soak_columns_wo_cyc], df_soak_high.iloc[:,soak_columns_wo_cyc], df_transform_down.iloc[:,transform_columns_amb], df_transform_up.iloc[:,transform_columns_amb]], axis=1)
        result_each_cycle.insert(0, 'cycle#', pd.Series(list(range(1,result_each_cycle.shape[0]+1))))

    else:
        soak_columns_with_cyc = [1,6,9,10,11] ## 'cycle#', 'duration_minutes', 'mean_temp', 'max_temp', 'min_temp'
        soak_columns_wo_cyc = [6,9,10,11]  ## 'duration_minutes', 'mean_temp', 'max_temp', 'min_temp'
        transform_columns_non_amb = [6,7,8]
        result_each_cycle = pd.concat([df_soak_low.iloc[:,soak_columns_with_cyc], df_soak_high.iloc[:,soak_columns_wo_cyc], df_transform_down.iloc[:,transform_columns_non_amb], df_transform_up.iloc[:,transform_columns_non_amb]], axis=1)

    cycles_label = ['cycle#', 
                     'cold_soak_duration_minute', 'cold_soak_mean_temp_c', 'cold_soak_max_temp_c', 'cold_soak_min_temp_c', 
                     'hot_soak_duration_minute', 'hot_soak_mean_temp_c', 'hot_soak_max_temp_c', 'hot_soak_min_temp_c', 
                     'down_recovery_time_minute', 'down_RAMP_temp_c', 'down_RAMP_rate_c/minute', 
                     'up_recovery_time_minute', 'up_RAMP_temp_c', 'up_RAMP_rate_c/minute']

    result_each_cycle.columns = cycles_label
    ls_mean, ls_std, ls_min, ls_min_cid, ls_max, ls_max_cid= [], [], [], [], [], []

    for i in range(1, result_each_cycle.shape[1]):
        ls_mean.append(result_each_cycle.ix[:,i].mean())
        ls_std.append(result_each_cycle.ix[:,i].std())
        ls_max.append(result_each_cycle.ix[:,i].max())
        ls_min.append(result_each_cycle.ix[:,i].min())
        ls_min_cid.append(result_each_cycle.ix[:,i].idxmin())
        ls_max_cid.append(result_each_cycle.ix[:,i].idxmax())

    summary_label = cycles_label[1:]

    df_summary = pd.DataFrame.from_items([('mean', ls_mean), ('min', ls_min),('min_cycle#', ls_min_cid), ('max', ls_max), ('max_cycle#', ls_max_cid),('std_dev', ls_std)],orient='index', columns=summary_label)
    df_summary = df_summary.iloc[:, :14]
    df_summary = df_summary.round(2)
    result_each_cycle = result_each_cycle.round(2)
    result_each_cycle.set_index('cycle#', inplace=True)
    
    return result_each_cycle, df_summary


def find_transition_indices(df, channel, upper_threshold, lower_threshold):
    df['last_temp'] = df[channel].shift(1)
    df['next_temp'] = df[channel].shift(-1)
    transition_diff = (abs(upper_threshold)+abs(lower_threshold))/2
    transitions = [0]
    for index, row in df.iterrows():
        diff_last = abs(row[channel]-row['last_temp'])
        diff_next = abs(row[channel]-row['next_temp'])
        if diff_last > transition_diff:
            transitions.append(index)
        if diff_next > transition_diff:
            transitions.append(index)
    transitions.append(df.index[-1])
    return transitions


def get_key_point_basedon_period(df_chan_Ambient, channel, transitions, upper_threshold, lower_threshold):
    channel_period = []
    key_point = []

    for i in range(len(transitions)-1): 
        if df_chan_Ambient[channel].iloc[transitions[i]] > 0 and df_chan_Ambient[channel].iloc[transitions[i+1]] > 0:
            channel_period.append([transitions[i], transitions[i+1]])
        if df_chan_Ambient[channel].iloc[transitions[i]] < 0 and df_chan_Ambient[channel].iloc[transitions[i+1]] < 0:
            channel_period.append([transitions[i], transitions[i+1]])


    for j in range(len(channel_period)):
        ls_period_1 = df_chan_Ambient[channel].iloc[channel_period[j][0]:channel_period[j][1]+1][df_chan_Ambient[channel].iloc[channel_period[j][0]:channel_period[j][1]+1]<= lower_threshold].index.tolist()
        ls_period_2 = df_chan_Ambient[channel].iloc[channel_period[j][0]:channel_period[j][1]+1][df_chan_Ambient[channel].iloc[channel_period[j][0]:channel_period[j][1]+1]>= upper_threshold].index.tolist()
        ls_period = ls_period_1 + list(set(ls_period_2) - set(ls_period_1))
        ls_period = sorted(ls_period)
        consecutive_points = []

        for k, g in itertools.groupby(enumerate(ls_period), lambda x: x[1]-x[0] ) :
            consecutive_points.append(list(map(itemgetter(1), g)))
        key_point.append(max(consecutive_points, key=len)[0])
        key_point.append(max(consecutive_points, key=len)[-1])

    if key_point != []: 
        del key_point[0]
        if df_chan_Ambient.shape[0] <= channel_period[-1][-1]+1:
            del key_point[-1]
    return key_point