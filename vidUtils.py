from datetime import datetime, timedelta
import pandas as pd
import os
import sys
import cv2

cwd = os.getcwd()
delimiter = "\\" if "\\" in cwd else "/"
repoPath = delimiter.join(cwd.split(delimiter)[:cwd.split(delimiter).index("dataImport")]) + delimiter
sys.path.append(repoPath + "dataImport/")
bulkDataPath = repoPath + "bulkData/"
from rwWorkingTSDf import writeWorkingTSDf, dt_to_fnString

def bulkExtension(time):
    return time.strftime("%Y") + "/" + time.strftime("%m-%d") + "/"


def getFrame(deviceDescriptor, startTS, endTS, index):
    #use the timestamp to find the video
    directory = bulkDataPath + "_".join(deviceDescriptor) + "/" + bulkExtension(startTS)
    fileName = dt_to_fnString(startTS) + "_"  + dt_to_fnString(endTS) + ".mp4"
    if not os.path.exists(directory + fileName):
        print("no path to that video")
        return None
    
    cap = cv2.VideoCapture(video_path)
    # Set the frame position
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    success, frame = cap.read()
    cap.release()
    
    if success:
        return frame  # Returns the frame as a NumPy array
    else:
        print("Could not retrieve the frame")
        return None