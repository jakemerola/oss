import serial
import sys
import os

SERIAL_PORT_NAME = "/dev/rfcomm0"
SERIAL_BAUD = 38400
SERIAL_PORT_TIMEOUT = 60
ELM_CONNECT_SETTLE_PERIOD = 5
ELM_CONNECT_TRY_COUNT = 5

def GetResponse(SerialCon, Data):
    SerialCon.write(Data)
    Response = ""
    ReadChar = 1
    while ReadChar != b'>' and ReadChar!= 0:
        ReadChar = SerialCon.read()
        if ReadChar != b'>':
            Response += str(ReadChar, 'utf-8')
    return Response.replace('\r', '\n').replace('\n\n', '\n')
    
port_connection = True

try:
    ELM327 = serial.Serial(SERIAL_PORT_NAME, SERIAL_BAUD)
    ELM327.timeout = SERIAL_PORT_TIMEOUT
    ELM327.write_timeout = SERIAL_PORT_TIMEOUT
except:
    port_connection = False
    print("Could not connect to port '"+ SERIAL_PORT_NAME + "'")
    
if(port_connection == True):
    Response = GetResponse(ELM327, b'01 0D\r')
    if "NO DATA" in Response: #Vehicle turned off
        os.system("echo 0 > /mnt/oss-ramdisk/obd-vehicle-on")
        os.system("echo 0 > /mnt/oss-ramdisk/obd-vehicle-moving")
    elif '41 0D 00' in Response: #Vehicle not moving
        os.system("echo 1 > /mnt/oss-ramdisk/obd-vehicle-on")
        os.system("echo 0 > /mnt/oss-ramdisk/obd-vehicle-moving")
    else:
        os.system("echo 1 > /mnt/oss-ramdisk/obd-vehicle-on")
        os.system("echo 1 > /mnt/oss-ramdisk/obd-vehicle-moving")
