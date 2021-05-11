import board
import busio
import time
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import RPi.GPIO as GPIO 
from time import sleep
import os

try:
	i2c = busio.I2C(board.SCL, board.SDA)
	ads = ADS.ADS1115(i2c)
	ads.gain = 2

	GPIO.setwarnings(False) 
	GPIO.setmode(GPIO.BCM) #physical pin numbering
	GPIO.setup(14, GPIO.OUT, initial=GPIO.LOW)

	while(True):
		chan = AnalogIn(ads, ADS.P0)
		time.sleep(0.3)
		if chan.voltage < 1.0: #door open
			GPIO.output(14, GPIO.HIGH)
			os.system("echo 1 > /mnt/oss-ramdisk/door-open")
		else: #door closed
			GPIO.output(14, GPIO.LOW)
			os.system("echo 0 > /mnt/oss-ramdisk/door-open")

except KeyboardInterrupt:
	print("[E] Interrupt")
	exit(1)
except:
	print("[E] Error encountered while communicating with sensor.")
	os.system("echo 1 > /mnt/oss-ramdisk/error")
	exit(1)
