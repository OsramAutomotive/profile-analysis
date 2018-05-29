# Temperature Analysis Profile 

This program analyzes the temperature of raw environmental test data for automotive lighting systems. The tests expose lighting systems to various temperature profiles while the systems are powered. The primary function of this project is to detect if the changing of temperature of each sample and the ambient is as consistent and regular as the particular and regular changed temperature condition.

## Input Raw Data Sample
**1. Thermal Shock data (CSV.)**

```
| Sweep #  | Time                    | Chan 101 (C) | Chan 102(C) | Chan 103(C) | Chan 104(C) | Chan 105(C) | Chan 106(C) | Chan 107(C) | Chan 108(C) | Chan 109(C) | Chan 110(C) | Chan 111 (C) | Chan 112 (C) |
|----------|-------------------------|--------------|-------------|-------------|-------------|-------------|-------------|-------------|-------------|-------------|-------------|------------- |--------------|
|        1 | 02/02/2000 23:44:40:402 | -39.67       | -36.883     | -39.157     | -38.98      | -38.569     | -38         | -38.641     | -38.856     | -39.221     | -38.58      | -38.601      | -39.235      |
|        2 | 02/02/2000 23:44:50:400 | 0.71         | -21.093     | -20.878     | -19.067     | -30.03      | -23.05      | -7.155      | 4.015       | -5.027      | -19.617     | -0.937       | -32.58       |
|        3 | 02/02/2000 23:45:00:392 | 41.508       | -9.481      | -5.9        | -1.346      | -19.172     | -6.093      | -11.602     | 32.437      | 19.626      | -2.157      | 34.374       | -22.409      |
|        4 | 02/02/2000 23:45:10:388 | 62.637       | -1.898      | 6.5         | 12.534      | -9.154      | 8.154       | 24.148      | 50.898      | 37.156      | 13.323      | 58.978       | -11.983      |
|        5 | 02/02/2000 23:45:20:392 | 75.47        | 5.009       | 18.254      | 24.162      | 0.197       | 20.523      | 34.437      | 66.14       | 51.606      | 27.723      | 76.651       | -2.815       |
|        6 | 02/02/2000 23:45:30:387 | 81.49        | 10.233      | 26.757      | 32.854      | 8.107       | 30.106      | 40.208      | 75.387      | 61.888      | 38.971      | 82.712       | 5.639        |
|        7 | 02/02/2000 23:45:40:430 | 85.288       | 14.787      | 35.487      | 40.491      | 15.559      | 38.178      | 46.548      | 83.573      | 70.482      | 49.097      | 93.826       | 13.806       |
|        8 | 02/02/2000 23:45:50:422 | 88.046       | 18.896      | 42.555      | 47.717      | 22.248      | 44.708      | 51.972      | 90.076      | 77.227      | 57.661      | 98.748       | 21.745       |

(and so on ...)

```

**2. PTC data (CSV. or TXT.)**

```
| Date     | Time       | Amb Temp TC1 | TC2    | TC3    | TC4    | VSetpoint | VSense 1 | VSense 2 | Board on/off | TP1: System 82 | TP2: System 83 | TP3: System 84 | TP4: System 85 | TP5: System 86 | TP6: System 87 | TP7: System 88 | TP8: System 89 | TP9: System 90 | TP10: System 91 | TP11: System 92 | TP12: System 93 |
|----------|------------|--------------|--------|--------|--------|-----------|----------|----------|--------------|----------------|----------------|----------------|----------------|----------------|----------------|----------------|----------------|----------------|-----------------|-----------------|-----------------|
| 2/2/2017 | 4:29:32 PM | 22.955       | 23.367 | 22.785 | 22.281 | 9         | 9.009    | 9.118    | 1            | 0.49788        | 0.49691        | 0.49941        | 0.48962        | 0.4949         | 0.49386        | 0.49448        | 0.49518        | 0.49372        | 0.49802         | 0.49865         | 0.48726         |
| 2/2/2017 | 4:29:33 PM | 22.943       | 23.364 | 22.764 | 22.266 | 9         | 9.012    | 9.019    | 1            | 0.49851        | 0.49754        | 0.50004        | 0.49011        | 0.49566        | 0.49441        | 0.4949         | 0.49587        | 0.49441        | 0.49851         | 0.49927         | 0.48775         |
| 2/2/2017 | 4:29:34 PM | 22.949       | 23.37  | 22.785 | 22.284 | 9         | 9.023    | 9.071    | 1            | 0.49879        | 0.49761        | 0.50011        | 0.49018        | 0.49573        | 0.49462        | 0.49511        | 0.49615        | 0.49455        | 0.49872         | 0.49927         | 0.48775         |
| 2/2/2017 | 4:29:35 PM | 22.943       | 23.391 | 22.776 | 22.272 | 9         | 9.015    | 9.122    | 1            | 0.49886        | 0.49775        | 0.50025        | 0.49025        | 0.49594        | 0.49469        | 0.49525        | 0.49608        | 0.49469        | 0.49879         | 0.4992          | 0.48789         |
| 2/2/2017 | 4:29:41 PM | 22.949       | 23.431 | 22.782 | 22.639 | 9         | 0.003    | 0.003    | 0            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF             | OFF             | OFF             |
| 2/2/2017 | 4:29:42 PM | 22.965       | 23.456 | 22.764 | 22.629 | 9         | 0.003    | 0.003    | 0            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF             | OFF             | OFF             |
| 2/2/2017 | 4:29:43 PM | 22.961       | 23.45  | 22.767 | 22.595 | 9         | 0.003    | 0.003    | 0            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF             | OFF             | OFF             |
| 2/2/2017 | 4:29:44 PM | 22.968       | 23.465 | 22.785 | 22.614 | 9         | 0.003    | 0.003    | 0            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF            | OFF             | OFF             | OFF             |

(and so on ...)

```

## Current Limits

This program can only analyze the cycles that can reach the threshold, but will leave those cycles cannot reach as blank. 

## Core Functions

**1. Temporal Plotting**

**2. Summary Tables with basic statistics**
* List out outrage data
* Statistic summary of all the cycles
* List out all the calculate result of each cycle: (the attributes listed as below)
   * Cold_soak_duration_minute
   * Cold_soak_mean_temp_c
   * Cold_soak_max_temp_c
   * Cold_soak_min_temp_c
   * Hot_soak_duration_minute
   * Hot_soak_mean_temp_c
   * Hot_soak_max_temp_c
   * Hot_soak_min_temp_c
   * Down_recovery_time_minute
   * Down_RAMP_temp_c
   * Down_RAMP_rate_c/minute
   * Up_recovery_time_minute
   * Up_RAMP_temp_c
   * Up_RAMP_rate_c/minute

### Introduction
**1. Gui**

![Gui UI](/images/tshock_gui.PNG)

   * In this interface, user give the input of this program.
   * Choose the raw testdata file and the type of this test.
   * Give a name or discription to this datafile over Test Name box.
   * Input the Upper & Lower Threshold, and Temperate Tolerance.
   * Input Component rate adjustment if it exists.
   

![Gui UI_2](/images/tshock_gui_2.PNG)

   * In this interface, this program can detect there are how many channels in this test.
   * User can label out which channel is the Ambient.
   * Give a brief discription for each channel or leave it blank.
   * All of these brief label will show in the tab of output excel file.
   
**2. Analyze! (Click "Analyze!" Button)**

![Analyze](/images/notification.PNG)

   * In this interface, the notification can show the progress of analysis, and also can show how the channel start.
   
**3. Plotting**

![general_graph](/images/general_plot.PNG)

   * This is the general plot of raw testdata.
   * The X axis is the time scale and index.
   * The Y axis is the temperature(C) over that scan.
   * This graph can show only selected channels, and also can zoom in and out.
   
![selected_graph](/images/scale_in_graph.PNG)

![selected_graph](/images/ambient_graph.PNG)

**4. Output Excel**

![selected_graph](/images/output.PNG)

   * Each tab of the output excel represent one channel.
   * Each sheet is consisted with 3 tables as this instruction mentioned above.
   
**5. Independency**

* [Python3](https://www.python.org/)
* [Pandas](http://pandas.pydata.org/) - Data wrangling and processing
* [Matplotlib](https://plot.ly/python/) - Plotting and histograms
* [XlsWriter](http://xlsxwriter.readthedocs.io/) - Creates analysis tables
* [PyQt5](https://pypi.python.org/pypi/PyQt5) - GUI

## Authors

* Siyu Chen
* Sam Bruno
