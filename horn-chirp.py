from gpiozero import LED
from time import sleep

horn=LED(5)
try:
	horn.on()
	sleep(1)
	horn.off()
except:
	horn.off() #prevent horn from staying on in event of error
