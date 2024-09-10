import pandas as pd
import os
import sys

cwd = os.getcwd()
delimiter = "\\" if "\\" in cwd else "/"
repoPath = delimiter.join(cwd.split(delimiter)[:cwd.split(delimiter).index("dataImport")]) + delimiter

workingDataPath = repoPath + "workingData/"
exportsDataPath = repoPath + 'dataExports/'


def getWorkingHRDfParquet(deviceName):
    workingDataHRPath = workingDataPath + deviceName + "/hr/"
    workingDataFiles = os.listdir(workingDataHRPath)
    columnNames = ["sampleDT", "value"]
    dfSoFar = pd.DataFrame(columns=columnNames).set_index("sampleDT")
    # print(dfSoFar.head())

    for dataFileName in workingDataFiles:
        # print(pd.read_parquet(workingDataHRPath + dataFileName).head())
        # print(pd.read_parquet(workingDataHRPath + dataFileName)['value'].head())
        # print(dfSoFar.head())
        dfSoFar['value'] = pd.concat([dfSoFar['value'], pd.read_parquet(workingDataHRPath + dataFileName)['value']]) 
        # print(dfSoFar.head())
    dfSoFar = pd.DataFrame(dfSoFar)

    return dfSoFar[~dfSoFar.index.duplicated(keep="first")].sort_index()

def writeHypnoDfParquet(deviceName, hypnoDf):
    parquetName = deviceName + "HypnoDf.parquet.gzip"
    hypnoDf.to_parquet(workingDataPath + deviceName + "/sleep/" + parquetName,
              compression='gzip') 


def getWorkingHypnoDfParquet(deviceName):
    workingDataSleepPath = workingDataPath + deviceName + "/sleep/"
    parquetName = deviceName + "HypnoDf.parquet.gzip"
    return pd.read_parquet(workingDataSleepPath + parquetName)


def regroupHypno(hypnoDF, includedTypes):
    hypnoDF["isInTypes"] = hypnoDF["value"].map(lambda x:int(x in includedTypes))
    hypnoDF["isNewGroup"] = (hypnoDF["isInTypes"] - hypnoDF["isInTypes"].shift(1)).map(lambda x:int(x != 0))
    hypnoDF['ConsecutiveGroup'] = hypnoDF['isNewGroup'].cumsum()

    # there must be a simpler way to do this, but it works
    # left join hypnodf with grouped first startDate and last endDate
    endTimesOfGroups = pd.merge(hypnoDF, 
                            hypnoDF.groupby('ConsecutiveGroup').endDate.agg(max), 
                            on='ConsecutiveGroup',
                            how='left')[['endDate_x', 'endDate_y']]

    hypnoDF = pd.merge(hypnoDF, endTimesOfGroups, 
                    left_on='endDate', 
                    right_on='endDate_x').drop('endDate_x', axis=1)

    startTimesOfGroups = pd.merge(hypnoDF, 
                                hypnoDF.groupby('ConsecutiveGroup').startDate.agg(min), 
                                on='ConsecutiveGroup',
                                how='left')[['startDate_x', 'startDate_y']]

    hypnoDF = pd.merge(hypnoDF,startTimesOfGroups,
                    left_on='startDate', 
                    right_on='startDate_x').drop('startDate_x', axis=1)
    
    #print(hypnoDF.head(20))
    # rename Columns
    dfToReturn = pd.DataFrame(columns=['startDate', 'endDate', 'value'])

    dfToReturn['endDate'] = hypnoDF['endDate_y']
    dfToReturn['startDate'] = hypnoDF['startDate_y']
    dfToReturn['value'] = hypnoDF["isInTypes"]
    dfToReturn['durationInMin'] = (dfToReturn['endDate'] - dfToReturn['startDate']).astype('timedelta64[m]')
    #print(dfToReturn.drop_duplicates().head(5))
    return dfToReturn.drop_duplicates()


from datetime import datetime, date, time, timedelta
import pytz
import matplotlib.pyplot as plt
def graphHypnoDate(hypnoDf, forDate, deviceName, cutOffTime = time(12,0,0), timezone = 'US/Arizona'):
    graphTimeStart = pytz.timezone(timezone).localize(datetime.combine(forDate, cutOffTime))
    graphTimeEnd = graphTimeStart + timedelta(days=1)
    hypnoDfForDay = hypnoDf[(hypnoDf['startDate'] < graphTimeEnd) &
                            (hypnoDf['endDate'] > graphTimeStart)]

    # print(hypnoDfForDay['startDate'].iloc[0])
    # print(hypnoDfForDay['value'].iloc[0])
    # print(hypnoDfForDay['endDate'].iloc[0])

    values = []
    times = []
    for rowIndex in range(len(hypnoDfForDay)):
        times.append(hypnoDfForDay.iloc[rowIndex]['startDate'])
        values.append(hypnoDfForDay.iloc[rowIndex]['value'])
        times.append(hypnoDfForDay.iloc[rowIndex]['endDate'])
        values.append(hypnoDfForDay.iloc[rowIndex]['value'])



    fig, ax = plt.subplots(figsize=(16.0, 4.0))

    plt.gca().set_title("Sleep Stages for " + deviceName + " for " + str(forDate))
    plt.gca().set_ylim([-1.3,3.3])
    plt.gca().set_xlim([graphTimeStart, graphTimeEnd])
    xFormatter = plt.matplotlib.dates.DateFormatter('%H:%M', tz=pytz.timezone(timezone))
    plt.gca().xaxis.set_major_formatter(xFormatter)


    legend1 = ax.plot(times, values, label=deviceName, alpha=1, linewidth=1)


    legend2 = [
        ax.axhline(y = -1, color = 'k', linestyle = ':', linewidth=.7, label = "No Data"),
        ax.axhline(y = 0, color = 'c', linestyle = ':', linewidth=.7, label = "Awake"),
        ax.axhline(y = 1, color = 'm', linestyle = ':', linewidth=.7, label = "Light"),
        ax.axhline(y = 2, color = 'r', linestyle = ':', linewidth=.7, label = "Deep"),
        ax.axhline(y = 3, color = 'b', linestyle = ':', linewidth=.7, label = "REM") 
    ]

    legendToAdd = ax.legend(loc="upper left", handles=legend1)
    plt.legend(loc="upper right", handles=legend2[::-1])

    ax.add_artist(legendToAdd)
    plt.ylabel("Sleep Stage")
    plt.xlabel("Time")
    plt.show()


































