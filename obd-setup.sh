#!/bin/bash
macAddress="00:00:00:00:00:00" #withheld from Git repository

echo -e "power on" | bluetoothctl
sleep 2
echo -e "agent on" | bluetoothctl
sleep 2
echo -e "default-agent" | bluetoothctl
sleep 2
echo -e "scan on" | bluetoothctl
sleep 2
echo -e "pair ${macAddress}" | bluetoothctl
sleep 6
echo -e "trust ${macAddress}" | bluetoothctl
sleep 6
sudo rfcomm bind rfcomm0 ${macAddress}

sudo echo 1 > /mnt/oss-ramdisk/bluetooth-ready
