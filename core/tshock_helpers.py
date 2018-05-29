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
    df_soak_low = ambient.loc[ls_index_cold].reset_index(drop=True)
    df_soak_high = ambient.loc[ls_index_hot].reset_index(drop=True)

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

        if ambient.iloc[cold]['Sweep_screen'] == ambient.iloc[up]['Sweep_screen']:
            mean_temp_low.append(np.nan)
            max_temp_low.append(np.nan)
            min_temp_low.append(np.nan)
        else:
            df_temp_low = df_chan_Ambient.iloc[int(ambient.iloc[cold]['Sweep_screen'])-1:int(ambient.iloc[up]['Sweep_screen'])]
            df_temp_low = df_temp_low[[channel_name]]
            mean_temp_low.append(df_temp_low.mean(axis=0).ix[0])
            max_temp_low.append(df_temp_low.max(axis=0).ix[0])
            min_temp_low.append(df_temp_low.min(axis=0).ix[0])

        if ambient.iloc[hot]['Sweep_screen'] == ambient.iloc[down]['Sweep_screen']:
            mean_temp_high.append(np.nan)
            max_temp_high.append(np.nan)
            min_temp_high.append(np.nan)
        else:
            df_temp_high = df_chan_Ambient.iloc[int(ambient.iloc[hot]['Sweep_screen'])-1:int(ambient.iloc[down]['Sweep_screen'])]
            df_temp_high = df_temp_high[[channel_name]]
            mean_temp_high.append(df_temp_high.mean(axis=0).ix[0])
            max_temp_high.append(df_temp_high.max(axis=0).ix[0])
            min_temp_high.append(df_temp_high.min(axis=0).ix[0])

    df_soak_low['mean_temp'] = pd.Series(mean_temp_low)
    df_soak_high['mean_temp'] = pd.Series(mean_temp_high)
    df_soak_low['max_temp'] = pd.Series(max_temp_low)
    df_soak_high['max_temp'] = pd.Series(max_temp_high)
    df_soak_low['min_temp'] = pd.Series(min_temp_low)
    df_soak_high['min_temp'] = pd.Series(min_temp_high)
    return df_soak_high, df_soak_low


def ramp_analysis(ambient, df_chan_Ambient, ls_index_down, ls_index_up):
    df_transform_down = ambient.loc[ls_index_down].reset_index(drop=True)
    df_transform_up =ambient.loc[ls_index_up].reset_index(drop=True)
    return df_transform_down, df_transform_up


def calculate_ramp_stats(channel_name, ambient, date_format):
    ### Adds time duration
    time = []
    check = ambient.isnull()
    for m in range(0, ambient.shape[0]-1):
        a1 = ambient['Time'][m+1]
        a2 = ambient['Time'][m]
        if check.iloc[m][1] == True or check.iloc[m+1][1] == True: 
            time.append(np.nan)
        else: 
            time.append((datetime.strptime(a1, date_format) - datetime.strptime(a2, date_format)).total_seconds())
    time.append(np.nan)
    ambient.insert(0,'duration',time)
    ambient['duration_minutes'] = ambient['duration']/60 ## translate duration to minutes
 
    # temp range difference of consecutive rows
    ambient['ramp_temp'] = pd.Series(np.nan)
    ambient['ramp_temp'] = ambient[channel_name].shift(-1) - ambient[channel_name]
     
    # Find ramp rates
    ambient['ramp_rate'] = pd.Series(np.nan)
    ambient['ramp_rate'] = ambient['ramp_temp']*60/ambient['duration']

    return ambient


########### Determine Starting Point Case (e.g. - up-ramp, down-ramp, high-soak, low-soak)
def find_starting_point_case(amb, ambient, upper_threshold, lower_threshold):
    check = ambient.isnull()
    ls_sweepnum = ambient.Sweep_screen.tolist()
    if all_same(ls_sweepnum) == True:
        ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_low_soak(ambient)
    elif all_same(ls_sweepnum) == False:
        for i in range(0, ambient.shape[0], 4):
            startcase = ambient.iloc[i:i+5]
            ls_startcase = startcase.Sweep_screen.tolist()
            if all_same(ls_startcase) == False:
                
                if startcase.iloc[0][amb]<0 and startcase.iloc[1][amb]<0:
                    ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_low_soak(ambient)
                    break
                if startcase.iloc[2][amb]>0 and startcase.iloc[3][amb]>0:
                    ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_low_soak(ambient)
                    break
                if startcase.iloc[3][amb]>0 and startcase.iloc[4][amb]<0:
                    ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_low_soak(ambient)
                    break

                if startcase.iloc[0][amb]>0 and startcase.iloc[1][amb]>0:
                    ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_high_soak(ambient)
                    break
                if startcase.iloc[2][amb]<0 and startcase.iloc[3][amb]<0:
                    ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_high_soak(ambient)
                    break
                if startcase.iloc[3][amb]<0 and startcase.iloc[4][amb]>0:
                    ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_high_soak(ambient)
                    break

                if startcase.iloc[0][amb]>0 and startcase.iloc[1][amb]<0:
                    ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_transform_down(ambient)
                    break
                if startcase.iloc[2][amb]<0 and startcase.iloc[3][amb]>0:
                    ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_transform_down(ambient)
                    break
                if startcase.iloc[3][amb]>0 and startcase.iloc[4][amb]>0:
                    ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_transform_down(ambient)
                    break

                if startcase.iloc[0][amb]<0 and startcase.iloc[1][amb]>0:
                    ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_transform_up(ambient)
                    break
                if startcase.iloc[2][amb]>0 and startcase.iloc[3][amb]<0:
                    ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_transform_up(ambient)
                    break
                if startcase.iloc[3][amb]<0 and startcase.iloc[4][amb]<0:
                    ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_transform_up(ambient)
                    break

                else: continue
            else: continue
    try:
        ls_index_down # does a exist in the current namespace
    except NameError:
        ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = set_low_soak(ambient)

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
        result_each_cycle = pd.concat([ df_soak_low.iloc[:,soak_columns_wo_cyc], 
                                        df_soak_high.iloc[:,soak_columns_wo_cyc], 
                                        df_transform_down.iloc[:,transform_columns_amb], 
                                        df_transform_up.iloc[:,transform_columns_amb] ], 
                                      axis=1)
        result_each_cycle.insert(0, 'cycle#', pd.Series(list(range(1,result_each_cycle.shape[0]+1))))

    else:
        soak_columns_with_cyc = [1,6,9,10,11]  ## 'cycle#', 'duration_minutes', 'mean_temp', 'max_temp', 'min_temp'
        soak_columns_wo_cyc = [6,9,10,11]  ## 'duration_minutes', 'mean_temp', 'max_temp', 'min_temp'
        transform_columns_non_amb = [6,7,8]
        result_each_cycle = pd.concat([ df_soak_low.iloc[:,soak_columns_with_cyc], 
                                        df_soak_high.iloc[:,soak_columns_wo_cyc], 
                                        df_transform_down.iloc[:,transform_columns_non_amb], 
                                        df_transform_up.iloc[:,transform_columns_non_amb] ], 
                                      axis=1)

    cycles_label = ['cycle#', 
                    'cold_soak_duration_minute', 'cold_soak_mean_temp_c', 'down_RAMP_temp_change_rate_min_temp_c', 'cold_soak_min_temp_c', 
                    'hot_soak_duration_minute', 'hot_soak_mean_temp_c', 'hot_soak_max_temp_c', 'up_RAMP_temp_change_rate_max_temp_c', 
                    'down_recovery_time_minute', 'down_RAMP_temp_c', 'down_RAMP_rate_c/minute', 
                    'up_recovery_time_minute', 'up_RAMP_temp_c', 'up_RAMP_rate_c/minute']

    result_each_cycle.columns = cycles_label
    ls_mean, ls_std, ls_min, ls_min_cid, ls_max, ls_max_cid = [], [], [], [], [], []

    for i in range(1, result_each_cycle.shape[1]):
        ls_mean.append(result_each_cycle.ix[:,i].mean())
        ls_std.append(result_each_cycle.ix[:,i].std())
        ls_max.append(result_each_cycle.ix[:,i].max())
        ls_min.append(result_each_cycle.ix[:,i].min())
        ls_min_cid.append(result_each_cycle.ix[:,i].idxmin()+1)
        ls_max_cid.append(result_each_cycle.ix[:,i].idxmax()+1)

    summary_label = cycles_label[1:]

    df_summary = pd.DataFrame.from_items([('mean', ls_mean), 
                                          ('min', ls_min),('min_cycle#', ls_min_cid), 
                                          ('max', ls_max), ('max_cycle#', ls_max_cid),
                                          ('std_dev', ls_std)], 
                                          orient='index', columns=summary_label)
    df_summary = df_summary.iloc[:, :14]
    df_summary = df_summary.round(2)
    result_each_cycle = result_each_cycle.round(2)
    result_each_cycle.set_index('cycle#', inplace=True)

    return result_each_cycle, df_summary


def all_same(items):
    return all(x == items[0] for x in items)


def df_keypoints(channel, df_chan_Ambient, upper_threshold, lower_threshold):
    lower = df_chan_Ambient[df_chan_Ambient[channel] < 0]
    upper = df_chan_Ambient[df_chan_Ambient[channel] >= 0]

    lower.insert(0,'diff_sweep_last',lower['Sweep_screen'] - lower['Sweep_screen'].shift(1)) 
    lower.insert(0,'diff_sweep_next',lower['Sweep_screen'].shift(-1) - lower['Sweep_screen']) 
    cycle_index_last = lower['diff_sweep_last'][lower['diff_sweep_last']>2].index.tolist()
    cycle_index_next = lower['diff_sweep_next'][lower['diff_sweep_next']>2].index.tolist()
    cycle_index = cycle_index_last + list(set(cycle_index_next) - set(cycle_index_last))
    cycle_index = sorted(cycle_index)

    ####Get all the key points
    if cycle_index[0] != lower.iloc[0].Sweep_screen: cycle_index.append(lower.iloc[0].Sweep_screen)
    if cycle_index[-1] != lower.iloc[lower.shape[0]-1].Sweep_screen: cycle_index.append(lower.iloc[lower.shape[0]-1].Sweep_screen)
    lower_key = lower.loc[cycle_index].sort_values(['Sweep_screen']).index.tolist()
    channel_period = []
    key_point = []
    n_reach_ls_period = []
    consecutive_points = []

    for i in range(len(lower_key)-1): 
        if df_chan_Ambient[channel].iloc[lower_key[i]] > 0 and df_chan_Ambient[channel].iloc[lower_key[i+1]] > 0:
            channel_period.append([lower_key[i], lower_key[i+1]])
        if df_chan_Ambient[channel].iloc[lower_key[i]] < 0 and df_chan_Ambient[channel].iloc[lower_key[i+1]] < 0:
            channel_period.append([lower_key[i], lower_key[i+1]])
    channel_period.append([lower_key[i+1], df_chan_Ambient.shape[0]-1])
    channel_period.insert(0,[1,channel_period[0][0]])
    if channel_period[0] == [1,1]: channel_period.remove([1,1])
    if channel_period[-1] == [df_chan_Ambient.shape[0]-1,df_chan_Ambient.shape[0]-1]: channel_period.remove([df_chan_Ambient.shape[0]-1,df_chan_Ambient.shape[0]-1])

    for i in range(len(channel_period)):
        if df_chan_Ambient[channel].iloc[channel_period[i][0]:channel_period[i][1]].mean() > 0:
            ls_period = df_chan_Ambient[channel].iloc[channel_period[i][0]:channel_period[i][1]+1][df_chan_Ambient[channel].iloc[channel_period[i][0]:channel_period[i][1]+1]>= upper_threshold].index.tolist()
        if df_chan_Ambient[channel].iloc[channel_period[i][0]:channel_period[i][1]].mean() < 0:
            ls_period = df_chan_Ambient[channel].iloc[channel_period[i][0]:channel_period[i][1]+1][df_chan_Ambient[channel].iloc[channel_period[i][0]:channel_period[i][1]+1]<= lower_threshold].index.tolist()
        
        ls_period = sorted(ls_period)
        if len(ls_period)<2 :
            key_point.append(0)
            key_point.append(0)
        else:
            consecutive_points = []
            for k, g in itertools.groupby(enumerate(ls_period), lambda x: x[1]-x[0] ) :
                consecutive_points.append(list(map(itemgetter(1), g)))
            consecutive_points.reverse()
            key_point.append(max(consecutive_points, key=len)[0])
            key_point.append(max(consecutive_points, key=len)[-1])

    if key_point[0] == 1: key_point.remove(1)
    if key_point[0] == 1: key_point.remove(1)
    if key_point[0] == 0: key_point.remove(0)
    if key_point[0] == 0: key_point.remove(0)
    #if key_point[-1] == df_chan_Ambient.shape[0]-1: del key_point[-1]

    ambient = df_chan_Ambient.iloc[key_point].reset_index(drop=True)

    return ambient, n_reach_ls_period


def drop_errors_channel(df, channel):
    ''' Get rid of outrage data and output error list '''
    #df_chan_orig[['Sweep #']] = df_chan_orig.index.values.tolist()
    df_chan_orig = df[['Sweep #', 'Time', channel]].reset_index(drop=True)
    df_chan_orig[['Sweep #']] = df_chan_orig.index.values.tolist()
    df_chan_selected = df[['Sweep #', 'Time', channel]].reset_index(drop=True)
    df_chan_selected[['Sweep #']] = df_chan_selected.index.values.tolist()

    df_chan_selected = df_chan_selected[df_chan_selected[channel] < 150]
    df_chan_selected = df_chan_selected[df_chan_selected[channel] > -150]

    errors = df_chan_orig[~df_chan_orig.index.isin(df_chan_selected.index.tolist())]

    return df_chan_selected, errors