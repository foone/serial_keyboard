import serial
from cobs import cobs
import struct
from crccheck.crc import CrcModbus
from key_layout import *


MOUSE_LEFT=1
MOUSE_MIDDLE=4
MOUSE_RIGHT=2
MOUSE_BACK=8
MOUSE_FORWARD=16
MOUSE_BUTTONS=(MOUSE_LEFT, MOUSE_MIDDLE, MOUSE_RIGHT, MOUSE_BACK, MOUSE_FORWARD)

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

	def release(self):
		self.send([], 0, 0xFF, 0)


	def send(self, keys, modifiers, raw_time_pressed, raw_time_between_presses):
		data=struct.pack('BBB'+('B'*len(keys)),modifiers,raw_time_pressed ,raw_time_between_presses ,*tuple(keys))
		self.send_raw_data(data)

	def send_raw_data(self, data):
		crc = CrcModbus()
		crc.process([ord(x) for x in data])

		encoded_data = buffer(crc.finalbytes() + data)
		encoded_packet = cobs.encode(encoded_data)
		ser = self.serial
		ser.write(encoded_packet+'\0')
		result = ser.read(1)
		if result!='\x00':
			message=ser.read_until()
			raise ValueError("Got an error back from the device: {:02x}: {}".format(ord(result),message))

	def click(self, button=0, time_pressed=None, time_between_presses=None):
		button_mask = MOUSE_BUTTONS[button]
		if time_pressed is None:
			time_pressed = self.time_pressed
		if time_between_presses is None:
			time_between_presses = self.time_between_presses
		return self.mouse_buttons(button_mask, time_pressed // 10, time_between_presses // 10)

	def mouse_buttons(self, button_mask, raw_time_pressed, raw_time_between_presses):
		data=struct.pack('BBB5s', button_mask, raw_time_pressed, raw_time_between_presses, 'click')
		self.send_raw_data(data)

	def move(self, dx, dy):
		data=struct.pack('BBB5sbb',0, 0, 0, 'mouse', dx, dy)
		self.send_raw_data(data)
		


if __name__=='__main__':
	sk=SerialKeyboard('COM8')
	import time 
	#time.sleep(3)
	sk.move(0,-10)
