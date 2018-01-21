import calendar
import time

class AlarmUtils(object):
	def __init__(self):
		pass

	def get_epoch_time(self):
		epoch_time = calendar.timegm(time.gmtime())
		return epoch_time
