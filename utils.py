import pandas as pd
import os
import sys

cwd = os.getcwd()
delimiter = "\\" if "\\" in cwd else "/"
repoPath = delimiter.join(cwd.split(delimiter)[:cwd.split(delimiter).index("dataImport")]) + delimiter

workingDataPath = repoPath + "workingData/"
exportsDataPath = repoPath + 'dataExports/'

def infillIntervals(intervals):
    # Shift columns to compare consecutive rows
    next_start = intervals['startDate'].shift(-1)

    # Find rows where there is a gap
    gap_mask = next_start > intervals['endDate']

    # Create a DataFrame for the gaps
    gap_df = pd.DataFrame({
        'startDate': df.loc[gap_mask, 'endDate'],
        'endDate': next_start[gap_mask],
        'value': -1  # indicator for gaps
    })

    # Concatenate the original DataFrame and the gap DataFrame
    combined_df = pd.concat([df, gap_df])

    return combined_df.sort_values('startDate').reset_index(drop=True)

# returns an interval DataFrame [startDate, endDate, value]
# for every group with samples always less than maxDelta apart
# and at least coveres minGroupTime
def getHRIntervals(HRDf, maxDelta = 20, minGroupTime = pd.Timedelta(minutes=5)):
    time_diffs = HRDf.index.to_series().diff()
    
    # Mark where the time difference exceeds the threshold (group break points)
    group_breaks = time_diffs.dt.total_seconds() > maxDelta
    
    # Assign group labels by cumulatively summing the group breaks
    group_labels = group_breaks.cumsum()

    # Create a dataframe of (start_time, end_time) for each group
    group_labels_times = pd.Series(group_labels.index, index=group_labels.values)
    gStarts = group_labels_times[~group_labels_times.index.duplicated(keep="first")]
    gEnds = group_labels_times[~group_labels_times.index.duplicated(keep="last")]
    allGroupsDf = pd.DataFrame({'startTime':gStarts, 'endTime': gEnds})

    #check min group time
    groupsDf = allGroupsDf[allGroupsDf['endTime'] - allGroupsDf['startTime'] > minGroupTime]
    
    groupsDf['value'] = 1
    return groupsDf


def calcSingleIntersection(intervals1, intervals2):
    intersectingIntervals = []

    intervals1i = 0
    intervals2i = 0

    # go though every group in group 1
    while intervals1i < len(intervals1) and intervals2i < len(intervals2):
        # no intersctions 
        # if the end time of group 2 is less than the start time of group 1
        if intervals1[intervals1][1] < intervals2[intervals2i][0]:
            #no intersection, go to the next group in intervals1
            intervals1 += 1
            continue
        
        # if the intervals1 group we're looking starts after the end of the group 2 group
        if intervals1[intervals1][0] > intervals2[intervals2i][1]:
            #no intersection, and check the next late group
            intervals2i += 1
            continue

        # there is an intersection and it is the latest of the start times
            # and the earliest of the end times
        intersectionStart = max(intervals1[intervals1i][0], intervals2[intervals2i][0])
        intersectionEnd = min(intervals1[intervals1i][1], intervals2[intervals2i][1])
        intersectingIntervals.append([intersectionStart, intersectionEnd])

        #whichever set had the interval with the earliest end time, iterate that one
        if intervals1[intervals1i][1] <= intervals2[intervals2i][1]:
            intervals1i += 1
        else:
            intervals2i += 1
        
    return intersectingIntervals





def intervalOverlap(groupsList):
    intersectingIntervalsList = groupsList[0][groupsList[0].value == 1][['startDate', 'endDate']].values()
    for groupsi in range(1, len(groupsList)):
        listForm = groupsList[groupsi][groupsList[groupsi].value == 1][['startDate', 'endDate']].values()
        intersectingIntervalsList = calcSingleIntersection(intersectingIntervalsList, groupsList[groupsi])
    
    ColumnNames = ["startDate", "endDate", "value"]
    dfVals = [[interval[0], interval[1], 1] for interval in intersectingIntervalsList]
    intersectingIntervals = pd.DataFrame(columns=ColumnNames, data=dfVals)
    return infillIntervals(intersectingIntervals)




def secBySecHRGraph(HRDfs, group, deviceNames, withpoints):
    colorsList = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
    graphTimeStart = group[0]
    graphTimeEnd = group[1]

    plotWidth = (graphTimeEnd - graphTimeStart).total_seconds() / 60
    fig, ax = plt.subplots(figsize=(16, 4.0)) # is set this to 2k normally
    
    plt.gca().set_title("HR for " + ", ".join(deviceNames) + " for " + str(graphTimeStart))
    plt.gca().set_ylim([30,210])
    plt.gca().set_xlim([graphTimeStart, graphTimeEnd])
    plt.xticks(rotation=45)
    plt.ylabel("Heart Rate")
    plt.xlabel("Time")
    # xFormatter = plt.matplotlib.dates.DateFormatter('%H:%M', tz=pytz.timezone(timezone))
    # plt.gca().xaxis.set_major_formatter(xFormatter)

    legend1 = []
    for deviceIndex in range(len(deviceNames)):
        # prepping HR
        HRDf = HRDfs[deviceIndex]
        HRDf["sampleDT"] = HRDf.index
        HRTimes = [HRDf.iloc[rowIndex]["sampleDT"] for rowIndex in range(len(HRDf))]
        HRValues = [HRDf.iloc[rowIndex]['value'] for rowIndex in range(len(HRDf))]
        
        # ax.plot(HRTimes, HRValues, alpha=.5, linewidth=5, color='white')

        ax.plot(HRTimes, HRValues, label=deviceNames[deviceIndex], alpha=.5, linewidth=5, color=colorsList[deviceIndex])
        if withpoints: ax.plot(HRTimes, HRValues, alpha=.3, color=colorsList[deviceIndex], marker='.', markersize=10)


    plt.legend(loc="upper left")
    plt.style.use('default') 

    plt.show()

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
            group = groupsForDevice[groupi].values()
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
def getHRsForTimePeriods(intervals, HRDf):
    mask = pd.Series([False] * len(HRDf), index=HRDf.index)
    
    for start, end in intervals[['startDate', 'endDate']].values.tolist():
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
    
    if len(workingDataFiles) > 0:
        dfSoFar = pd.read_parquet(workingDataHRPath + workingDataFiles[0])
        for dataFileNameIndex in range(1, len(workingDataFiles)):
            dfSoFar = pd.concat([dfSoFar, pd.read_parquet(workingDataHRPath + workingDataFiles[dataFileNameIndex])]) 
        dfSoFar = dfSoFar[~dfSoFar.index.duplicated(keep="first")].sort_index()
        return pd.DataFrame(dfSoFar['value'])
    print('no files found')
    return []


def getRowsPerFile(HRDf, targetFileSize = 2 * 1024 * 1024):
    HRDf.iloc[:1_000_000].to_parquet(workingDataPath + 'compressionTest.parquet.gzip',
                compression='gzip')
    file_size = os.path.getsize(workingDataPath + 'compressionTest.parquet.gzip')
    os.remove(workingDataPath + 'compressionTest.parquet.gzip')
    rows_per_file = int(1_000_000 // (file_size / targetFileSize))
    print(f"a million rows took up {file_size / targetFileSize} MB")
    print(f"putting {rows_per_file} rows per file")
    return rows_per_file



def writeHRDfFile(HRDf, startRow, endRow, workingDataHRPath):
    print(f"saving rows {startRow} to {endRow}")

    parquetName = HRDf.iloc[startRow].name.strftime('%Y-%m-%dT%H%M%S%z') +\
                "_" +\
                HRDf.iloc[endRow].name.strftime('%Y-%m-%dT%H%M%S%z') +\
                ".parquet.gzip"
    print(f"to a file named {parquetName}")

    HRDf.iloc[startRow:endRow+1].to_parquet(workingDataHRPath + parquetName,
            compression='gzip') 

def writeFreshHRFiles(HRDf, rows_per_file, workingDataHRPath):
    # Get the size of the file in bytes
    numFiles = math.ceil(len(HRDf) / rows_per_file)
    print(f'saving to {numFiles} files')
    for fileNumber in range(numFiles + 1):
        startRow = fileNumber * rows_per_file
        if startRow > len(HRDf) - 1:
            continue
        if fileNumber == numFiles-1:
            endRow = len(HRDf) - 1
        else:
            endRow = ((fileNumber + 1) * rows_per_file) - 1

        writeHRDfFile(HRDf, startRow, endRow, workingDataHRPath)

def writeToExistingFiles(HRDf, rows_per_file, workingDataHRPath):
    #read in the file names and get the intervals
    fileNames = sorted(os.listdir(workingDataHRPath))
    [os.remove(workingDataHRPath + file) for file in fileNames]
    for fnum, fileName in enumerate(fileNames):
        print(fileName)
        print(fnum)
        startTime = pd.to_datetime(fileName.replace('.', '_').split('_')[0])
        startRow = HRDf.index.searchsorted(startTime, side='right')
        if fnum == 0: startRow = 0
        if startRow > len(HRDf)-1: startRow = len(HRDf)-1
        print(f"the start row and parsed time is {startRow} {startTime}")
        print(f"the time of the start row is {HRDf.index[startRow]}")

        endTime = pd.to_datetime(fileName.replace('.', '_').split('_')[1])
        endRow = HRDf.index.searchsorted(endTime, side='right')
        if fnum == len(fileNames)-1: endRow = len(HRDf)-1
        if endRow > len(HRDf)-1: endRow = len(HRDf)-1
        print(f"the end row and  parsed  time is {endRow} {endTime}")
        print(f"the time of the end row is {HRDf.index[endRow]}")

        rows_remaining = endRow - startRow
        while rows_remaining > 2 * rows_per_file:
            print(f'{rows_remaining} is too many rows writing {startRow} to {(endRow - rows_remaining) + rows_per_file}')
            writeHRDfFile(HRDf, startRow, (endRow - rows_remaining) + rows_per_file, workingDataHRPath)
            rows_remaining -= rows_per_file
            startRow += rows_per_file
        
        writeHRDfFile(HRDf, startRow, endRow, workingDataHRPath)

import math
def writeWorkingHRDfParquet(deviceName, HRDf, clearFiles = True):
    # I would like to write this in a way that
        #if there is new data in one of the intervals
        #that file grows, untill it hits 2MB expected then it splits
    rows_per_file = getRowsPerFile(HRDf)
    workingDataHRPath = workingDataPath + deviceName + "/hr/"
    ogFiles = os.listdir(workingDataHRPath)

    workingDataFiles = os.listdir(workingDataHRPath)
    if len(workingDataFiles) == 0:
        if clearFiles:
            print("Clearing files")
            [os.remove(workingDataHRPath + file) for file in ogFiles]
        print('no files found making new ones')
        writeFreshHRFiles(HRDf, rows_per_file, workingDataHRPath)

    else:
        writeToExistingFiles(HRDf, rows_per_file, workingDataHRPath)
        





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
































