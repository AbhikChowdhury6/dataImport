import os
import sys

cwd = os.getcwd()
delimiter = "\\" if "\\" in cwd else "/"
repoPath = delimiter.join(cwd.split(delimiter)[:cwd.split(delimiter).index("dataImport")]) + delimiter
sys.path.append(repoPath + "dataImport/")

import rwWorkingTSDf
from rwWorkingTSDf import writeWorkingTSDf, readWorkingTSDF

#given a device descriptor and a timestamp
# get the closest n frames centered around the timestamp
# along with a list of their timestamps
# if n is 5 it would get the closest frame and 2 frames either side
# if there are no times after then it would return just the 3 before


# if the device descriptor is not available it should print that and return an empty list

def getClosestFrame(deviceDescriptor, timestamp, n):
    pass


# given a tuple of timestamps being start and end
# as well as a device descriptor
# load 
def loadVidsOfInterval(deviceDescriptor, timestamps):
    pass


# the first thing that will be used for both the time series and the crames to look up
# take in a target timestamp and a number n wich wil be // 2 and the number of 
# it will return an n length list where empty values will be None
# we have gound where a timestamp belongs in the files, but how would we get the previous n
# timestamps


# check if there's a file for the target timestamp
# continually check for the gratest timestamp less than that
# iloc idx -1 or +1
# if its the end of the file, check if there are more files
# if so load it, if not replace the rest with Nones

# so since we arent currently holding any values that could be the index in the video 
# the provess to look up a frame index for a time would be to
# find the target timestamp
# find the name of the video that timestamp would be a part of
# query the times df for the number of timestamps for that video
# caluculate the index for the target timestamp based on the offset

# to calculate indexes it's so much easier to just store it in the metadata


#there'll be two kinds of window functions
#wondowed with time and windowed with samples
#the current read working tsdf works with a time window very nice for the standard width time series graphs

