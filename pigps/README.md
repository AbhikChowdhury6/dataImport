###getting the gps pps setup on a pi 5
basically using this tut - https://austinsnerdythings.com/2025/02/14/revisiting-microsecond-accurate-ntp-for-raspberry-pi-with-gps-pps-in-2025/


sudo apt update
sudo apt upgrade -y
sudo apt install pps-tools gpsd gpsd-clients chrony -y

sudo bash -c "echo 'dtoverlay=pps-gpio,gpiopin=18' >> /boot/firmware/config.txt"
sudo bash -c "echo 'pps-gpio' >> /etc/modules"
sudo reboot

lsmod | grep pps
sudo ppstest /dev/pps0

edit
sudo nano /etc/default/gpsd

# USB might be /dev/ttyACM0
# serial might be /dev/ttyS0
# on raspberry pi 5 with raspberry pi os based on debian 12 (bookworm)
DEVICES="/dev/ttyACM0 /dev/pps0"

# -n means start without a client connection (i.e. at boot)
GPSD_OPTIONS="-n"

# also start in general
START_DAEMON="true"

# Automatically hot add/remove USB GPS devices via gpsdctl
USBAUTO="true"

run
sudo reboot

to look at gps traits
cgps


add these lines to a few lines in by the other server directives
sudo nano /etc/chrony/chrony.conf
# SHM refclock is shared memory driver, it is populated by GPSd and read by chrony
# it is SHM 0
# refid is what we want to call this source = NMEA
# offset = 0.000 means we do not yet know the delay
# precision is how precise this is. not 1e-3 = 1 millisecond, so not very precision
# poll 0 means poll every 2^0 seconds = 1 second poll interval
# filter 3 means take the average/median (forget which) of the 3 most recent readings. NMEA can be jumpy so we're averaging here
refclock SHM 0 refid NMEA offset 0.000 precision 1e-3 poll 0 filter 3

# PPS refclock is PPS specific, with /dev/pps0 being the source
# refid PPS means call it the PPS source
# lock NMEA means this PPS source will also lock to the NMEA source for time of day info
# offset = 0.0 means no offset... this should probably always remain 0
# poll 3 = poll every 2^3=8 seconds. polling more frequently isn't necessarily better
# trust means we trust this time. the NMEA will be kicked out as false ticker eventually, so we need to trust the combo
refclock PPS /dev/pps0 refid PPS lock NMEA offset 0.0 poll 3 trust

# also enable logging by uncommenting the logging line
log tracking measurements statistics

run
sudo systemctl restart chrony

check (even though it didn't say pps was working even though it was being used)
watch -n 1 chronyc sources

i just eyeball the the average of the last field for NEMA above and put it in SHM 0
sudo nano /etc/chrony/chrony.conf
sudo systemctl restart chrony


for timing metrics
watch -n 1 chronyc tracking



### now for pointing other computers to it
on the pi
sudo nano /etc/chrony/chrony.conf
allow 10.0.0.0/24
sudo systemctl restart chronyd



on the other computer
#sudo apt update
sudo apt install chrony -y


sudo nano /etc/chrony/chrony.conf

add
server 10.0.0.11 iburst minpoll 3 maxpoll 3 prefer

sudo systemctl restart chrony


### getting the gps better
i wasn't getting good reception using my adafruit module, so i switched to a sparkfun M9N
out of the box the M9N was able to connect to a bunch of different sattelite networks and that helped a bunch
even with my updated settings i only get 1 or 2 good gps signals the rest are from other networks
(i'm in a house with a metallic insulation layer)


i went on my windows computer (*gasp*) and opened up u-center

I'm having this problem where i can't seem to configure parameters that don't have a default
so I was able to configure
- PMS or CFG-PM operate mode to full power
- NAV5 or CFG-NAVSPG dynamics model to be stationary 


what i didn't seem able to set that i think would be helpful was 
- TMODE fixed and all the info about my location



