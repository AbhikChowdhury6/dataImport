import json
import pytz
from datetime import datetime
import pandas as pd
import os
import sys
def getRepoPath():
    cwd = os.getcwd()
    delimiter = "\\" if "\\" in cwd else "/"
    repoPath = delimiter.join(cwd.split(delimiter)[:cwd.split(delimiter).index("dataImport")+1]) + delimiter
    return repoPath
repoPath = getRepoPath()
sys.path.append(repoPath)
import rwWorkingTSDf
from rwWorkingTSDf import writeWorkingTSDf


exportDataPath = "/home/chowder/Documents/dataExports/fitbit/25-1-7/takeout-20250106T144047Z-001/Takeout/Fitbit/Global Export Data/"
#read in the path of the export
#exportsDataPath = sys.argv[1]

# get alist of files with HR data
dir_list = os.listdir(exportDataPath)
hrFilenames = sorted([x for x in dir_list if x.split("-")[0] == "heart_rate"])

# parse the HR's from the files
def to_iso(s):
    return '20' + s[6:8] + '-' + s[0:2] + '-' + s[3:5] + s[8:]

samplesCount = 0
samplesList = []
for fn in hrFilenames:
    data = json.load(open(exportDataPath + fn))
    for row in data:
        sampleDT = datetime.fromisoformat(to_iso(row["dateTime"]))
        samplesList.append([sampleDT, 
                            row["value"]["confidence"], 
                            row["value"]["bpm"]])
        samplesCount += 1
        if samplesCount % 1_000_000 == 0:
            print(f"added {samplesCount} samples so far")
print(f"added {samplesCount} samples")


# make the DF
columnNames = ["sampleDT", "confidence", "value"]
samplesList = sorted(samplesList, key=lambda x: x[0]) #sort by timestamp
print("finished sorting")

fitbitHRdf = pd.DataFrame(data=samplesList, columns=columnNames)
fitbitHRdf = fitbitHRdf.set_index("sampleDT")
print("made dataframe")
fitbitHRdf.index = fitbitHRdf.index.tz_localize('UTC')
print("loacalized index to utc")
fitbitHRdf["confidence"] = fitbitHRdf["confidence"].astype('uint8')

deviceDescriptor = ["abhik", "0", "fitbit", "charge4or5", "hr", "builtin"]
#write the DF
writeWorkingTSDf(deviceDescriptor, fitbitHRdf)

print("done")
