import calendar
import os
import time

class AlarmHeartbeat:
	def __init__(self, heartbeat_path, alarm_config_path):
		self.heartbeat_path = heartbeat_path
		self.alarm_config_path = alarm_config_path

        def update_heartbeat_file(self):
                epoch_time = calendar.timegm(time.gmtime())
                cur_config_mtime = os.stat(self.alarm_config_path).st_mtime
                contents = str(epoch_time)
                file = open(self.heartbeat_path, "w")
                file.write(contents)
                file.close()
