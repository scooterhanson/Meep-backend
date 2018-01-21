import RPi.GPIO as GPIO
from threading import Event
import time
GPIO.setmode(GPIO.BCM)

####
# This one is still a work in progress.  Nothing is hooked up here yet, but my plan is to trigger a strobe light and siren
# from a relay keyed off a GPIO pin.
####

class AlarmRelayControl:
	def __init__(self, pin):
		self.exit = Event()
		self.pin = pin
		GPIO.setup(pin, GPIO.OUT,)
		GPIO.output(pin,1)

	def trigger_relay(self, duration_seconds):
		GPIO.setup(self.pin, GPIO.OUT, )
		GPIO.output(self.pin,0) #Turn on Relay
		while not self.exit.is_set():
			time.sleep(1)	#need to figure out how the sleep and wait times play with each other here
			print('sleeping 1')
			self.exit.wait(duration_seconds)
			print('waiting')
		GPIO.output(self.pin,1) #Turn off relay
		GPIO.cleanup()

	#def interrupt_relay(signo, _frame):
	def interrupt_relay(self):
		self.exit.set()
		self.exit.clear()
