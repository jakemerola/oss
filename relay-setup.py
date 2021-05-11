from gpiozero import LED
from time import sleep

relay1=LED(22) #car to battery input
relay2=LED(24) #NO relay (battery)
relay3=LED(23) #NC relay (vehicle input)

relay1.off()
sleep(0.5)
relay2.off()
sleep(0.5)
relay3.off()
