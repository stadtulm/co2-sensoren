#Organization:  TH Ulm
#               Prittwitzstraße 10
#               89075 Ulm
#
#Project:       Zukunftsstadt - LoRa CO2 Evaluation
#Date:          05.01.2022
#Author:        Petrick, Louis
#               louis.petrick@thu.de

#This script is used as a module to query data from influxDB 

from ast import In
from influxdb import InfluxDBClient
import json

#change influxDB credentials here
INFLUX_IP       = 'xxx'
INFLUX_PORT     = 0
INFLUX_USER     = 'xxx'
INFLUX_PW       = 'xxx'

#----------------------------------------------------------------------------------------------------------------------------------------
#Will create an client to connect to influxdb and query the data in the requested range
def queryData(SensorID, start, end, limit):
    try: 
        client = InfluxDBClient(host=INFLUX_IP, port=INFLUX_PORT, username=INFLUX_USER, password=INFLUX_PW)
        client.switch_database('loradata')                  
        #use get_list_measurements() and get_list_series() for debugging of expected database content

    except Exception as e:
        print(e)
        print(">>>ERROR<<<: Couldn't connect to the database.\n> Aborting script...")
        return -1

    try:
        QUERY = 'SELECT co2, Temp FROM autogen.backendtest WHERE (ID = ' + chr(39) + SensorID + chr(39) + ' AND time >= ' + chr(39) + start + chr(39) + ' AND time < ' + chr(39) + end + chr(39) + ') ORDER BY time ASC LIMIT ' + limit + ''
        print("> Querying: " + str(QUERY))
        #expected query string: 'SELECT co2, Temp FROM autogen.backendtest WHERE (ID = 'CO2_Sensor_X' AND time > now() - xx) ORDER BY time DESC LIMIT xxx'
        #Backup query string: QUERY = 'SELECT co2, Temp FROM autogen.backendtest WHERE (ID = ' + chr(39) + SensorID + chr(39) + ' AND time > now() - ' + timeRange + ') ORDER BY time ASC LIMIT ' + limit + ''
        data = client.query(QUERY)

    except Exception as e:
        print(e)
        print(">>>ERROR<<<: Couldn't request query from database. Check Exception for connection or query string format!\n> Aborting script...")
        return -1

    return data

#----------------------------------------------------------------------------------------------------------------------------------------
#Extracts the JSON formatted data to a variable
def processJSON(data, id):
    #read out json file
    file_str = "JSON_Files/" + id + "data.json"

    with open(file_str, "w") as writeFile:
        json.dump(data.raw, writeFile)
    writeFile.close()

    readFile = open(file_str, "r")
    jsonData = json.load(readFile)
    readFile.close()

    #***complement check for empty data from json request here***

    return jsonData
#----------------------------------------------------------------------------------------------------------------------------------------