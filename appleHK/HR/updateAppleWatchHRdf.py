import pandas as pd
from datetime import datetime
import os
import sys
cwd = os.getcwd()
delimiter = "\\" if "\\" in cwd else "/"
repoPath = delimiter.join(cwd.split(delimiter)[:cwd.split(delimiter).index("dataImport")]) + delimiter
sys.path.append(repoPath + "dataImport/")
import rwWorkingTSDf
from rwWorkingTSDf import writeWorkingTSDf
import xml.etree.ElementTree as ET 


exportsDataPath = "/home/chowder/Documents/dataExports/apple/2025-1-15/export/apple_health_export/export.xml"
appleDeviceName = sys.argv[1]
deviceName = sys.argv[2]

# my device names
# Abhik_AppleWatch_10_46mm_0
# called AppleWatch-10-46mm
# Abhik_AppleWatch_6_40mm_0
# called watch6

# Abhik_AppleWatch_10_46mm_0 AppleWatch-10-46mm



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
dd = ["abhik", '0', "apple", deviceName, 'hr', 'builtin']

writeWorkingTSDf(dd, watchData)