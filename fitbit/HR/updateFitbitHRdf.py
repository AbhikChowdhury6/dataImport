import os
import sys
def getRepoPath():
    cwd = os.getcwd()
    delimiter = "\\" if "\\" in cwd else "/"
    repoPath = delimiter.join(cwd.split(delimiter)[:cwd.split(delimiter).index("dataImport")+1]) + delimiter
    return repoPath
repoPath = getRepoPath()
sys.path.append(repoPath)
from utils import exportsDataPath, workingDataPath, writeWorkingHRDfParquet

import json
import pytz
from datetime import datetime
import pandas as pd


# find the folder that contains a bunch of json files some of which contain heart rates
fitbitHRWorkingDataPath = workingDataPath + 'fitbit/hr/'

#update this with the location of the new export
exportFilePath = exportsDataPath + "/home/chowder/Documents/dataExports/fitbit/25-1-7/takeout-20250106T144047Z-001/Takeout/Fitbit/Global Export Data"
dir_list = os.listdir(exportFilePath)




#load up the exisitng fitbit hr data if it's there
workingDataFiles = os.listdir(fitbitHRWorkingDataPath)
columnNames = ["sampleDT", "confidence", "value"]
dfSoFar = pd.DataFrame(columns=columnNames).set_index("sampleDT")

for dataFileName in workingDataFiles:
    dfSoFar = pd.concat([dfSoFar, pd.read_parquet(fitbitHRWorkingDataPath + dataFileName)]) 

dfSoFar = dfSoFar[~dfSoFar.index.duplicated(keep="first")].sort_index()

print(f"read in {len(dfSoFar)} rows from {len(workingDataFiles)} files")




# get a list of unique dates in the index
#   removing the latest 3 days since they might be incomplete
if len(dfSoFar) > 0:
    datesSoFar = sorted(list(set(dfSoFar.index.date)))[:-3]
    print(datesSoFar[-1])
    hrFilenames = [x for x in dir_list if x.split("-")[0] == "heart_rate"]
    hrFilenames = [x for x in hrFilenames if pd.to_datetime(x[11:-5]).date() not in datesSoFar]
else:
    hrFilenames = [x for x in dir_list if x.split("-")[0] == "heart_rate"]



#read in the new files
#takes like 50 seconds to make 16 million rows
def to_iso(s):
    return '20' + s[6:8] + '-' + s[0:2] + '-' + s[3:5] + s[8:]

samplesCount = 0
samplesList = []
for fn in hrFilenames:
    data = json.load(open(exportFilePath + fn))
    for row in data:
        sampleDT = datetime.fromisoformat(to_iso(row["dateTime"]))
        samplesList.append([sampleDT, 
                            row["value"]["confidence"], 
                            row["value"]["bpm"]])
        samplesCount += 1
        if samplesCount % 1_000_000 == 0:
            print(f"added {samplesCount} samples so far")
print(f"added {samplesCount} samples")


#make a df out of the new data
columnNames = ["sampleDT", "confidence", "value"]
samplesList = sorted(samplesList, key=lambda x: x[0]) #sort by timestamp

fitbitHRdf = pd.DataFrame(data=samplesList, columns=columnNames)
fitbitHRdf = fitbitHRdf.set_index("sampleDT")
fitbitHRdf.index = fitbitHRdf.index.tz_localize('UTC')

fitbitHRdf.index = fitbitHRdf.index.tz_convert("US/Arizona")
fitbitHRdf.index = pd.to_datetime(fitbitHRdf.index)

fitbitHRdf["confidence"] = fitbitHRdf["confidence"].astype('uint8')
fitbitHRdf["value"] = fitbitHRdf["value"].astype('uint8')
fitbitHRdf.dtypes

# concatenate the old and the new df's
# remove duplicate indexes
fitbitHRdf = pd.concat([dfSoFar, fitbitHRdf])
fitbitHRdf = fitbitHRdf[~fitbitHRdf.index.duplicated(keep="first")].sort_index()

# all the info i want
# folder named 2025
# file named
# fitbit_charge4or5_hr_builtin
# data stored in UTC

#write the df
writeWorkingHRDfParquet('fitbit', fitbitHRdf)







