
# the function we'll make will take in the export file and return a list of source names , versions, and device metrics like ID's for a given record type
def getHKDeviceInfo(targetRecordType, record):
    # check if the type of record is right
    if (record["type"] == targetRecordType):

        # parse the device to a dictonary to make sure we have the right one
        # raw text of record["device"] should look like this 
        # '<<HKDevice: 0x999999999>, name:Apple Watch, manufacturer:' +
        # 'Apple Inc., model:Watch, hardware:Watch6,1, software:7.6>'
        device = [[x.split(":")[0].strip(), x.split(":")[1]] 
                  for x in record["device"].split(",")
                  if len(x.split(":")) == 2]

        device = [x for sublist in device for x in sublist]

        device[0] = device[0][3:]
        device[1] = device[1][:-1]
        # device[-1] = device[-1][:-1] # removes a hanging '>' from the field

        return device
    
    return None


def getDevicesForRecordType(targetRecordType, exportLocation):
    numRecords = 0
    totalRecords = 0
    devices = set()

    for event, elem in ET.iterparse(exportLocation, events=("start", "end")):
        totalRecords += 1
        # if totalRecords % 1_000_000 == 0: print(f"{totalRecords}")
        if event == "start" and elem.tag == "Record":
            record = elem.attrib
            deviceInfo = getHKDeviceInfo(targetRecordType, record)
            if deviceInfo is not None:
                numRecords += 1
                if numRecords % 1_000_000 == 0: print(f"cuurently found {numRecords}")

                sourceData = ["sourceName", record["sourceName"], "sourceVersion", record["sourceVersion"]]
                sourceData += deviceInfo
                devices.add(tuple(sourceData[1::2]))
        elem.clear() # this is important
    
    print(f"parsed total {totalRecords}")
    print(f"found {numRecords} relevant records")
    return devices