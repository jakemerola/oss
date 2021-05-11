import Adafruit_DHT
import sys
import time
import datetime
import os

sensor=Adafruit_DHT.DHT11
gpio=17
 
while True:
	humidity, temperature = Adafruit_DHT.read_retry(sensor, gpio) 
	if humidity is not None and temperature is not None:
		os.system("echo \"%s\" > /mnt/oss-ramdisk/temp-reading" % temperature )
