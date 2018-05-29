#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from core.analysis import *
import pandas as pd
import numpy as np
import xlrd
import math

TEXTFIELD_WIDTH = 3

class ProfileUI(QWidget):

    def __init__(self):
        super().__init__()
        self.data_file = ''
        self.channels = []
        self.tc_names = []
        self.stylesheet = 'styles\dark.qss'
        self.width = 500
        self.height = 200
        self.init_ui()

    def init_ui(self):
        ## use self.grid layout for GUI
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.setSpacing(10)  # spacing between widgets

        ## data folder
        self.data_file_textfield_1 = QLineEdit('(No File Selected)', self)
        self.data_file_button_1 = FileButton('Select Manual Data File', self.data_file_textfield_1, self)
        self.grid.addWidget(self.data_file_button_1, 0, 0)
        self.grid.addWidget(self.data_file_textfield_1, 0, 1, 1, TEXTFIELD_WIDTH)

        self.data_file_textfield_2 = QLineEdit('(No File Selected)', self)
        self.data_file_button_2 = FileButton('Select Program Data File', self.data_file_textfield_2, self)
        self.grid.addWidget(self.data_file_button_2, 1, 0)
        self.grid.addWidget(self.data_file_textfield_2, 1, 1, 1, TEXTFIELD_WIDTH)

        ## test name
        self.test_name_label = QLabel('Output File Name:', self)
        self.test_name_label.setFont(QFont("Times", weight=QFont.Bold))
        self.test_name_textfield = QLineEdit(self)
        self.grid.addWidget(self.test_name_label, 2, 0)
        self.grid.addWidget(self.test_name_textfield, 2, 1, 1, 1)

        ## How many sheets
        self.sheets_number = QLabel('The amount of ThermoCouples:', self)
        self.sheets_number.setFont(QFont("Times", weight=QFont.Bold))
        self.sheets_number_textfield = QLineEdit(self)
        self.grid.addWidget(self.sheets_number, 3, 0)
        self.grid.addWidget(self.sheets_number_textfield, 3, 1, 1, 1)

        ## Analyze Button
        self.analyze_button = AnalyzeButton('Analyze!', self)
        self.grid.addWidget(self.analyze_button, 4, 0, 1, 4)

        ## gui window properties
        self.setStyleSheet(open(self.stylesheet, "r").read())
        self.setWindowTitle('Excel Compare')
        self.resize(self.width, self.height)
        self.move(300, 150) # center window
        self.show()

    

class AnalyzeButton(QPushButton):

    def __init__(self, name, ui):
        super().__init__()
        self.init_button(name)
        self.ui = ui

    def init_button(self, name):
        self.setText(name)
        self.name = name
        self.clicked[bool].connect(self.analyze)



    def analyze(self):
        ## Get user inputs
        test_name = self.ui.test_name_textfield.text()
        datapath_1 = self.ui.data_file_textfield_1.text()
        datapath_2 = self.ui.data_file_textfield_2.text()
        sheets_number = self.ui.sheets_number_textfield.text()

        sheetname = list(range(int(sheets_number)))
        
        df1 = pd.read_excel(datapath_1, sheetname = sheetname)
        df2 = pd.read_excel(datapath_2, sheetname = sheetname)
        df1_ls = clean_df_ls(df1, 'Manual')
        df2_ls = clean_df_ls(df2, 'Program')

        GetSheetName = xlrd.open_workbook(datapath_1)
        SheetLabel = GetSheetName.sheet_names()

        difference = compare(df1_ls, df2_ls)
        content_instruction = ["Manual", "Program", "Compare"]

        writer = create_wb(test_name)
        for i in range(len(difference)):
            write_multiple_dfs(writer, [difference[i], df1_ls[i], df2_ls[i]], SheetLabel[i], 4, content_instruction)
        info_df = pd.DataFrame({'Info Sheet': ['Version 6.0', datapath_1, datapath_2]})
        info_df = info_df.rename({0: 'Program Version' , 1: 'Manual datapath', 2: 'Program datapath'})
        info_df.to_excel(writer, sheet_name='Version Info')

        format_excel_file(writer)
        writer.save()

class FileButton(QPushButton):

    def __init__(self, text, text_box, ui):
        super().__init__()
        self.ui = ui
        self.setText(text)
        self.text_box = text_box
        self.name = ''
        self.clicked.connect(self.select_file)

    def select_file(self):
        self.name = str(QFileDialog.getOpenFileName(self, "Select temperature data file")[0])
        self.text_box.setText(self.name)
        self.ui.data_file = self.name
     


if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    gui = ProfileUI()
    sys.exit(app.exec_())