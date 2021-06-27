This file imports data from the mind monitor moble application, testing with Abhiks phone a moto5g


The file format
- The mind monitor app

the preproccesing from the muse headset
- 60HZ notch filter on raw data I believe
- features in the EEG singnal (jaw clench, blink) (don't know exactly how they are doing this)
- it appears that the Delta and other powers are being calculated with a window of about 100ms
- the battery is in units of percent and not voltage

data format
- brainwave powers @ ~10HZ
- Raw electrode votages @ ~400HZ
- the accelerometer and gyroscope is between 10HZ and 30HZ most often closer to 30HZ
- headband on and Horse Shoe indicators for each electrode I believe lower numbers indicate better contatct
- elements that are blinks and jaw clenches (unsure about the specific timing of the datatapoint realitive to the activity)

diffrent data files:
the data is split into diffrent data streams as described in the import data file

deduplication:
in the orignal export file data is duplicated if it hasnt been updated before another data stream is updated
we only store the time at which a data point first appears
