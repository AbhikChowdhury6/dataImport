import pandas as pd
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
import pytz

cwd = os.getcwd()
delimiter = "\\" if "\\" in cwd else "/"
repoPath = delimiter.join(cwd.split(delimiter)[:cwd.split(delimiter).index("dataImport")]) + delimiter

workingDataPath = repoPath + "workingData/"


import hashlib
import numpy as np

def fnString_to_dt(fn_string):
    return datetime.fromisoformat(fn_string.replace(",", "."))

def dt_to_fnString(dt):
    return dt.astimezone(ZoneInfo("UTC")).strftime('%Y-%m-%dT%H%M%S,%f%z')

# Function to compute a short hash of a Python object
def short_hash_df(df, length=8):
    values_hash = pd.util.hash_pandas_object(df).values
    index_hash = pd.util.hash_pandas_object(df.index).values
    combined = np.concatenate((values_hash, index_hash)).tobytes()

    # Return the hash truncated to the specified length
    return hashlib.md5(combined).hexdigest()[:length]


# this writes a file for a timeSeries of a DF
def writeTimeSeriesDf(TSDf, targetPath):
    sh = short_hash_df(TSDf)
    parquetName = dt_to_fnString(TSDf.iloc[0].name) +\
                "_" +\
                dt_to_fnString(TSDf.iloc[-1].name) +\
                "_" + sh + "_" + ".parquet.gzip"
    print(f"saved to a file named {parquetName}")

    TSDf.to_parquet(targetPath + parquetName,
            compression='gzip') 


#takes in a dataframe you want to save and does it in multiple files
#with the number of rows between rows_per_file and 2 * rows_per_file 
def saveRows(TSDf, targetPath, rows_per_file):
    if len(TSDf) == 0: return
    startRow = 0
    endRow = len(TSDf)
    rows_remaining = endRow - startRow
    while rows_remaining > 2 * rows_per_file:
        print(f'{rows_remaining} is too many rows writing {startRow} to {(endRow - rows_remaining) + rows_per_file}')
        writeTimeSeriesDf(TSDf.iloc[startRow: (endRow - rows_remaining) + rows_per_file + 1], targetPath)
        rows_remaining -= rows_per_file
        startRow += rows_per_file
    writeTimeSeriesDf(TSDf.iloc[startRow:endRow+1], targetPath)



#given a df returns the approximate number of rows to get a target file size 
def calcRowsPerFile(Df, targetFileSize, targetPath, fileName = 'test.parquet.gzip'):
    if fileName == 'test.parquet.gzip':
        fileRows = 1_000_000
        if len(Df) < fileRows: fileRows = len(Df)-1
        Df.iloc[:fileRows].to_parquet(targetPath + fileName,
                        compression='gzip')
        file_size = os.path.getsize(targetPath + fileName)
        os.remove(targetPath + fileName)
    else:
        fileRows = len(pd.read_parquet(targetPath + fileName))
        file_size = os.path.getsize(targetPath + fileName)
    
    rows_per_file = int(fileRows//(file_size/targetFileSize))
    return rows_per_file



#iterates over exiting files and adds rows in the relevant scope
def writeToExistingTSFiles(TSDf, fileNames, targetPath, rows_per_file):
    tzi = TSDf.index[0].tzinfo
    for fileNum, fileName in enumerate(fileNames):
        if fileNum == 0:
            startTime = pd.Timestamp.min.tz_localize("UTC")
        else:
            startTime = fnString_to_dt(fileName.split('_')[0]).astimezone(tzi)
        
        if len(fileNames) == 1 or fileNum == len(fileNames) - 1:
            endTime = pd.Timestamp.max.tz_localize("UTC")
        else:
            endTime = fnString_to_dt(fileNames[fileNum + 1].split('_')[0]).astimezone(tzi)
        
        sdf = TSDf.loc[startTime:endTime]
        if len(sdf) == 0:
            print("nothing to add")
            continue

        # if the hash doesn't match write a new file
        if short_hash_df(sdf) != fileName.split('_')[2]:
            print(f"the hashes don't match for start time {startTime} to end time {endTime}")
            print("reading and combining to see if there's any new data")
            # read in that file
            existingParquet = pd.read_parquet(targetPath + fileName)
            # combine, sort and deduplicate the dfs
            combinedParquet = pd.concat([sdf, existingParquet])
            combinedParquet = combinedParquet[~combinedParquet.index.duplicated(keep="first")].sort_index()
            # then save rows for the combined df
            if short_hash_df(combinedParquet) == fileName.split('_')[2]:
                print("hashes match now")
            else:
                print("hashes still don't match")
                os.remove(targetPath + fileName)
                saveRows(combinedParquet, targetPath, rows_per_file)
        else:
            print(f'hashes match for {fileName}')


####### this is the function to be used
def writeWorkingTSDf(responsiblePartyName, instanceName, developingPartyName, deviceName, dataType, dataSource, TSDf, targetFileSize = 2 * 1024 * 1024):
    dataFolderName = "_".join([responsiblePartyName, instanceName, developingPartyName, deviceName, dataType, dataSource]) + "/"
    fullPath = workingDataPath + dataFolderName
    if not os.path.exists(fullPath):
        os.makedirs(fullPath)
    currentFileNames = sorted(os.listdir(fullPath))

    TSDf.index = TSDf.index.tz_convert('UTC')

    TSDf = TSDf[~TSDf.index.duplicated(keep="first")].sort_index()


    if len(currentFileNames) == 0:
        rows_per_file = calcRowsPerFile(TSDf, targetFileSize, fullPath)
        saveRows(TSDf, fullPath, rows_per_file)

    else:
        rows_per_file = calcRowsPerFile(TSDf, targetFileSize, fullPath, currentFileNames[0])
        writeToExistingTSFiles(TSDf, currentFileNames, fullPath, rows_per_file)

def readWorkingTSDF(responsiblePartyName, instanceName, developingPartyName, deviceName, dataType, dataSource,
                     chnageTz = None, startTime = pd.Timestamp.min.tz_localize("UTC"), endTime = pd.Timestamp.max.tz_localize("UTC")):
    # find the data folder
    dataFolderName = "_".join([responsiblePartyName, instanceName, developingPartyName, deviceName, dataType, dataSource]) + "/"
    fullPath = workingDataPath + dataFolderName
    if not os.path.exists(fullPath):
        print("no folder with the location " + fullPath)
        return None


    fileNames = sorted(os.listdir(fullPath))
    if len(fileNames) == 0:
        print("no data in the folder")
        return None

    justTimes = [x.split(".")[0] for x in fileNames]

    foundFileCount = 0
    for fname in justTimes:
        # index 0 is start time, index 1 is end time
        fnElements = fname.split("_")
        
        # check if the file name lands within the the start and end time
        if not (fnString_to_dt(fnElements[0]) < endTime and fnString_to_dt(fnElements[1]) > startTime):
            continue
        
        #read in the file
        foundFileCount += 1
        if foundFileCount == 1:
            readDF = pd.read_parquet(fullPath + fname + ".parquet.gzip")
        else:
            pd.concat([readDF, pd.read_parquet(fullPath + fname + ".parquet.gzip")])
    
    
    if foundFileCount == 0:
        print("No files found for the requested dates")
        return None

    # a sorted copy of the df you read in based on the exact bounds passed in
    print(readDF.head())
    dfToReturn = readDF[startTime:endTime].sort_index().copy()
    
    if chnageTz is not None:
        print("converting to timeszone " + chnageTz)
        dfToReturn.index = dfToReturn.index.tz_convert(chnageTz)
    
    print(f"read in {len(readDF)} rows from {foundFileCount} files, retruning {len(dfToReturn)} rows")

    return dfToReturn

