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
import xlsxwriter

from core.tshock_helpers import *


def tshock_analyze_all_channels(df, channels, amb, tc_channel_names, upper_threshold, lower_threshold, 
                                tolerance, rate_adjustment, date_format, file_extension, test_name):
    report_summary = []
    writer = create_wb(test_name) ## create workbook
    print('inside tshock_analyze_all_channels...')
    ## analyze ambient
    amb_upper_threshold = upper_threshold - tolerance
    amb_lower_threshold = lower_threshold + tolerance

    df_ambient, errors_ambient = drop_errors_channel(df, amb)

    result_each_cycle_amb, df_summary_amb, ambient, content_instruction_ambient, cycle_amount = ambient_analysis(df_ambient, channels, amb, amb_upper_threshold, amb_lower_threshold, date_format)
    write_multiple_dfs(writer, [errors_ambient, df_summary_amb, result_each_cycle_amb], 'Amb '+str(amb), 3, content_instruction_ambient)

    report_summary_amb = df_summary_amb[['cold_soak_duration_minute', 'cold_soak_mean_temp_c', 
                                         'hot_soak_duration_minute', 'hot_soak_mean_temp_c', 
                                         'down_RAMP_rate_c/minute', 'up_RAMP_rate_c/minute']].iloc[:1]
    report_summary_amb.index = ['Amb']
    report_summary.append(report_summary_amb)

    ### all other channels
    if rate_adjustment:  ## apply rate adjustment if supplied
        temp_adjustment = rate_adjustment*(float(upper_threshold) - float(lower_threshold))/100
        upper_threshold = upper_threshold - temp_adjustment
        lower_threshold = lower_threshold + temp_adjustment

    else: ## otherwise use tolerance used for ambient
        upper_threshold = amb_upper_threshold
        lower_threshold = amb_lower_threshold

    for channel in channels:
        print(channel)
        if channel != amb:
            df_channel, errors_channel = drop_errors_channel(df, channel)
            result_each_cycle, df_summary_tc, n_reach_summary = pd.DataFrame(), pd.DataFrame(), pd.DataFrame() ## ensure reset
            result_each_cycle, df_summary_tc, content_instruction = single_channel_analysis(df_channel, channel, amb, ambient, upper_threshold, lower_threshold, date_format, cycle_amount)
            report_summary_tc = df_summary_tc[['cold_soak_duration_minute', 'cold_soak_mean_temp_c', 
                                               'hot_soak_duration_minute', 'hot_soak_mean_temp_c', 
                                               'down_RAMP_rate_c/minute', 'up_RAMP_rate_c/minute']].iloc[:1]

            print('Channel name/in names:', channel, channel in tc_channel_names, '\n')
            if tc_channel_names[channel]: 
                report_summary_tc.index = [tc_channel_names[channel]]
            else: 
                report_summary_tc.index = [channel]
            
            report_summary.append(report_summary_tc)

            if tc_channel_names[channel]:
                if file_extension == 'csv':
                    tc_name = tc_channel_names[channel] + ' (' + channel.split(' ')[1] + ')'
                else:
                    tc_name = tc_channel_names[channel]
            else:
                tc_name = channel

            if rate_adjustment:
                df_summary_tc = df_summary_tc[[ 'up_RAMP_temp_change_rate_max_temp_c', 'up_RAMP_temp_c', 'up_recovery_time_minute', 'up_RAMP_rate_c/minute', 
                                                'down_RAMP_temp_change_rate_min_temp_c', 'down_RAMP_temp_c', 'down_recovery_time_minute', 'down_RAMP_rate_c/minute' ]]
                result_each_cycle = result_each_cycle[[ 'up_RAMP_temp_change_rate_max_temp_c', 'up_RAMP_temp_c', 'up_recovery_time_minute', 'up_RAMP_rate_c/minute', 
                                                'down_RAMP_temp_change_rate_min_temp_c', 'down_RAMP_temp_c', 'down_recovery_time_minute', 'down_RAMP_rate_c/minute' ]]
            write_multiple_dfs(writer, [errors_channel, df_summary_tc, result_each_cycle], tc_name, 3, content_instruction)
    
    result = pd.concat(report_summary)
    result.to_excel(writer, sheet_name='Report Summary Table', startrow=2, startcol=0)
    worksheet = writer.sheets['Report Summary Table']

    ### format output excel file
    format_excel_file(writer)
    writer.save()


def format_excel_file(writer):
    workbook = writer.book
    table_format = workbook.add_format({'align':'center'})
    for sheet_name in writer.sheets:
        if sheet_name != 'Report Summary Table':
            writer.sheets[sheet_name].set_column('A:Z', 27, table_format)
        else: 
            merge_format = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': 'yellow'})
        
            cell_format = workbook.add_format()
            cell_format.set_bold()
            cell_format.set_align('center')
            cell_format.set_align('vcenter')

            worksheet = writer.sheets['Report Summary Table']
            worksheet.merge_range('A2:G2', 'Thermocouple Data Summary Table - Mean Values', merge_format)
            worksheet.write(2, 0, "Type", cell_format)
            writer.sheets[sheet_name].set_column('A:G', 27, table_format)


def ambient_analysis(df, channels, amb, upper_threshold, lower_threshold, date_format):
    ''' Analysis for ambient channel '''
    print('inside ambient_analysis...')

    df_chan_Ambient = df[['Sweep #', 'Time', amb]].reset_index(drop=True)
    df_nan = [{'Sweep #': np.nan, 'Time': np.nan, amb: np.nan}]
    df_chan_Ambient = pd.concat([pd.DataFrame(df_nan), df_chan_Ambient], ignore_index=True)
    sweep_screen = []
    for i in range(df_chan_Ambient.shape[0]):
        sweep_screen.append(i)
    df_chan_Ambient.insert(0,'Sweep_screen',pd.Series(sweep_screen, index=df_chan_Ambient.index).tolist())

    ambient, n_reach_ls_period = df_keypoints(amb, df_chan_Ambient, upper_threshold, lower_threshold)
    ambient = calculate_ramp_stats(amb, ambient, date_format)

    start_index_list = find_starting_point_case(amb, ambient, upper_threshold, lower_threshold)  

    down_i = start_index_list[0]
    up_i = start_index_list[1]
    cold_i = start_index_list[2]
    hot_i = start_index_list[3]

    ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = [], [], [], []
    for i in range(int(ambient.shape[0]/4)):
        ls_index_down.append(i*4 + down_i)
        ls_index_up.append(i*4 + up_i)
        ls_index_cold.append(i*4 + cold_i)
        ls_index_hot.append(i*4 + hot_i)

    df_chan_Ambient = df_chan_Ambient.iloc[1:]
    ### SOAK ANALYSIS
    df_soak_high, df_soak_low = soak_analysis(amb, amb, ambient, df_chan_Ambient, ls_index_cold, ls_index_hot, start_index_list)
    ### RAMP ANALYSIS
    df_transform_down, df_transform_up = ramp_analysis(ambient, df_chan_Ambient, ls_index_down, ls_index_up)
    ### Create summary
    result_each_cycle, df_summary = create_analysis_summary(amb, amb, df_soak_high, df_soak_low, df_transform_down, df_transform_up)
    cycle_amount = len(result_each_cycle)

    if n_reach_ls_period == []: 
        content_instruction = ['Version 6.0\n\nIn this TSHOCK test file, there are '+ str(cycle_amount) +' cycles.\n\nThe First Table: List out the test data that have reading error.', 'The Second Table: Summary table for the ambient.', 'The Third Table: List out the calculation result for each cycle of ambient.']
    else: 
        content_instruction = ['Version 6.0\n\nIn this TSHOCK test file, there are '+ str(cycle_amount) +' cycles.\n\nThe First Table: List out the test data that have reading error.', 'The Second Table: Summary table for the ambient.\n\nNot every cycle reached the threshold!', 'The Third Table: List out the calculation result for each cycle of ambient.']

    return result_each_cycle, df_summary, ambient, content_instruction, cycle_amount


def single_channel_analysis(df, channel, amb, ambient, upper_threshold, lower_threshold, date_format, cycle_amount):
    ''' Analysis for non-ambient channels '''
    df_summary = pd.DataFrame()
    n_reach_summary = pd.DataFrame()
    n_reach = pd.DataFrame()
    ####Test for one channel
    df_chan = df[['Sweep #', 'Time']+[channel]].reset_index(drop=True)
    df_nan = [{'Sweep #': np.nan, 'Time': np.nan, channel: np.nan}]
    df_chan = pd.concat([pd.DataFrame(df_nan), df_chan], ignore_index=True)
    sweep_screen = []
    for i in range(df_chan.shape[0]):
        sweep_screen.append(i)
    df_chan.insert(0, 'Sweep_screen', pd.Series(sweep_screen, index=df_chan.index).tolist())

    selected_channel, n_reach_ls_period = df_keypoints(channel, df_chan, upper_threshold, lower_threshold)
    #### Cycle Statistics #####
    selected_channel = calculate_ramp_stats(channel, selected_channel, date_format)

    start_index_list = find_starting_point_case(channel, selected_channel, upper_threshold, lower_threshold)  

    down_i = start_index_list[0]
    up_i = start_index_list[1]
    cold_i = start_index_list[2]
    hot_i = start_index_list[3]

    ls_index_down, ls_index_up, ls_index_cold, ls_index_hot = [], [], [], []
    for i in range(int(ambient.shape[0]/4)):
        ls_index_down.append(i*4 + down_i)
        ls_index_up.append(i*4 + up_i)
        ls_index_cold.append(i*4 + cold_i)
        ls_index_hot.append(i*4 + hot_i)
        
    df_chan = df_chan.iloc[1:]

    ### SOAK ANALYSIS
    df_soak_high, df_soak_low = soak_analysis(channel, amb, selected_channel, df_chan, ls_index_cold, ls_index_hot, start_index_list)   

    ### RAMP ANALYSIS
    df_transform_down, df_transform_up = ramp_analysis(selected_channel, df_chan, ls_index_down, ls_index_up)

    ### Create summary
    result_each_cycle, df_summary = create_analysis_summary(amb, amb, df_soak_high, df_soak_low, df_transform_down, df_transform_up)
    if n_reach_ls_period == []: 
        content_instruction = ['The First Table: List out the reading errors.', 
                               'The Second Table: List out the summary table.', 
                               'The Third Table: Calculate result for cycle of this channel.']
    else:
        content_instruction = ['The First Table: List out the reading errors.', 
                               'The Second Table: List out the summary table.', 
                               'The Third Table: Calculate result for cycle of this channel.']

    return result_each_cycle, df_summary, content_instruction
