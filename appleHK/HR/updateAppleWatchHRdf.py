import os
import sys
def getRepoPath():
    cwd = os.getcwd()
    delimiter = "\\" if "\\" in cwd else "/"
    repoPath = delimiter.join(cwd.split(delimiter)[:cwd.split(delimiter).index("dataImport")+1]) + delimiter
    return repoPath
repoPath = getRepoPath()
sys.path.append(repoPath)
from utils import exportsDataPath, writeWorkingHRDfParquet

pathOfExport = exportsDataPath + "apple/"
#change this to new export path
individualExportPath = "/17-9-24/export/apple_health_export/"
xmlFileName = "export.xml"


