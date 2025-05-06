#!/bin/bash

set -e  # Exit on error

# Source directories
WORKING_DATA="/home/chowder/Documents/workingData"
BULK_DATA="/home/chowder/Documents/bulkData"
EXPORTS_DATA="/home/chowder/Documents/dataExports"

# Destination mounts
SSD_DEST="/media/chowder/abhiksFiles"
HDD_DEST="/media/chowder/eb722a4b-57f1-4cf6-9e3f-a23e5bc2962a"

# Rsync options
RSYNC_OPTS="-avh --progress --exclude='.Trash-*'"

echo "Starting sync..."

# Function to sync a folder to a destination
sync_folder() {
    SRC=$1
    DEST_ROOT=$2
    DEST_PATH="$DEST_ROOT$(basename $SRC)"

    echo "Syncing $SRC to $DEST_PATH"
    mkdir -p "$DEST_PATH"
    rsync $RSYNC_OPTS "$SRC/" "$DEST_PATH/"
}

# Sync all sources to SSD
sync_folder "$WORKING_DATA" "$SSD_DEST/"
sync_folder "$BULK_DATA" "$SSD_DEST/"
sync_folder "$EXPORTS_DATA" "$SSD_DEST/"

# Sync all sources to HDD
sync_folder "$WORKING_DATA" "$HDD_DEST/"
sync_folder "$BULK_DATA" "$HDD_DEST/"
sync_folder "$EXPORTS_DATA" "$HDD_DEST/"

echo "All data synced successfully."
