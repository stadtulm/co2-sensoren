#Organization:  TH Ulm
#               Prittwitzstraße 10
#               89075 Ulm
#
#Project:       Zukunftsstadt - LoRa CO2 Evaluation
#Date:          01.10.2021
#Author:        Petrick, Louis
#               louis.petrick@thu.de

import argparse
import matplotlib.pyplot as plt
import InfluxDB_Query
from datetime import datetime
#import numpy as np
#from scipy.interpolate import make_interp_spline

#Constants to set for data evaluation
LECTURE_START   = 7       #Uhr
LECTURE_END     = 16        #Uhr
LIMIT_EXCEED    = 1000     #ppm
LIMIT_CRITICAL  = 750    #ppm

#File to extract LoRa device ids from
ID_FILE = 'CO2_Device_IDs.txt'

#----------------------------------------------------------------------------------------------------------------------------------------
#processes the raw data from influxdb to visualize it on a map
def processData_co2(jsonData):
    co2 = []
    temp = []
    timestamp = []
    date_arr = []
    time_arr = []
    old_timestamp = ""

    try:
        datasets = jsonData['series'][0]['values']
    except Exception as e:
        print(e)
        print(">>>ERROR<<< It seems like there is no data available in the given time range. Check .json file for more information on the dataset!")
        print("> Aborting script...")
        return -1

    for dataset in datasets:
        current_timestamp = str(dataset[0]).split('.')[0]
        if((dataset[1] != 0 or dataset[2] != 0) and old_timestamp != current_timestamp):       #check if last timestamp is identical to the current one. It seems like influxdb sometimes returns duplicates of the timestamps next to each other
            timestamp.append(dataset[0])
            old_timestamp = str(timestamp[-1]).split('.')[0]
            co2.append(dataset[1])
            temp.append(dataset[2])

    #split up timestamp in its elements
    for string in timestamp:
        date = string.split('T')[0]
        time = (string.split('T')[1]).split('.')[0]
        time = time.replace('Z', '')

        date_arr.append(date)
        time_arr.append(time)

    print(f"\n> Found {len(datasets)} datasets. {len(timestamp)}/{len(datasets)} are valid!")
 
    return (date_arr, time_arr, co2, temp)

#----------------------------------------------------------------------------------------------------------------------------------------
def plot_calc_graphs(id, time_arr, date_arr, y_axis_co2):
    colorList = []
    y_axis_diff = []    #discrete slope
    x_axis_mins = []
    x_axis_mins.append(0)

    #Check if datasets exceed the defined limits and color the datapoints of the scatter plot
    for idx, value in enumerate(y_axis_co2): 
        hh = int(time_arr[idx].split(':')[0])

        if value >= LIMIT_EXCEED: 
            if (hh > LECTURE_START and hh < LECTURE_END): colorList.append('red')
            else: colorList.append('grey')

        elif (value < LIMIT_EXCEED and value >= LIMIT_CRITICAL):
            if (hh > LECTURE_START and hh < LECTURE_END): colorList.append('orange')
            else: colorList.append('grey')

        else: colorList.append('grey')

    for idx in range(len(y_axis_co2)):
        if (idx < len(y_axis_co2) - 1): 

            #Format time strings to allow calculations 
            x1 = datetime.strptime(date_arr[idx] + " " + time_arr[idx], "%Y-%m-%d %H:%M:%S")
            x2 = datetime.strptime(date_arr[idx + 1] + " " + time_arr[idx + 1], "%Y-%m-%d %H:%M:%S")

            #Prepare values for the calculation of the difference quotient:
            #calculate time delta between two adjacent datapoints
            delta_x = str(x2 - x1).split(':')

            y1 = y_axis_co2[idx]
            y2 = y_axis_co2[idx + 1]
            
            #If the time delta is -1 day, assume that this is due the string format when substracting around midnight --> discard "-1 day" and keep time information
            if (delta_x[0].find("-1 day") != -1):
                delta_x[0] = delta_x[0].split(', ')[1]

            #check if the time delta is greater than 1 day: delta_x[0] contains [x days, y], where x is days, y hours. Extraxt x, y and continue
            if (delta_x[0].find(", ") != -1):
                temp = delta_x[0].split(', ')
                days = temp[0].split(" ")[0]
                hours = temp[1]
                
            else:
                days = 0
                hours = delta_x[0]

            delta_x.insert(0, days)
            delta_x[1] = hours

            #calculate time delta in seconds
            delta_hour = int(delta_x[1]) * 60 * 60 + 24 * int(delta_x[0])
            delta_minute = int(delta_x[2]) * 60
            delta_sec = int(delta_x[3])
            added_delta_x_sec = delta_hour + delta_minute + delta_sec

            x_axis_mins.append(x_axis_mins[-1] + (added_delta_x_sec / 60))
            
            #calculate forward difference quotient
            diff_quot = (y2 - y1) / (added_delta_x_sec / 60)
            y_axis_diff.append(diff_quot)

    #Plot the data:
    #discrete values
    fig, (ax1, ax2) = plt.subplots(2)
    ax1.scatter(x_axis_mins, y_axis_co2, marker = 'o', c = colorList, s = 10)
    ax1.plot(x_axis_mins, y_axis_co2, linewidth=0.4)
    ax1.set_title(f"Auswertung CO2 Messwerte - {id}")
    ax1.set_xlabel("Minuten")
    ax1.set_ylabel("CO2 [ppm]")
    ax1.grid(axis = 'y')
    ax1.legend(["Diskret - Zeitlicher Verlauf CO2 Konzentreation"])

    x_axis_mins.pop()

    #discrete rate
    ax2.scatter(x_axis_mins, y_axis_diff, marker = 'o', s = 10, c = 'grey')
    ax2.plot(x_axis_mins, y_axis_diff, c = 'orange', linewidth=0.4)
    ax2.set_xlabel("Minuten")
    ax2.set_ylabel("CO2 [ppm]")
    ax2.grid(axis = 'y')
    ax2.legend(["Diskret - Vorwärts Differenzierter zeitl. Verlauf"])
    plt.get_current_fig_manager().window.state('zoomed')    

#----------------------------------------------------------------------------------------------------------------------------------------
def plot_calc_percentage(id, time_arr, co2):
    lecture_exceed_co2 = 0
    lecture_critical_co2 = 0
    lecture_non_critical_co2 = 0

    allday_exceed_co2 = 0
    allday_critical_co2 = 0
    allday_non_critical_co2 = 0

    #Check if datapoints exceed the defined limits to create the pie charts
    for idx, value in enumerate(co2): 
        hh = int(time_arr[idx].split(':')[0])

        if (value < LIMIT_EXCEED and value >= LIMIT_CRITICAL):
            allday_critical_co2 += 1
            if (hh > LECTURE_START and hh < LECTURE_END): lecture_critical_co2 += 1
        elif value >= LIMIT_EXCEED: 
            allday_exceed_co2 += 1
            if (hh > LECTURE_START and hh < LECTURE_END): lecture_exceed_co2 += 1
        else:
            allday_non_critical_co2 += 1
            if (hh > LECTURE_START and hh < LECTURE_END): lecture_non_critical_co2 += 1

    allday_total = allday_exceed_co2 + allday_non_critical_co2 + allday_critical_co2
    lecture_total = lecture_exceed_co2 + lecture_non_critical_co2 + lecture_critical_co2

    if allday_exceed_co2 > 0 or allday_critical_co2 > 0:
        #Log result to console
        print(f"> 0h00 - 24h00: {allday_exceed_co2}/{allday_total} = {round(float(allday_exceed_co2 / allday_total * 100 ), 2)}% of the given datapoints exceed the limit of 1000ppm")
        print(f"> 0h00 - 24h00: {allday_critical_co2}/{allday_total} = {round(float(allday_critical_co2 / allday_total * 100 ), 2)}% of the given datapoints exceed the limit of 750ppm")
        
        #plot pie chart
        fig2 = plt.figure()
        ax2 = fig2.add_subplot(111)
        pie2 = ax2.pie([allday_exceed_co2, allday_critical_co2, allday_non_critical_co2], explode = [0.1, 0.05, 0], labels = [">= 1000ppm", ">= 750ppm", "< 750 ppm"], startangle = 90, counterclock = False, autopct = '%1.1f%%', colors = ['pink', 'yellow', 'orange'])
        ax2.set_title(f"Verhältnis der CO2 Konzetration über die Zeit | 24h | {id}")
        plt.get_current_fig_manager().window.state('zoomed')
    else:
        print("No datapoint within the lecture periods exceeded the co2 limits")
        
    if lecture_exceed_co2 > 0 or lecture_critical_co2 > 0:
        #Log result to console
        print(f"> {LECTURE_START}h00 - {LECTURE_END}h00: {lecture_exceed_co2}/{lecture_total} = {round(float(lecture_exceed_co2 / lecture_total * 100 ), 2)}% of the given datapoints exceed the limit of 1000ppm")
        print(f"> {LECTURE_START}h00 - {LECTURE_END}h00: {lecture_critical_co2}/{lecture_total} = {round(float(lecture_critical_co2 / lecture_total * 100 ), 2)}% of the given datapoints exceed the limit of 750ppm")

        #plot pie chart
        fig1 = plt.figure()
        ax1 = fig1.add_subplot(111)
        pie1 = ax1.pie([lecture_exceed_co2, lecture_critical_co2, lecture_non_critical_co2], explode = [0.1, 0.05, 0], labels = [">= 1000ppm", ">= 750ppm", "< 750 ppm"], startangle = 90, counterclock = False, autopct = '%1.1f%%', colors = ['red', 'orange', 'green'])
        ax1.set_title("Verhältnis der CO2 Konzetration über die Zeit | " + str(LECTURE_START) + "h00 - " + str(LECTURE_END) + "h00 Uhr | " + id)
        plt.get_current_fig_manager().window.state('zoomed')
    else:
        print("No datapoint exceeded the co2 limits")

#----------------------------------------------------------------------------------------------------------------------------------------
def plotData(id, data):
    date_arr = data[0]
    time_arr = data[1]
    co2 = data[2]   
    #temp = data[3]
    
    plot_calc_graphs(id, time_arr, date_arr, co2)
    plot_calc_percentage(id, time_arr, co2)

    plt.show()
    
#----------------------------------------------------------------------------------------------------------------------------------------
def parseArgs():

    with open(ID_FILE) as f:
        ids = f.readlines()
    
    for _, id in enumerate(ids): ids[_] = id.rstrip()

    #definition of the possible arguments
    parser = argparse.ArgumentParser(description = f"This script will evaluate the collected co2 data.")
    parser.add_argument("-id",
                        "--identifier", 
                        type=str, 
                        required=True,
                        help=f"Identifier of the LoRa Device as defined in the related flow within NodeRed:\n{ids}")

    parser.add_argument("-sd",
                        "--startDate",
                        type=str,
                        required=True,
                        help="Start date for query request: YYYY-MM-DD (Start date < End date)")

    parser.add_argument("-ed",
                        "--endDate",
                        type=str,
                        required=True,
                        help="End date for query request: YYYY-MM-DD (Start date < End date)")

    parser.add_argument("-st",
                        "--startTime",
                        type=str,
                        required=False,
                        default="00:00:00",
                        help="Start time for query request: HH:MM:SS (Start time < End time)")

    parser.add_argument("-et",
                        "--endTime",
                        type=str,
                        required=False,
                        default="00:00:00",
                        help="End time for query request: HH:MM:SS (Start time < End time)")

    parser.add_argument("-lim",
                        "--limit",
                        type=str,
                        required=False,
                        default="5000",
                        help="Limit of datasets within the given time range")

    return parser.parse_args()

#----------------------------------------------------------------------------------------------------------------------------------------
def main(id, sd, ed, st, et, limit):

    print("\n>>>THU/IAS - CO2 Evaluation<<<")
    print("-------------------------------")

    #prepare input strings to match influxdb format
    start = f"{sd}T{st}Z"
    end = f"{ed}T{et}Z"

    data_raw = InfluxDB_Query.queryData(id, start, end, limit)

    if data_raw != -1: 
        jsonData = InfluxDB_Query.processJSON(data_raw, id)
        data = processData_co2(jsonData)
    else: return
    
    if data != -1: plotData(id, data)
    else: return

#----------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
   
    args = parseArgs()
    main(args.identifier, args.startDate, args.endDate, args.startTime, args.endTime, args.limit)
    #main("CO2_Sensor_3", "2021-08-02", "2021-08-07", "00:00:00", "00:00:00", "20000")
    