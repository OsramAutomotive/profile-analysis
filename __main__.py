#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import matplotlib.pyplot as plt

from core.tshock_analysis import *
from core.ptc_analysis import *
from core.data_import import *


TEXTFIELD_WIDTH = 3

## widget row placement
TEST_TYPE_ROW = 0
DATAPATH_ROW = 1
TEST_NAME_ROW = 2
UPPER_TEMP_ROW = 3
LOWER_TEMP_ROW = 4
TOL_ROW = 5
RT_ADJ_ROW = 6
LOAD_TC_ROW = 7
TC_LABELS_ROW = 8


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

        ## radio buttons (PTC or Thermal Shock)
        self.ptc_radio = QRadioButton('Test Station', self)
        self.tshock_radio = QRadioButton('34972A Data Logger', self)
        self.grid.addWidget(self.ptc_radio, TEST_TYPE_ROW, 0)
        self.grid.addWidget(self.tshock_radio, TEST_TYPE_ROW, 1)

        ## data folder
        self.data_folder_textfield = QLineEdit('(No Folder Selected)', self)
        self.data_folder_button = FolderButton('Select Data Folder', self.data_folder_textfield, self)
        self.grid.addWidget(self.data_folder_button, DATAPATH_ROW, 0)
        self.grid.addWidget(self.data_folder_textfield, DATAPATH_ROW, 1, 1, TEXTFIELD_WIDTH)

        ## test name
        self.test_name_label = QLabel('Test Name:', self)
        self.test_name_label.setFont(QFont("Times", weight=QFont.Bold))
        self.test_name_textfield = QLineEdit(self)
        self.grid.addWidget(self.test_name_label, TEST_NAME_ROW, 0)
        self.grid.addWidget(self.test_name_textfield, TEST_NAME_ROW, 1, 1, 1)

        ## upper temperature threshold
        self.upper_temp_label = QLabel('Upper Threshold (\N{DEGREE SIGN}C):', self)
        self.upper_temp_label.setFont(QFont("Times",weight=QFont.Bold))
        self.upper_temp_textfield = QLineEdit(self)
        self.grid.addWidget(self.upper_temp_label, UPPER_TEMP_ROW, 0)
        self.grid.addWidget(self.upper_temp_textfield, UPPER_TEMP_ROW, 1, 1, 1)

        ## lower temperature threshold
        self.lower_temp_label = QLabel('Lower Threshold (\N{DEGREE SIGN}C):', self)
        self.lower_temp_label.setFont(QFont("Times",weight=QFont.Bold))
        self.lower_temp_textfield = QLineEdit(self)
        self.grid.addWidget(self.lower_temp_label, LOWER_TEMP_ROW, 0)
        self.grid.addWidget(self.lower_temp_textfield, LOWER_TEMP_ROW, 1, 1, 1)

        ## temperature tolerance
        self.temp_tol_label = QLabel('Temperature Tolerance (\N{DEGREE SIGN}C):', self)
        self.temp_tol_textfield = QLineEdit(self)
        self.grid.addWidget(self.temp_tol_label, TOL_ROW, 0)
        self.grid.addWidget(self.temp_tol_textfield, TOL_ROW, 1, 1, 1)

        ## threshold component rate adjustment
        self.adjustment_label = QLabel('Component rate adjustment (%):', self)
        self.adjustment_textfield = QLineEdit(self)
        self.grid.addWidget(self.adjustment_label, RT_ADJ_ROW, 0)
        self.grid.addWidget(self.adjustment_textfield, RT_ADJ_ROW, 1, 1, 1)

        ## load tc button
        self.load_tc_button = QPushButton('Load TCs...', self)
        self.grid.addWidget(self.load_tc_button, LOAD_TC_ROW, 0, 1, 4)
        self.load_tc_button.clicked.connect(lambda: self.populate_tc_field_group(TC_LABELS_ROW))
        
        ## gui window properties
        self.setStyleSheet(open(self.stylesheet, "r").read())
        self.setWindowTitle('Temperature Profile Analysis')
        self.setWindowIcon(QIcon('images\sine.png'))
        self.resize(self.width, self.height)
        self.move(300, 150) # center window
        self.show()

    def populate_tc_field_group(self, row):
        ''' Populate GUI with user input TC analysis widgets '''
        datapath = self.data_folder_textfield.text()
        if datapath and datapath != '(No Folder Selected)': ## if datapath provided
            try:
                self.retrieve_thermocouple_channels()

                ## ambient temp channel field
                self.amb_chan_label = QLabel('Amb Temp Channel:', self)
                self.amb_chan_textfield = QLineEdit(self)
                self.grid.addWidget(self.amb_chan_label, row, 0)
                self.grid.addWidget(self.amb_chan_textfield, row, 1, 1, 1)
                row += 1

                ## thermocouple fields
                for i, channel in enumerate(self.channels):
                    self.add_tc_field(i, channel, row)
                    row += 1

                ## analyze button
                self.analyze_button = AnalyzeButton('Analyze!', self)
                self.grid.addWidget(self.analyze_button, row, 0, 1, 4)

            except OSError as e: ## no datapath selected
                print('\n', e)
                print('Data load error -- Make sure you have selected a valid data file')
        else:
            print('\n', 'Error: path to data file must be provided to load TCs')

    def retrieve_thermocouple_channels(self):
        if ( self.data_folder_textfield.text() ):
            datapath = self.data_folder_textfield.text()
            head_ls_file = os.listdir(datapath)
            filepath = head_ls_file[0]
            regex_temp, date_format, sep, file_extension = define_test_parameters(filepath)
            head_ls_file = os.listdir(datapath)
            df_temp = pd.read_csv(datapath + '\\' + head_ls_file[0], nrows=5, sep=sep)  ## read first 5 rows of datafile
            self.channels = get_channels(df_temp, regex_temp)
        else:
            print('You must define a valid datapath first')

    def add_tc_field(self, i, channel, row):
        ''' Adds a single TC widget pair to the GUI '''
        label = QLabel(channel+':', self)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        field = QLineEdit(self)
        if i+1 <= 10:
            use_row = row
            column = 0
        else:
            use_row = row-10
            column = 2
        self.grid.addWidget(label, use_row, column)
        self.grid.addWidget(field, use_row, column+1)
        self.tc_names.append(field)


class FolderButton(QPushButton):
    def __init__(self, text, text_box, ui):
        super().__init__()
        self.ui = ui
        self.setText(text)
        self.text_box = text_box
        self.name = r''
        self.clicked.connect(self.set_folder)
        self.setToolTip('Select the directory containing the raw data of the test you would like to analyze')

    def set_folder(self):
        self.name = str(QFileDialog.getExistingDirectory(self, "Select directory for data analysis"))
        self.text_box.setText(self.name)
        self.ui.data_folder = self.name
     

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
        test_type = get_test_type(self.ui.ptc_radio, self.ui.tshock_radio)
        test_name = self.ui.test_name_textfield.text()
        datapath = self.ui.data_folder_textfield.text()
        tolerance = self.ui.temp_tol_textfield.text()
        upper_threshold = self.ui.upper_temp_textfield.text()
        lower_threshold = self.ui.lower_temp_textfield.text()
        ambient_channel_number = self.ui.amb_chan_textfield.text()
        rate_adjustment = self.ui.adjustment_textfield.text()
        title = 'Temperature Profile Analysis'

        if rate_adjustment:
            rate_adjustment = float(self.ui.adjustment_textfield.text())

        ## Load TC component/location name labels
        tc_channel_names = {}  ## key: channel, value: tc_name
        for i, channel in enumerate(self.ui.channels):
            tc_channel_names[channel] = self.ui.tc_names[i].text()

        ## if all required user inputs exist
        if test_name and test_type and datapath and upper_threshold and lower_threshold and tolerance:
            upper_threshold, lower_threshold = int(upper_threshold), int(lower_threshold)
            tolerance = int(tolerance)
            head_ls_file = os.listdir(datapath)
            filepath = head_ls_file[0]
            regex_temp, date_format, sep, file_extension= define_test_parameters(filepath)

            ### Print test parameters
            print('Test Type:', test_type)
            print('Datapath:', datapath)
            print('Upper Threshold:', upper_threshold)
            print('Lower Threshold:', lower_threshold)
            print('Channels:', tc_channel_names)
            print('Amb Channel:', ambient_channel_number)

            ls_df_all = build_dataframe(datapath) 
            df = pd.concat(ls_df_all)

            ## Do plot
            df_plot, channels, amb = import_data_with_date_index(datapath, ambient_channel_number, regex_temp, date_format, sep, file_extension)  ## df time indexed
            try:
                plot_profile_matplotlib(upper_threshold, lower_threshold, tolerance, rate_adjustment, 
                                        title, df_plot, channels, tc_channel_names, regex_temp)
            except Exception as e:
                print('There was an error with the Plotting')
                print(e)

            ## Do analysis
            channels, amb = import_data_without_date_index(df, ambient_channel_number, regex_temp, sep) ## df raw for analysis
            if test_type == 'Thermal Shock': 
                tshock_analyze_all_channels(df, channels, amb, tc_channel_names, 
                                            upper_threshold, lower_threshold, tolerance, rate_adjustment, 
                                            date_format, file_extension, test_name)
            elif test_type == 'PTC':
                ptc_analyze_all_channels(df, channels, amb, tc_channel_names, 
                                         upper_threshold, lower_threshold, tolerance, rate_adjustment, 
                                         date_format, file_extension, test_name)
            plt.show()
            print('\nANALYSIS COMPLETE.')
        else:
            print('\n', 'All user inputs must be filled before analysis can be conducted. Please fill in the required fields.')
        

### Helpers
def get_test_type(ptc_widget, tshock_widget):
    if ptc_widget.isChecked():
        test_type = 'PTC'
    elif tshock_widget.isChecked():
        test_type = 'Thermal Shock'
    else:
        test_type = None
    return test_type


if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    gui = ProfileUI()
    sys.exit(app.exec_())
