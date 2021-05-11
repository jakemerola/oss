#!/bin/bash

echo "25" > /sys/class/gpio/export
echo "in" > /sys/class/gpio/gpio25/direction

echo "Reset button monitor"

while [ 1 ]; do
	if [ "$(cat /sys/class/gpio/gpio25/value)" == "1" ]; then
		echo "Shutting down"
		sudo shutdown now
	fi
done
