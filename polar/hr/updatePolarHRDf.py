import json
import pandas as pd
from datetime import datetime
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

#exportLocation = "/home/chowder/Documents/dataExports/polar/polar-user-data-export_9cc7f44f-6622-4e4d-b682-f3065d10aeb1/"
exportsDataPath = sys.argv[1]

dir_list = os.listdir(exportsDataPath)
hrFilenames = [x for x in dir_list if x.split("-")[0] == "training"]

columnNames = ["sampleDT", "value"]

samplesCount = 0
samplesList = []

for fn in hrFilenames:
    print(fn)
    data = json.load(open(exportLocation + fn))

    samples = data["exercises"][0]["samples"]
    if 'heartRate' not in samples:
        continue
    for row in samples['heartRate']:
        if len(row) != 2:
            continue
        samplesList.append([datetime.fromisoformat(row["dateTime"] + "-0700"), row["value"]])
        samplesCount += 1
        if samplesCount % 1_000_000 == 0:
            print(samplesCount)


samplesList = sorted(samplesList, key=lambda x:x[0])
samplesList = [x for x in samplesList if x[1] > 0]
polarHRdf = pd.DataFrame(data=samplesList, columns=columnNames)
polarHRdf = polarHRdf.set_index("sampleDT")

writeWorkingTSDf("abhik", "0", "polar", "h10", "hr", "builtin", polarHRdf)