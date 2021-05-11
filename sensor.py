import serial                    #talk to com ports
from collections import deque    #shift register looking for sync pattern
import numpy as np               #dumping data
import time                      #threading
import struct                    #casting bytes to float
import traceback                 #displaying full exception errors while still handling cleanup code
import os			 #controlling gpio

global_cliPort='/dev/ttyUSB0'
global_cliBaud=115200
global_dataPort='/dev/ttyUSB1'
global_dataBaud=115200
global_configFilePath='config.cfg'
global_cliEncoding='utf-8'
global_ramfile='/dev/shm/sensordata.txt'

global_ansiColors=True

class PrintDecisionVector():
	def __init__(self, data):
		for zone in range(0, 6):
			print("%s " % data[zone]["percent"], end="")

		print("")

class Main:
	def __init__(self):
		os.system("echo 0 > /mnt/oss-ramdisk/sensor-ready")
		try:
			self.sendConfigObj=CliPort()
			try:	
				self.sendConfigObj.openPort(global_cliPort, global_cliBaud)
			except serial.serialutil.SerialException:
				printError("Could not open serial port %s. Please check permissions." % global_cliPort)
				self.quit(1)

			#now VODDemo:/> prompt is up and ready for input
			printPrompt("Sending configuration file to the sensor...")
			try:
				self.sendConfigObj.sendConfigFile(global_configFilePath)
			except FileNotFoundError:
				printError("Configuration file %s not found." % global_configFilePath)
				self.quit(1)
			except serial.serialutil.SerialTimeoutException:
				printError("Serial timed out.") 
				self.quit(1)


			#open com port to collect data
			self.dataObj=DataPort()
			try:
				self.dataObj.openPort(global_dataPort, global_dataBaud)
			except serial.serialutil.SerialException:
				printError("Could not open serial port %s. Please check permissions." % global_dataPort)
				self.quit(1)

			#start data collection
			print("Ready")
			os.system("echo 1 > /mnt/oss-ramdisk/sensor-ready")

			self.dataObj.loop()
			self.quit(0)

		except KeyboardInterrupt:
			printError("Keyboard Interrupt")
			self.quit(1)

		except Exception as ex:
			printError("Exception: %s" % ex)
			printError(traceback.format_exc())
			printStatus("Running cleanup code...")
			self.quit(1)

	def quit(self, exitCode):
		try:
			for x in range(0, 5):
				tempString=self.sendConfigObj.sendStopCommand()
				if "Done" in tempString:
					printOutput(tempString)
					break
			else:
				printWarning("Sent 5 sensorStop commands but sensor did not respond.")
		except Exception as ex:
			printWarning("Unable to send stop command.")

		try:
			self.sendConfigObj.closePort()
		except Exception as ex:
			printWarning("Unable to send stop command.")
		
		try:
			self.dataObj.closePort()
		except Exception as ex:
			printWarning("Unable to send stop command.")

		exit(exitCode)

class CliPort:

	def openPort(self, port, baud):
		self.serialObj=serial.Serial(port=port, baudrate=baud, timeout=0.5)

	def closePort(self):
		self.serialObj.close()

	def sendStopCommand(self):
		self.serialObj.write("sensorStop\n".encode(global_cliEncoding))
		return (self.serialObj.read_until(b'>').decode(global_cliEncoding).rstrip())


	def spinWaitReset(self):
		spinQueueLength=20
		spinQueue=deque(maxlen=spinQueueLength)
		while 1:
			spinQueue.append(self.serialObj.read(1)) #do not pop anything from this as it can cause data loss 
			tempSpinQueue=spinQueue.copy()
			lineString=""
			try: #necessary because tempSpinQueue throws an exception if queue is empty
				for x in range(0, spinQueueLength):
					lineString += tempSpinQueue.popleft().decode(global_cliEncoding)
			except:
				pass

			if "VODDemo:/>" in lineString:
				return(12)

	def sendConfigFile(self, path):
		with open(path, 'r') as configFile:
			for line in configFile:
				#send out bits first, then listen
				self.serialObj.write(line.encode(global_cliEncoding))
				printOutput(self.serialObj.read_until(b'>').decode(global_cliEncoding).rstrip())
				time.sleep(0.1)

class DumpRawData:
	def __init__(self, data):
		numpyObj=np.array(data)
		np.savetxt(global_ramfile, numpyObj)

class DataPort:
	def openPort(self, port, baud):
		self.serialObj=serial.Serial(port=port, baudrate=baud, timeout=0.5)

	def closePort(self):
		self.serialObj.close()

	def spinWaitSync(self):
		watchdog=0
		syncQueue=deque(maxlen=8)
		while 1:
			watchdog+=1
			if (watchdog > 4294967296):
				raise Exception("Timed out while waiting for sync")

			syncQueue.append(self.serialObj.read(1))
			try: #required because deque raises exception if elements not present
				if ((syncQueue.index(b'\x02') == 0) \
					and (syncQueue.index(b'\x01') == 1) \
					and (syncQueue.index(b'\x04') == 2) \
					and (syncQueue.index(b'\x03') == 3) \
					and (syncQueue.index(b'\x06') == 4) \
					and (syncQueue.index(b'\x05') == 5) \
					and (syncQueue.index(b'\x08') == 6) \
					and (syncQueue.index(b'\x07') == 7)):
					return(12)
			except:
				pass

	def loop(self):
		occupantDetected=False
		print("Starting test...")

		while True:
			self.spinWaitSync()
			assert (self.spinWaitSync() == 12), "spinWaitSync() did not return 12"
			numberOfBytes, = struct.unpack('<I', self.serialObj.read(4))
			platform,  = struct.unpack('<I', self.serialObj.read(4))
			frameNumber,  = struct.unpack('<I', self.serialObj.read(4))
			timeCpuCycles,  = struct.unpack('<I', self.serialObj.read(4))
			numDetectedObj,  = struct.unpack('<I', self.serialObj.read(4))
			numTLVs,  = struct.unpack('<I', self.serialObj.read(4))

			#printStatus("[ %s ] bytes=%s, frame=%s, packets (TLVs)=%s" % (timeCpuCycles, numberOfBytes, frameNumber, numTLVs))

			for x in range(0, numTLVs):

				tlvType, = struct.unpack('<I', self.serialObj.read(4))
				tlvLength, = struct.unpack('<I', self.serialObj.read(4))

				self.heatMap=[[0 for x in range(48)] for y in range(64)]
				if (tlvType == 8): #azimuth heat map (size should be 48x64x2 or 48x64x4)
					for row in range(0, 64):
						for col in range(0, 48):
							if (tlvLength == 6144):
								#unsigned short 2 bytes
								self.heatMap[row][col], = struct.unpack('<H', self.serialObj.read(2)) 
							elif (tlvLength == 12288):
								#float 4 bytes
								self.heatMap[row][col], = struct.unpack('<f', self.serialObj.read(4))
							else:
								raise ValueError("TLV length not 6144 or 12288")


				elif (tlvType == 9):
					raise ValueError("TLV type 9 not implemented yet")

				elif (tlvType == 10): #decision vector
					#number of zones based on length of packet/12
					assert ((tlvLength/12).is_integer())
					numberZones=int(tlvLength/12)
					self.decisionVector=[]

					for zone in range(0, numberZones): #should be 0 to 6 with current config file
						self.decisionVector.append({
							"percent": 0,
							"power": 0,
							"rangeIdx": 0,
							"azimuthIdx": 0 })

						#struct values like <f and <H: see https://docs.python.org/3/library/struct.html
						self.decisionVector[zone]["percent"], = struct.unpack('<f', self.serialObj.read(4))
						self.decisionVector[zone]["power"], = struct.unpack('<f', self.serialObj.read(4))
						self.decisionVector[zone]["rangeIdx"], = struct.unpack('<H', self.serialObj.read(2))
						self.decisionVector[zone]["azimuthIdx"], = struct.unpack('<H', self.serialObj.read(2))

					for zone in range(0, 6):
						if (float(self.decisionVector[zone]["percent"]) > 0.1):
							os.system("echo 1 > /mnt/oss-ramdisk/sensor-occupant-detected")
						else:
							os.system("echo 0 > /mnt/oss-ramdisk/sensor-occupant-detected")

				else:
					raise ValueError("TLV type not 8, 9, or 10")


def printError(message):
	if (global_ansiColors):
		print("\033[31m[E] %s\033[0m" % message)
	else:
		print("[E] %s" % message)

def printStatus(message):
	print("%s" % message)

def printWarning(message):
	if (global_ansiColors):
		print("\033[33m[E] %s\033[0m" % message)
	else:
		print("[E] %s" % message)

def printPrompt(message):
	print("%s" % message)

def printOutput(message):
	pass
#	if (global_ansiColors):
#		print("\033[36m%s\033[0m" % message)
#	else:
#		print("%s" % message)

Main()
