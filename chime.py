from gpiozero import LED
from time import sleep

chime = LED(16)
for i in range(0, 2):
    chime.on()
    sleep(0.11)
    chime.off()
    sleep(0.11)
