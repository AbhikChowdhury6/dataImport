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
    next_start = intervals['startTime'].shift(-1)

    # Find rows where there is a gap
    gap_mask = next_start > intervals['endTime']

    # Create a DataFrame for the gaps
    gap_df = pd.DataFrame({
        'startTime': intervals.loc[gap_mask, 'endTime'],
        'endTime': next_start[gap_mask],
        'value': -1  # indicator for gaps
    })

    # Concatenate the original DataFrame and the gap DataFrame
    combined_df = pd.concat([intervals, gap_df])

    return combined_df.sort_values('startTime').reset_index(drop=True)

# returns an interval DataFrame [startTime, endTime, value]
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
    groupsDf = allGroupsDf[allGroupsDf['endTime'] - allGroupsDf['startTime'] > minGroupTime].copy()
    
    groupsDf['value'] = 1
    return groupsDf


def calcSingleIntersection(intervals1, intervals2):
    if len(intervals1) == 0 or len(intervals2) == 0:
        return []
    intersectingIntervals = []

    intervals1i = 0
    intervals2i = 0

    # go though every group in group 1
    while intervals1i < len(intervals1) and intervals2i < len(intervals2):
        # no intersctions 
        # if the end time of group 2 is less than the start time of group 1
        # print(intervals1i)
        # print(intervals1[intervals1i])
        # print(intervals2i)
        # print(intervals2[intervals2i])
        if intervals1[intervals1i][1] < intervals2[intervals2i][0]:
            #no intersection, go to the next group in intervals1
            intervals1i += 1
            continue
        
        # if the intervals1 group we're looking starts after the end of the group 2 group
        if intervals1[intervals1i][0] > intervals2[intervals2i][1]:
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
    intersectingIntervalsList = groupsList[0][groupsList[0].value == 1][['startTime', 'endTime']].values
    for groupsi in range(1, len(groupsList)):
        listForm = groupsList[groupsi][groupsList[groupsi].value == 1][['startTime', 'endTime']].values
        intersectingIntervalsList = calcSingleIntersection(intersectingIntervalsList, listForm)
    
    ColumnNames = ["startTime", "endTime", "value"]
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
    
    for start, end in intervals[['startTime', 'endTime']].values.tolist():
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

import hashlib
import pickle

# Function to compute a short hash of a Python object
def short_hash(obj, length=8):
    # Serialize the object using pickle
    obj_bytes = pickle.dumps(obj)
    
    # Compute MD5 hash of the serialized object
    hash_obj = hashlib.md5(obj_bytes)
    
    # Return the hash truncated to the specified length
    return hash_obj.hexdigest()[:length]

# this writes a file for a subset of a DF
def writeHRDfFile(HRDf, workingDataHRPath):
    sh = short_hash(HRDf)
    parquetName = HRDf.iloc[0].name.strftime('%Y-%m-%dT%H%M%S%z') +\
                "_" +\
                HRDf.iloc[-1].name.strftime('%Y-%m-%dT%H%M%S%z') +\
                "_" + sh + "_" + ".parquet.gzip"
    print(f"saved to a file named {parquetName}")

    HRDf.to_parquet(workingDataHRPath + parquetName,
            compression='gzip') 

#takes in a dataframe you want to save and does it in multiple files
def saveRows(df, workingDataHRPath, rows_per_file):
    if len(df) == 0: return
    startRow = 0
    endRow = len(df)
    rows_remaining = endRow - startRow
    while rows_remaining > 2 * rows_per_file:
        print(f'{rows_remaining} is too many rows writing {startRow} to {(endRow - rows_remaining) + rows_per_file}')
        writeHRDfFile(df.iloc[startRow: (endRow - rows_remaining) + rows_per_file + 1], workingDataHRPath)
        rows_remaining -= rows_per_file
        startRow += rows_per_file
    writeHRDfFile(df.iloc[startRow:endRow+1], workingDataHRPath)

def rowsPerFile(Df, targetFileSize, workingDataHRPath, fileName = 'test.parquet.gzip'):
    if fileName == 'test.parquet.gzip':
        fileRows = 1_000_000
        if len(Df) < fileRows: fileRows = len(Df)-1
        Df.iloc[:fileRows].to_parquet(workingDataHRPath + fileName,
                        compression='gzip')
        file_size = os.path.getsize(workingDataHRPath + fileName)
        os.remove(workingDataHRPath + fileName)
    else:
        fileRows = len(pd.read_parquet(workingDataHRPath + fileName))
        file_size = os.path.getsize(workingDataHRPath + fileName)
    
    rows_per_file = int(fileRows//(file_size/targetFileSize))
    return rows_per_file

def writeToExistingHRFiles(HRDf, fileNames, workingDataHRPath, rows_per_file):
    tzi = HRDf.index[0].tzinfo
    for fileNum, fileName in enumerate(fileNames):
        if fileNum == 0:
            startTime = HRDf.index[0]
        else:
            startTime = pd.to_datetime(fileName.split('_')[0]).tz_convert(tzi)
        
        if len(fileNames) == 1 or fileNum == len(fileNames) - 1:
            endTime = HRDf.index[-1]
        else:
            endTime = pd.to_datetime(fileNames[fileNum + 1].split('_')[0]).tz_convert(tzi)
        
        # if the hash doesn't match write a new file
        if short_hash(HRDf.loc[startTime:endTime]) != fileName.split('_')[2]:
            print("the hashes don't match")
            os.remove(workingDataHRPath + fileName)
            saveRows(HRDf.loc[startTime:endTime], workingDataHRPath, rows_per_file)
        else:
            print(f'hashes match for {fileName}')

def writeWorkingHRDfParquet(deviceName, HRDf, clearFiles = True, targetFileSize = 2 * 1024 * 1024):
    workingDataHRPath = workingDataPath + deviceName + "/hr/"
    fileNames = sorted(os.listdir(workingDataHRPath))

    if len(fileNames) == 0:
        rows_per_file = rowsPerFile(HRDf, targetFileSize, workingDataHRPath)
        saveRows(HRDf, workingDataHRPath, rows_per_file)

    else:
        rows_per_file = rowsPerFile(HRDf, targetFileSize, workingDataHRPath, fileNames[0])
        writeToExistingHRFiles(HRDf, fileNames, workingDataHRPath, rows_per_file)


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
    # left join hypnodf with grouped first startTime and last endTime
    endTimesOfGroups = pd.merge(hypnoDF, 
                            hypnoDF.groupby('ConsecutiveGroup').endTime.agg(max), 
                            on='ConsecutiveGroup',
                            how='left')[['endTime_x', 'endTime_y']]

    hypnoDF = pd.merge(hypnoDF, endTimesOfGroups, 
                    left_on='endTime', 
                    right_on='endTime_x').drop('endTime_x', axis=1)

    startTimesOfGroups = pd.merge(hypnoDF, 
                                hypnoDF.groupby('ConsecutiveGroup').startTime.agg(min), 
                                on='ConsecutiveGroup',
                                how='left')[['startTime_x', 'startTime_y']]

    hypnoDF = pd.merge(hypnoDF,startTimesOfGroups,
                    left_on='startTime', 
                    right_on='startTime_x').drop('startTime_x', axis=1)
    
    #print(hypnoDF.head(20))
    # rename Columns
    dfToReturn = pd.DataFrame(columns=['startTime', 'endTime', 'value'])

    dfToReturn['endTime'] = hypnoDF['endTime_y']
    dfToReturn['startTime'] = hypnoDF['startTime_y']
    dfToReturn['value'] = hypnoDF["isInTypes"]
    dfToReturn['durationInMin'] = (dfToReturn['endTime'] - dfToReturn['startTime']).dt.total_seconds()/60
    #print(dfToReturn.drop_duplicates().head(5))
    return dfToReturn.drop_duplicates()


from datetime import datetime, date, time, timedelta
import pytz
import matplotlib.pyplot as plt
def graphHypnoDate(hypnoDf, forDate, deviceName, cutOffTime = time(12,0,0), timezone = 'US/Arizona'):
    graphTimeStart = pytz.timezone(timezone).localize(datetime.combine(forDate - timedelta(days=1), cutOffTime))
    graphTimeEnd = graphTimeStart + timedelta(days=1)
    hypnoDfForDay = hypnoDf[(hypnoDf['startTime'] < graphTimeEnd) &
                            (hypnoDf['endTime'] > graphTimeStart)]

    # print(hypnoDfForDay['startTime'].iloc[0])
    # print(hypnoDfForDay['value'].iloc[0])
    # print(hypnoDfForDay['endTime'].iloc[0])

    values = []
    times = []
    for rowIndex in range(len(hypnoDfForDay)):
        times.append(hypnoDfForDay.iloc[rowIndex]['startTime'])
        values.append(hypnoDfForDay.iloc[rowIndex]['value'])
        times.append(hypnoDfForDay.iloc[rowIndex]['endTime'])
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
    hypnoDfForDay = hypnoDf[(hypnoDf['startTime'] < graphTimeEnd) &
                            (hypnoDf['endTime'] > graphTimeStart)]


    #prepping hypno
    hypnoValues = []
    hypnoTimes = []
    for rowIndex in range(len(hypnoDfForDay)):
        hypnoTimes.append(hypnoDfForDay.iloc[rowIndex]['startTime'])
        hypnoValues.append(hypnoDfForDay.iloc[rowIndex]['value'])
        hypnoTimes.append(hypnoDfForDay.iloc[rowIndex]['endTime'])
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
































