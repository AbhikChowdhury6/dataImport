import pandas as pd
import os
import sys
from datetime import datetime

cwd = os.getcwd()
delimiter = "\\" if "\\" in cwd else "/"
repoPath = delimiter.join(cwd.split(delimiter)[:cwd.split(delimiter).index("dataImport")]) + delimiter

workingDataPath = repoPath + "workingData/"


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


# this writes a file for a timeSeries of a DF
def writeTimeSeriesDf(TSDf, targetPath):
    sh = short_hash(TSDf)
    parquetName = TSDf.iloc[0].name.strftime('%Y-%m-%dT%H%M%S%z') +\
                "_" +\
                TSDf.iloc[-1].name.strftime('%Y-%m-%dT%H%M%S%z') +\
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
            startTime = TSDf.index[0]
        else:
            startTime = pd.to_datetime(fileName.split('_')[0]).tz_convert(tzi)
        
        if len(fileNames) == 1 or fileNum == len(fileNames) - 1:
            endTime = TSDf.index[-1]
        else:
            endTime = pd.to_datetime(fileNames[fileNum + 1].split('_')[0]).tz_convert(tzi)
        
        # if the hash doesn't match write a new file
        if short_hash(TSDf.loc[startTime:endTime]) != fileName.split('_')[2]:
            print("the hashes don't match")
            os.remove(targetPath + fileName)
            saveRows(TSDf.loc[startTime:endTime], targetPath, rows_per_file)
        else:
            print(f'hashes match for {fileName}')


####### this is the function to be used
def writeWorkingTSDf(partyName, deviceName, dataType, dataSource, TSDf, targetFileSize = 2 * 1024 * 1024):
    dataFolderName = "_".join([partyName, deviceName, dataType, dataSource]) + "/"
    fullPath = workingDataPath + dataFolderName
    if not os.path.exists(fullPath):
        os.makedirs(fullPath)
    currentFileNames = sorted(os.listdir(fullPath))

    TSDf.index = TSDf.index.tz_convert('UTC')


    if len(currentFileNames) == 0:
        rows_per_file = calcRowsPerFile(TSDf, targetFileSize, fullPath)
        saveRows(TSDf, fullPath, rows_per_file)

    else:
        rows_per_file = calcRowsPerFile(TSDf, targetFileSize, fullPath, currentFileNames[0])
        writeToExistingTSFiles(TSDf, currentFileNames, fullPath, rows_per_file)

def readWorkingTSDF(partyName, deviceName, dataType, dataSource, chnageTz = None, startTime = datetime.min, endTime = datetime.max):
    # find the data folder
    dataFolderName = "_".join([partyName, deviceName, dataType, dataSource]) + "/"
    fullPath = workingDataPath + dataFolderName
    if not os.path.exists(fullPath):
        print("no folder with the location " + fullPath)
        return None


    fileNames = sorted(os.listdir(fullPath))
    if len(fileNames) == 0:
        print("no data in the folder")
        return None


    foundFileCount = 0
    for fname in fileNames:
        # index 0 is start time, index 1 is end time
        fnElements = fname.split("_")
        
        # check if the file name lands within the the start and end time
        if not (datetime.fromisoformat(fnElements[0]) < endTime and datetime.fromisoformat(fnElements[1]) > startTime):
            continue
        
        #read in the file
        foundFileCount += 1
        if foundFileCount == 1:
            readDF = pandas.read_parquet(fullPath + fname)
        else:
            pd.concat([readDF, pandas.read_parquet(fullPath + fname)])
    
    
    if foundFileCount == 0:
        print("No files found for the requested dates")
        return None

    # a sorted copy of the df you read in based on the exact bounds passed in
    dfToReturn = readDF.iloc[startTime:endTime].sort_index().copy()
    
    if chnageTz is not None:
        print("converting to timeszone " + chnageTz)
        dfToReturn.index = dfToReturn.index.tz_convert(chnageTz)
    
    print(f"read in {len(readDF)} rows from {foundFileCount} files, retruning {len(dfToReturn)} rows")

    return dfToReturn

