#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import pandas as pd
import numpy as np
import xlrd
import math


def compare(df1, df2):
    compare = []
    for i in range(len(df1)):
        difference_sheet = df1[i]-df2[i][df1[i]!=df2[i]]
        difference_sheet = difference_sheet.round(2)
        diff_copy = difference_sheet.copy()
        diff_copy.index.rename('Compare', inplace = True)
        #import pdb; pdb.set_trace()
        diff_copy[(-0.02<diff_copy) & (diff_copy<0.02)] = np.nan
        compare.append(diff_copy)
    return compare

def reset_excel(df):
    df = df.tail(21).set_index('Unnamed: 0')
    df = df[pd.notnull(df.index)]   
    df.columns = ['cold_soak_duration_minute', 'cold_soak_mean_temp_c', 'cold_soak_max_temp_c', 'cold_soak_min_temp_c', 'hot_soak_duration_minute', 'hot_soak_mean_temp_c', 'hot_soak_max_temp_c', 'hot_soak_min_temp_c', 'down_recovery_time_minute', 'down_RAMP_temp_c', 'down_RAMP_rate_c/minute', 'up_recovery_time_minute', 'up_RAMP_temp_c', 'up_RAMP_rate_c/minute']
    df = df.drop(df.index[6])
    return df


def clean_df_ls(df_OrderedDict, name):
    summary_df = []
    for i in range(len(df_OrderedDict)):
        print(i)
        df_OrderedDict[i] = reset_excel(df_OrderedDict[i])
        df_OrderedDict[i].index.rename(name, inplace = True)
        summary_df.append(df_OrderedDict[i])
    return summary_df

def create_wb(test_name):
    writer = pd.ExcelWriter(str(test_name)+'-output.xlsx', engine = 'xlsxwriter')
    return writer    

def write_multiple_dfs(writer, df_list, worksheet_name, spaces, content_instruction):
    row = 0
    for x in list(range(len(df_list))):
        df_list[x].to_excel(writer, sheet_name=worksheet_name, startrow=row , startcol=0)   
        worksheet = writer.sheets[worksheet_name]
        workbook = writer.book
        border_format=workbook.add_format({
                            'border':1,
                            'align':'center'
                           })
        worksheet.conditional_format( 'A1:O12' , { 'type' : 'no_blanks' , 'format' : border_format} )
        row = row - 2
        row = row + len(df_list[x].index) + spaces +1

def format_excel_file(writer):
    workbook = writer.book
    table_format = workbook.add_format({'align':'center'})
    for sheet_name in writer.sheets:
        if sheet_name != 'Version Info':
            writer.sheets[sheet_name].set_column('A:Z', 27, table_format)
        else:
            writer.sheets[sheet_name].set_column('A:B', 27) 