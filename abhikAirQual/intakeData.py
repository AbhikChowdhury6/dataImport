import os
import sys
cwd = os.getcwd()
delimiter = "\\" if "\\" in cwd else "/"
repoPath = delimiter.join(cwd.split(delimiter)[:cwd.split(delimiter).index("dataImport")]) + delimiter
sys.path.append(repoPath + "dataImport/")
import rwWorkingTSDf
from rwWorkingTSDf import writeWorkingTSDf
import pandas as pd
import shutil

# at this point the data should be in the recentSensorCap folder
data_loc = repoPath + 'recentSensorCap/'
dir_list = sorted(os.listdir(data_loc))

if len(dir_list) == 0:
    print('no folders found')
    sys.exit()

# all I'll do is for each folder in recent sensor cap
for folder in dir_list:
    device_descriptor = folder.split('_')[:-1]

    folder_loc = data_loc + folder + '/'
    file_list = sorted(os.listdir(folder_loc))
    for i, file in enumerate(file_list):
        source = folder_loc + file
        print("source file is: %s ", source)
        rDf = pd.read_parquet(source)
        rDf.index = rDf.index.tz_convert('UTC')
        if i == 0:
            readDf = rDf
        else:
            readDf = pd.concat([readDf, rDf])
    
    writeWorkingTSDf(device_descriptor, readDf)
    shutil.rmtree(folder_loc)
    
