from gpiozero import LED
from time import sleep

relay1=LED(22) #car to battery input
relay2=LED(24) #NO relay (battery)
relay3=LED(23) #NC relay (vehicle input)

while True:
	sleep(2)
	with open("/mnt/oss-ramdisk/relay-status") as f:
		relayStatus=f.readline()

	if "0" in relayStatus:
		relay1.off()
		sleep(0.5)
		relay2.on()
		sleep(0.5)
		relay3.on()
	else: #car moving
		relay3.off()
		sleep(0.5)
		relay2.off()
		sleep(0.5)
		relay1.on()
