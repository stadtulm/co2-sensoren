#Organization:  TH Ulm
#               Prittwitzstraße 10
#               89075 Ulm
#
#Project:       Zukunftsstadt - LoRa CO2 Evaluation
#Date:          05.01.2022
#Author:        Petrick, Louis
#               louis.petrick@thu.de

import argparse
import matplotlib.pyplot as plt
import InfluxDB_Query
import matplotlib.ticker as ticker

ID_FILE = 'CO2_Device_IDs.txt'

#----------------------------------------------------------------------------------------------------------------------------------------
def parseArgs():
    #definition of the possible arguments
    parser = argparse.ArgumentParser(description = 'This script will evaluate the collected co2 data')

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

    parser.add_argument("-lim",
                        "--limit",
                        type=str,
                        required=False,
                        default="20000",
                        help="Limit of datasets within the given time range")

    parser.add_argument("-sf",
                        action = 'store_true',
                        default=False)

    return parser.parse_args()

#----------------------------------------------------------------------------------------------------------------------------------------
def main(sd, ed, limit, sf):

    boxplot_data = []

    print("\n>>>THU/IAS - CO2 Evaluation<<<")
    print("-------------------------------")

    #prepare input strings to match influxdb format
    start = f"{sd}T00:00:00Z"
    end = f"{ed}T00:00:00Z"

    #read out lora device ids as specified in "CO2_Device_IDs"
    with open(ID_FILE) as f:
        ids = f.readlines()

    for id in ids:
        data_raw = []
        data_json = []
        co2_values = []
        datasets = []

        id = id.rstrip()
        print("Requesting Data from: " + id)
        data_raw = InfluxDB_Query.queryData(id, start, end, limit)
        data_json = InfluxDB_Query.processJSON(data_raw, id)

        try:
            datasets = data_json['series'][0]['values']
        except Exception as e:
            print(e)
            print(">>>ERROR<<< It seems like there is no data available in the given time range. Check .json file for more information on the dataset!")
            datasets.clear()

        #Only plot datasets which have content
        if len(datasets) > 0:
            print(f"Found {len(datasets)}/{limit} datasets")
            for dataset in datasets: 
                co2_values.append(dataset[1])    #keep only co2 value, discard timestamp and temperature

        boxplot_data.append(co2_values)
    
    fig, ax = plt.subplots()
    ax.boxplot(boxplot_data, showfliers=sf)
    ax.set_title(f"BoxPlot - Vergleich der CO2 Messwerte\n{sd} bis {ed}")
    ax.set_xlabel("Sensor #")
    ax.set_ylabel("CO2 [ppm]")
    ax.yaxis.grid(True)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(100))

    plt.get_current_fig_manager().window.state('zoomed')
    plt.show()

#----------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
   
    args = parseArgs()
    main(args.startDate, args.endDate, args.limit, args.sf)
    #main("2021-08-02", "2021-08-07", "20000")