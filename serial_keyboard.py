import serial
from cobs import cobs
import struct
from crccheck.crc import CrcModbus
from key_layout import *
class SerialKeyboard(object):
	def __init__(self, com_port, baud_rate=9600, time_pressed=100, time_between_presses=20):
		self.serial = serial.Serial(com_port, baud_rate)
		self.time_pressed = time_pressed
		self.time_between_presses = time_between_presses
	
	def press(self, keys, modifiers=0, time_pressed=None, time_between_presses=None):
		if isinstance(keys, int):
			keys=[keys]
		if len(keys)>=6:
			raise ValueError('Too many keys pressed at once! The USB max is 6')
		if time_pressed is None:
			time_pressed = self.time_between_presses
		if time_between_presses is None:
			time_between_presses = self.time_between_presses
		self.send(keys, modifiers, time_pressed // 10, time_between_presses // 10)
	
	def hold(self, keys, modifiers=0):
		if isinstance(keys, int):
			keys=[keys]
		self.send(keys, modifiers, 0, 0xFF)

	def release(self,  time_between_presses=None):
		if isinstance(keys, int):
			keys=[keys]
		if time_between_presses is None:
			time_between_presses = self.time_between_presses
		self.send([], 0, 0xFF, time_between_presses//10)


	def send(self, keys, modifiers, raw_time_pressed, raw_time_between_presses):
		data=struct.pack('BBB'+('B'*len(keys)),modifiers,raw_time_pressed ,raw_time_between_presses ,*tuple(keys))
		crc = CrcModbus()
		crc.process(list(data))

		encoded_data = crc.finalbytes() + data
		encoded_packet = cobs.encode(encoded_data)
		ser = self.serial
		ser.write(encoded_packet+b'\0')
		result = ser.read(1)
		if result!=b'\x00':
			message=ser.read_until()
			raise ValueError("Got an error back from the device: {:02x}: {}".format(ord(result),message))




if __name__=='__main__':
	sk=SerialKeyboard('/dev/ttyACM0')
	sk.press([KEY_7])
