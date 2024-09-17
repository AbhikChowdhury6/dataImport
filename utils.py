import pandas as pd
import os
import sys

cwd = os.getcwd()
delimiter = "\\" if "\\" in cwd else "/"
repoPath = delimiter.join(cwd.split(delimiter)[:cwd.split(delimiter).index("dataImport")]) + delimiter

workingDataPath = repoPath + "workingData/"
exportsDataPath = repoPath + 'dataExports/'

# returns a list of [[startTimestamp, endTimestamp], ...] 
# for every group with samples always less than maxDelta apart
# and at least coveres minGroupTime
def getHRGroups(series, maxDelta = 20, minGroupTime = pd.Timedelta(minutes=5)):
    if len(series) == 0:
        return []
    # add a column that is the time to next reading
    timesSeries = pd.Series(series.index)
    betweenMesures = ((timesSeries.shift(-1) - timesSeries)).dt.total_seconds()
    timeToNextDF = pd.DataFrame(timesSeries)
    timeToNextDF["timeToNextReading"]  =  betweenMesures
    # print(timeToNextDF.head(2))

    #filter out time to next reading that are too high
    ttnrGreaterThanThresh = timeToNextDF[timeToNextDF["timeToNextReading"] <= maxDelta]
    # print(ttnrGreaterThanThresh.head(2))

    #the indexes that have been removed indicate the boundaries of contiguious sections
    index_diff = ttnrGreaterThanThresh.index.to_series().diff()
    boundaryIndicators = index_diff[index_diff > 1].index.to_list()
    # print(boundaryIndicators)

    #add each bounded area to groupBoundaries, if it lasts longer than the minGroup time
    clusterStartIndex = 0
    groupBoundaries = []
    for bii in range(len(boundaryIndicators)): #bii being boundaryIndicatorIndex
        startTime = timeToNextDF["sampleDT"].iloc[clusterStartIndex]
        endTime = timeToNextDF["sampleDT"].iloc[boundaryIndicators[bii] - 1]
        # print( endTime - startTime)
        if endTime - startTime >= minGroupTime:
            groupBoundaries.append([startTime, endTime])
        
        clusterStartIndex = boundaryIndicators[bii]
    
    groupBoundaries.append([timeToNextDF["sampleDT"].iloc[clusterStartIndex], timeToNextDF["sampleDT"].iloc[-1]])
    
    return groupBoundaries

def calcIntersection(groups1, groups2):
    intersectingGroups = []

    groups1i = 0
    groups2i = 0

    # go though every group in group 1
    while groups1i < len(groups1) and groups2i < len(groups2):
        # no intersctions 
        # if the end time of group 2 is less than the start time of group 1
        if groups1[groups1i][1] < groups2[groups2i][0]:
            #no intersection, go to the next group in groups1
            groups1i += 1
            continue
        
        # if the groups1 group we're looking starts after the end of the group 2 group
        if groups1[groups1i][0] > groups2[groups2i][1]:
            #no intersection, and check the next late group
            groups2i += 1
            continue
        
        # print(f"groups1[{groups1i}]{groups1[groups1i]}")
        # print(f"groups2[{groups2i}]{groups2[groups2i]}")

        # there is an intersection and it is the latest of the start times
            # and the earliest of the end times
        intersectionStart = max(groups1[groups1i][0], groups2[groups2i][0])
        intersectionEnd = min(groups1[groups1i][1], groups2[groups2i][1])
        intersectingGroups.append([intersectionStart, intersectionEnd])

        #whichever set had the group with the earliest end time, iterate that one
        if groups1[groups1i][1] <= groups2[groups2i][1]:
            groups1i += 1
        else:
            groups2i += 1
        
    return intersectingGroups

def calcIntersectionOfMultipleGroups(groupsList):
    intersectingSet = groupsList[0]
    for groupsi in range(1, len(groupsList)):
        intersectingSet = calcIntersection(intersectingSet, groupsList[groupsi])
    return intersectingSet


from datetime import datetime, date, time, timedelta
import pytz
import matplotlib.pyplot as plt
def graphMultiHRDate(HRDfs, forDate, deviceNames, cutOffTime = time(12,0,0), timezone = 'US/Arizona'):
    colorsList = ['c', 'm', 'y', 'r', 'g', 'b', 'k'] #up to 7 HRs at a time
    graphTimeStart = pytz.timezone(timezone).localize(datetime.combine(forDate - timedelta(days=1), cutOffTime))
    graphTimeEnd = graphTimeStart + timedelta(days=1)

    fig, ax = plt.subplots(figsize=(16.0, 4.0), dpi=400) # is set this to 2k normally

    plt.gca().set_title("HR for " + ", ".join(deviceNames) + " for " + str(forDate))
    plt.gca().set_ylim([30,210])
    plt.gca().set_xlim([graphTimeStart, graphTimeEnd])
    plt.ylabel("Heart Rate")
    plt.xlabel("Time")
    # xFormatter = plt.matplotlib.dates.DateFormatter('%H:%M', tz=pytz.timezone(timezone))
    # plt.gca().xaxis.set_major_formatter(xFormatter)

    legend1 = []
    for deviceIndex in range(len(deviceNames)):
        # prepping HR
        HRDf = HRDfs[deviceIndex]
        HRDf["sampleDT"] = HRDf.index
        HRDfForDay = HRDf[(HRDf.index < graphTimeEnd) &
                        (HRDf.index > graphTimeStart)]
        
        # consider a gontunous section 10 minutes
        groupsForDevice = getHRGroups(HRDfForDay, 600)
        print (f"the day has {len(HRDfForDay)} samples for {deviceNames[deviceIndex]} in {len(groupsForDevice)} groups")

        for groupi in range(len(groupsForDevice)):
            group = groupsForDevice[groupi]
            groupSamples = HRDfForDay[(HRDfForDay.index > group[0]) & (HRDfForDay.index < group[1])]
            HRTimes = [groupSamples.iloc[rowIndex]["sampleDT"] for rowIndex in range(len(groupSamples))]
            HRValues = [groupSamples.iloc[rowIndex]['value'] for rowIndex in range(len(groupSamples))]

            #only add the first group to the legend
            if groupi == 0:
                ax.plot(HRTimes, HRValues, label=deviceNames[deviceIndex], alpha=.5, linewidth=1, color=colorsList[deviceIndex])
            else:
                ax.plot(HRTimes, HRValues, alpha=.5, linewidth=1, color=colorsList[deviceIndex])


    plt.legend(loc="upper left")
    plt.show()

# query the HRDf for the times during the section
def getHRsForTimePeriods(times, HRDf):
    mask = pd.Series([False] * len(HRDf), index=HRDf.index)
    
    for start, end in times[['startDate', 'endDate']].values.tolist():
        # Use binary search to find the positions of the start and end times
        start_idx = HRDf.index.searchsorted(start, side='left')  # Start index (left inclusive)
        end_idx = HRDf.index.searchsorted(end, side='right')     # End index (right exclusive)

        # Set the mask to True for the rows between the start and end positions
        mask.iloc[start_idx:end_idx] = True    

    return HRDf[mask]

def printHRMetrics(HRDf):
    print(f"mean HR is {HRDf['value'].mean()}")
    print(f"median HR is {HRDf['value'].median()}")
    print(f"min HR is {min(HRDf['value'])}")
    print(f"max HR is {max(HRDf['value'])}")
    HRDf['value'].plot.hist(bins=60)

def plot2HRHistDensities(HRDf1, HRDf2, name1, name2):
    bins = [x for x in range(30,221, (220-30)//40)]
    ax = HRDf1.value.plot.hist(bins=bins, xlim=(30,200), alpha=0.5, label=name1, density=True)
    ax.hist(HRDf2.value, bins=bins, alpha=0.5, color="g", label=name2, density=True)
    ax.set_xlabel("BPM")
    ax.set_title("Comparison between " + name1 + " and " + name2 + " probability densities")
    ax.axvline(HRDf1.value.mean(), color='b', linestyle='dashed', linewidth=1)
    ax.axvline(HRDf2.value.mean(), color='darkgreen', linestyle='dashed', linewidth=1)
    ax.legend(loc='upper right') 
    ax.set_xlim(30,220)

def getWorkingHRDfParquet(deviceName):
    workingDataHRPath = workingDataPath + deviceName + "/hr/"
    workingDataFiles = os.listdir(workingDataHRPath)
    columnNames = pd.read_parquet(workingDataHRPath + workingDataFiles[0]).columns.to_list()
    columnNames.insert(0,'sampleDT')
    dfSoFar = pd.DataFrame(columns=columnNames).set_index("sampleDT")

    for dataFileName in workingDataFiles:
        dfSoFar = pd.concat([dfSoFar, pd.read_parquet(workingDataHRPath + dataFileName)]) 
    dfSoFar = dfSoFar[~dfSoFar.index.duplicated(keep="first")].sort_index()

    return pd.DataFrame(dfSoFar['value'])

import math
def writeWorkingHRDfParquet(deviceName, HRDf):
    # Get the size of the file in bytes
    workingDataHRPath = workingDataPath + deviceName + "/hr/"
    HRDf.to_parquet(workingDataHRPath + 'compressionTest.parquet.gzip',
              compression='gzip') 
    file_size = os.path.getsize(workingDataHRPath + 'compressionTest.parquet.gzip')
    os.remove(workingDataHRPath + 'compressionTest.parquet.gzip')
    numFiles = math.ceil(file_size / (1024 * 1024 * 5))
    rows_per_file = int(len(HRDf)/numFiles)
    print(f"the file size of all the data is about {file_size // (1024 * 1024)} MB")
    print(f"the total number of rows in the file is {len(HRDf)}")
    print(f"splitting into {numFiles} number of about 5MB files with {rows_per_file} rows per file")


    for fileNumber in range(numFiles + 1):
        startRow = fileNumber * rows_per_file
        if fileNumber == numFiles:
            endRow = len(HRDf) - 1
        else:
            endRow = ((fileNumber + 1) * rows_per_file) - 1

        print(f"saving rows {startRow} to {endRow}")
        print(HRDf.iloc[startRow])

        parquetName = HRDf.iloc[startRow].name.strftime('%Y-%m-%dT%H%M%S%z') +\
                    "_" +\
                    HRDf.iloc[endRow].name.strftime('%Y-%m-%dT%H%M%S%z') +\
                    ".parquet.gzip"
        print(f"to a file named {parquetName}")

        print(pd.to_datetime(HRDf.iloc[startRow].name.strftime('%Y-%m-%dT%H%M%S%z')))

        HRDf.iloc[startRow:endRow+1].to_parquet(workingDataHRPath + parquetName,
                compression='gzip') 



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
    dfToReturn['durationInMin'] = (dfToReturn['endDate'] - dfToReturn['startDate']).dt.total_seconds()/60
    #print(dfToReturn.drop_duplicates().head(5))
    return dfToReturn.drop_duplicates()


from datetime import datetime, date, time, timedelta
import pytz
import matplotlib.pyplot as plt
def graphHypnoDate(hypnoDf, forDate, deviceName, cutOffTime = time(12,0,0), timezone = 'US/Arizona'):
    graphTimeStart = pytz.timezone(timezone).localize(datetime.combine(forDate - timedelta(days=1), cutOffTime))
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

from datetime import datetime, date, time, timedelta
import pytz
import matplotlib.pyplot as plt
def graphHypnoandHRDate(hypnoDf, HRDf, forDate, sleepDeviceName, HRDeviceName, cutOffTime = time(12,0,0), timezone = 'US/Arizona'):
    graphTimeStart = pytz.timezone(timezone).localize(datetime.combine(forDate - timedelta(days=1), cutOffTime))
    graphTimeEnd = graphTimeStart + timedelta(days=1)
    hypnoDfForDay = hypnoDf[(hypnoDf['startDate'] < graphTimeEnd) &
                            (hypnoDf['endDate'] > graphTimeStart)]


    #prepping hypno
    hypnoValues = []
    hypnoTimes = []
    for rowIndex in range(len(hypnoDfForDay)):
        hypnoTimes.append(hypnoDfForDay.iloc[rowIndex]['startDate'])
        hypnoValues.append(hypnoDfForDay.iloc[rowIndex]['value'])
        hypnoTimes.append(hypnoDfForDay.iloc[rowIndex]['endDate'])
        hypnoValues.append(hypnoDfForDay.iloc[rowIndex]['value'])
    
    # plotting Hypno
    fig, ax = plt.subplots(figsize=(16.0, 4.0))

    plt.gca().set_title("Sleep Stages for " + sleepDeviceName + " and HR for " + HRDeviceName + " for " + str(forDate))
    plt.gca().set_ylim([-1.3,3.3])
    plt.gca().set_xlim([graphTimeStart, graphTimeEnd])
    plt.ylabel("Sleep Stage")
    plt.xlabel("Time")

    legend1 = [ax.plot(hypnoTimes, hypnoValues, label=sleepDeviceName + " sleep", alpha=1, linewidth=1, color='b')[0]]
    legend2 = [
        ax.axhline(y = -1, color = 'k', linestyle = ':', linewidth=.7, label = "No Data"),
        ax.axhline(y = 0, color = 'c', linestyle = ':', linewidth=.7, label = "Awake"),
        ax.axhline(y = 1, color = 'm', linestyle = ':', linewidth=.7, label = "Light"),
        ax.axhline(y = 2, color = 'r', linestyle = ':', linewidth=.7, label = "Deep"),
        ax.axhline(y = 3, color = 'b', linestyle = ':', linewidth=.7, label = "REM") 
    ]



    # plotting HR
    ax2 = ax.twinx()
    ax2.set_ylim([30,210])
    ax2.set_ylabel('Heart Rate', color='r') 

    # prepping HR
    HRDf["sampleDT"] = HRDf.index
    HRDfForDay = HRDf[(HRDf.index < graphTimeEnd) &
                    (HRDf.index > graphTimeStart)]
    
    # consider a gontunous section 10 minutes
    groupsForDevice = getHRGroups(HRDfForDay, 600)
    print (f"the day has {len(HRDfForDay)} samples for {HRDeviceName} in {len(groupsForDevice)} groups")

    for groupi in range(len(groupsForDevice)):
        group = groupsForDevice[groupi]
        groupSamples = HRDfForDay[(HRDfForDay.index > group[0]) & (HRDfForDay.index < group[1])]
        HRTimes = [groupSamples.iloc[rowIndex]["sampleDT"] for rowIndex in range(len(groupSamples))]
        HRValues = [groupSamples.iloc[rowIndex]['value'] for rowIndex in range(len(groupSamples))]

        #only add the first group to the legend
        if groupi == 0:
            legend1.append(ax2.plot(HRTimes, HRValues, label=HRDeviceName + " HR", alpha=1, linewidth=1, color='r')[0])
        else:
            ax2.plot(HRTimes, HRValues, alpha=1, linewidth=1, color='r')


    legendToAdd = ax.legend(loc="upper left", handles=legend1)
    plt.legend(loc="upper right", handles=legend2[::-1])
    ax.add_artist(legendToAdd)

    xFormatter = plt.matplotlib.dates.DateFormatter('%H:%M', tz=pytz.timezone(timezone))
    plt.gca().xaxis.set_major_formatter(xFormatter)

    plt.show()
































