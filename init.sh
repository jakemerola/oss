#!/bin/bash

function spawn-processes() {
	echo 99999999999999 > /mnt/oss-ramdisk/timer-value
	echo 0 > /mnt/oss-ramdisk/timer-active

	#set sensor values then start sensor
	echo 0 > /mnt/oss-ramdisk/sensor-occupant-detected
	echo 0 > /mnt/oss-ramdisk/sensor-ready
	python3 sensor.py &
	sensorPID=$!
	echo "Started sensor subsystem with PID of ${sensorPID}"

	#door detection script
	echo 0 > /mnt/oss-ramdisk/door-open
	python3 door.py &
	doorPID=$!
	echo "Started door detection subsystem with PID of ${doorPID}"

	#temp sensor script
	echo 11 > /mnt/oss-ramdisk/temp-reading
	python3 temp.py &
	tempPID=$!
	echo "Started temperature sensing subsystem with PID of ${tempPID}"
}

cd /home/pi/oss/sys/

echo "Starting OSS in 5 seconds. Press Control+C to interrupt..."
read -t 5

#create ramdisk
sudo mkdir -p /mnt/oss-ramdisk
sudo mount -t tmpfs tmpfs /mnt/oss-ramdisk

#set permissions for ramdisk
sudo chmod -R 777 /mnt/oss-ramdisk

#set permissions for sensor
sudo chmod 777 /dev/ttyUSB0 /dev/ttyUSB1

#set relay values low
python3 relay-setup.py

#start reset button daemon
./reset-button-daemon.sh &

spawn-processes
echo "Done spawning processes"

#start bluetooth setup
./obd-setup.sh 

#start relay daemon
echo 0 > /mnt/oss-ramdisk/relay-status
python3 relay-daemon.py &

#program loop
while [ 1 ]; do
	echo "New loop, updating OBD"
	python3 obd-update.py

	#charge the system when the vehicle is moving and the vehicle cannot shut off
	if [ "$(cat /mnt/oss-ramdisk/obd-vehicle-moving)" == "1" ]; then
		echo 1 > /mnt/oss-ramdisk/relay-status
	else
		echo 0 > /mnt/oss-ramdisk/relay-status
	fi


	if [ "$(cat /mnt/oss-ramdisk/sensor-occupant-detected)" == "0" ] && [ "$(cat /mnt/oss-ramdisk/obd-vehicle-on)" == "0" ]; then
		echo "No occupant detected and vehicle is off. Now shutting down." 
		sudo shutdown
	fi

	if [ "$(cat /mnt/oss-ramdisk/sensor-occupant-detected)" == "1" ] && [ "$(cat /mnt/oss-ramdisk/obd-vehicle-moving)" == "0" ] && (( $(echo "($(cat /mnt/oss-ramdisk/temp-reading) > 32.0) || ($(cat /mnt/oss-ramdisk/temp-reading) < 4.4)" | bc -l) )); then

		echo "Occupant detected, vehicle not moving, unsafe conditions. Sounding alarm!" 
		echo "Alarm command goes here"
		#does this actually run continuously? use hair dryer to see if this keeps appearing
	fi

	if [ "$(cat /mnt/oss-ramdisk/sensor-occupant-detected)" == "1" ] && [ "$(cat /mnt/oss-ramdisk/door-open)" == "1" ]; then

		echo "Occupant detected and door open. Sending reminder" 
		python3 chime.py
		python3 push-notification-remind.py
		#echo "Waiting 5 minutes for occupant to leave"
		#sleep 300 
		echo "Waiting 30 seconds for occupant to leave (testing only, needs to be 5 min)"
		sleep 30 #in place so you don't get spam notification
	fi

	if [ "$(cat /mnt/oss-ramdisk/sensor-occupant-detected)" == "1" ] && [ "$(cat /mnt/oss-ramdisk/obd-vehicle-on)" == "0" ] && [ "$(cat /mnt/oss-ramdisk/timer-active)" == "0" ]; then

		echo "Occupant detected and car off. Setting timer because it hasn't been set yet." 
		python3 chime.py
		echo 1 > /mnt/oss-ramdisk/timer-active
		echo $(date +%s) > /mnt/oss-ramdisk/timer-value
	fi

	if [ "$(cat /mnt/oss-ramdisk/obd-vehicle-on)" == "1" ] && [ "$(cat /mnt/oss-ramdisk/timer-active)" == "1" ]; then

		echo "Vehicle moving and timer active. Stopping timer." 
		echo 0 > /mnt/oss-ramdisk/timer-active
		rm -f /mnt/oss-ramdisk/timer-value
	fi

	if [ "$(cat /mnt/oss-ramdisk/timer-active)" == "1" ] && [ "$(cat /mnt/oss-ramdisk/sensor-occupant-detected)" == "0" ]; then
		echo "Timer is running but occupant is no longer being detected (they left on their own?). Stopping timer." 
		echo 0 > /mnt/oss-ramdisk/timer-active
		rm -f /mnt/oss-ramdisk/timer-value
	fi

	if (( $(( $(date +%s) - $(cat /mnt/oss-ramdisk/timer-value) )) > 3600 )); then
		echo "More than an hour has elapsed. Sounding alarm!" 
		echo "Alarm command goes here"
	fi
done
