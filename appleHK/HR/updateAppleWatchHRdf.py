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


exportsDataPath = sys.argv[1]
appleDeviceName = sys.argv[2]
deviceName = sys.argv[3]

# my device names
# Abhik_AppleWatch_10_46mm_0
# called watch10
# Abhik_AppleWatch_6_40mm_0
# called watch6

def getAppleHKSamplesForDevice(targetSourceName, targetRecordType, exportsDataPath):
    # samples are of the format "SampleDT", "Value"
    numRecords = 0
    totalRecords = 0
    data = []

    for event, elem in ET.iterparse(exportsDataPath, events=("start", "end")):
        totalRecords += 1
        # if totalRecords % 1_000_000 == 0: print(f"{totalRecords}")

        if event != "start" or elem.tag != "Record":
            elem.clear()
            continue
        record = elem.attrib
        if record["type"] != targetRecordType or record["sourceName"] != targetSourceName:
            elem.clear()
            continue

        numRecords += 1
        if numRecords % 1_000_000 == 0: print(f"cuurently found {numRecords}")
        newRow = {"sampleDT": datetime.fromisoformat(record["startDate"]), "value": float(record["value"])}
        data.append(newRow)
        elem.clear() # this is important
    
    print(f"parsed total {totalRecords}")
    print(f"found {numRecords} relevant records")
    df = pd.DataFrame(data)
    df = df.set_index("sampleDT")
    return df

watchData = getAppleHKSamplesForDevice(appleDeviceName, "HKQuantityTypeIdentifierHeartRate", exportsDataPath)

writeWorkingTSDf("abhik", "0", "apple", deviceName, "hr", "builtin", watchData)