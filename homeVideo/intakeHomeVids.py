# this function will just read in the folders and put them in the bulk data
# it won't handle slicing videos
# it won't look at the names of the devices

# we can run this at 5:10 pm all of the sending should be done by then
#crontab -e
# 9 17 * * * /usr/bin/mv /home/uploadingGuest/recentCaptures/* /home/chowder/Documents/recentCaptures/
# 10 17 * * * /home/chowder/anaconda3/envs/vision/bin/python /home/chowder/Documents/dataImport/homeVideo/intakeHomeVids.py 

from datetime import datetime, timedelta
import pandas as pd
import os
import sys
import shutil

cwd = os.getcwd()
delimiter = "\\" if "\\" in cwd else "/"
repoPath = delimiter.join(cwd.split(delimiter)[:cwd.split(delimiter).index("dataImport")]) + delimiter
sys.path.append(repoPath + "dataImport/")
import rwWorkingTSDf
from rwWorkingTSDf import writeWorkingTSDf, fnString_to_dt
recentCapPath = repoPath + "recentCaptures/"
bulkDataPath = repoPath + "bulkData/"

def bulkExtension(time):
    return time.strftime("%Y") + "/" + time.strftime("%m-%d") + "/"

foldersToImport = sorted(os.listdir(recentCapPath))
for f in foldersToImport:
    # we don't really care about reading in the day we just want the descriptor
    camDescriptors = f.split("_")[:-1]

    folderPath = recentCapPath + f + "/"
    if os.path.exists(folderPath + "new.mp4"):  # if a leftover new got in
        os.remove(folderPath + "new.mp4")

    fileNameBases = sorted(list(set([x.split(".")[0] for x in os.listdir(folderPath)])))

    # combine all parquets
    for i, fb in enumerate(fileNameBases):
        source = folderPath + fb + ".parquet.gzip"
        rDf = pd.read_parquet(source)
        # rDf = rDf.reset_index().set_index("videoIndex")
        # rDf.rename(columns={'sampleDT': 'videoIndex'}, inplace=True)
        # rDf.index.name = "sampleDT"
        # print(rDf.head())
        rDf.index = rDf.index.tz_convert('UTC')
        if i == 0:
            readDf = rDf
        else:
            readDf = pd.concat([readDf, rDf])
    
    writeWorkingTSDf(*camDescriptors, readDf)

    for fb in fileNameBases:
        vidStrartTime = fnString_to_dt(fb.split("_")[0])
        fileName = fb + ".mp4"
        source = folderPath + "/" + fileName
        destinationBase =  bulkDataPath + "_".join(camDescriptors) + "/" + bulkExtension(vidStrartTime)
        if not os.path.exists(destinationBase):
                print("made directory " + destinationBase)
                os.makedirs(destinationBase)
        shutil.move(source, destinationBase  + fileName)
    
    shutil.rmtree(folderPath)