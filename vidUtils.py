from datetime import datetime, timedelta
import pandas as pd
import os
import sys
import cv2
import subprocess


cwd = os.getcwd()
delimiter = "\\" if "\\" in cwd else "/"
repoPath = delimiter.join(cwd.split(delimiter)[:cwd.split(delimiter).index("dataImport")]) + delimiter
sys.path.append(repoPath + "dataImport/")
bulkDataPath = repoPath + "bulkData/"
daysVidsPath = repoPath + "daysVids/"
from rwWorkingTSDf import writeWorkingTSDf, dt_to_fnString

def bulkExtension(time):
    return time.strftime("%Y") + "/" + time.strftime("%m-%d") + "/"

def getMP4Path(deviceDescriptor, startTS, endTS):
    directory = bulkDataPath + "_".join(deviceDescriptor) + "/" + bulkExtension(startTS)
    fileName = dt_to_fnString(startTS) + "_"  + dt_to_fnString(endTS) + ".mp4"
    if not os.path.exists(directory + fileName):
        print(directory + fileName)
        print("no path to that video")
        return ""
    return directory + fileName

def getFrame(deviceDescriptor, startTS, endTS, index):
    mp4Loc = getMP4Path(deviceDescriptor, startTS, endTS)
    cap = cv2.VideoCapture(mp4Loc)
    # Set the frame position
    cap.set(cv2.CAP_PROP_POS_FRAMES, index)
    success, frame = cap.read()
    cap.release()
    
    if success:
        return frame  # Returns the frame as a NumPy array
    else:
        print("Could not retrieve the frame")
        return None


def getCap(deviceDescriptor, startTS, endTS):
    mp4Loc = getMP4Path(deviceDescriptor, startTS, endTS)
    return cv2.VideoCapture(mp4Loc)


def generateDaysVid(deviceDescriptor, ts):
    sourceDirectory = bulkDataPath + "_".join(deviceDescriptor) + "/" + bulkExtension(ts)
    if not os.path.exists(sourceDirectory):
        print("No directory: " + sourceDirectory)
        return
    
    targetDirectory = daysVidsPath + "_".join(deviceDescriptor) + ts.strftime("_%Y-%m-%d/")
    os.makedirs(targetDirectory, exist_ok=True)

    mp4s = sorted(os.listdir(sourceDirectory))

    # Create a file listing all MP4s (ffmpeg requires this format)
    list_file_path = os.path.join(targetDirectory, "file_list.txt")
    with open(list_file_path, "w") as f:
        for mp4 in mp4s:
            f.write(f"file '{os.path.join(sourceDirectory, mp4)}'\n")

    output_file = os.path.join(targetDirectory, f"{deviceDescriptor[1]}.mp4")

    # Use ffmpeg to concatenate without re-encoding
    ffmpeg_command = [
        "ffmpeg", "-f", "concat", "-safe", "0",
        "-i", list_file_path, "-c", "copy", output_file
    ]
    subprocess.run(ffmpeg_command, check=True)

    print("Finished processing:", output_file)














