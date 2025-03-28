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
from rwWorkingTSDf import dt_to_fnString, deleteTSDfInterval

output_fourcc = "avc1"

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



def deleteVidInterval(deviceDescriptor, startTime, endTime):
    toDelDf = readWorkingTSDF(deviceDescriptor, None, delStartTime, delEndTime)
    grouped = toDelDf.groupby("videoStartTime")
    groupKeys = sorted(toDelDf['videoStartTime'].unique())
    allFileNames = []
    for firstTs, group in grouped:
        lastTs = group["videoEndTime"].iloc[0]
        allFileNames.append(getMP4Path(deviceDescriptor, firstTs, lastTs))
    allFileNames = sorted(allFileNames)
    if len(allFileNames) == 0:
        print("no frames in this interval")
        return
    
    firstCut = grouped.get_group(groupKeys[0])['videoIndex'].iloc[0] != 0
    lastRow = grouped.get_group(groupKeys[-1]).iloc[-1]
    lastCut = lastRow.name != lastRow['videoEndTime']

    firstGroup = grouped.get_group(groupKeys[0])
    lastGroup = grouped.get_group(groupKeys[-1])
    output_start_ts = groupKeys[0]
    output_end_ts = lastGroup['videoEndTime'].iloc[0]

    # get output parameters from the first video
    cap = cv2.VideoCapture(allFileNames[0])
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*output_fourcc)
    tempFilePath = bulkDataPath + "_".join(deviceDescriptor) + "/temp.mp4"
    cap.release()

    # make an outout with the temp direcotry
    out = cv2.VideoWriter(tempFilePath, fourcc, fps, (width, height))


    if firstCut:
        cap = cv2.VideoCapture(allFileNames[0])
        end_frame_index = firstGroup['videoIndex'].iloc[0]
        for i in range(end_frame_index):
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
        cap.release()
        if not lastCut:
            output_end_ts = firstGroup.iloc[0].name

    if lastCut:
        cap = cv2.VideoCapture(allFileNames[-1])
        start_frame_index = lastGroup['videoIndex'].iloc[-1] + 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame_index)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
        cap.release()
        if not firstCut:
            output_start_ts = lastGroup.iloc[-1].name

    out.release()

    newFileName = getMP4Path(deviceDescriptor, output_start_ts, output_end_ts)

    [os.remove(f) for f in allFileNames]

    if not firstCut and not lastCut:
        #delete the temp file
        os.remove(tempFilePath)
    else:
        #move the temp file to the new file name
        shutil.move(tempFilePath, newFileName)

    deleteTSDfInterval(deviceDescriptor, delStartTime, delEndTime)









