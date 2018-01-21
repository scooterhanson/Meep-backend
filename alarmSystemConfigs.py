import ConfigParser
import json
import time
import datetime
from alarmUtils import AlarmUtils


class AlarmSystemConfigs:
	def __init__(self, config_file):
		self.config_file = config_file
		self.system_configs = ''
		self.load_configs()
		#self.utils = AlarmUtils
		alarm_utils = AlarmUtils()
		self.last_loaded_time = alarm_utils.get_epoch_time()

	def load_configs(self):
		with open(self.config_file, 'r') as json_file:
                        data = json.load(json_file)
		self.system_configs = data
		json_file.close()
		alarm_utils = AlarmUtils()
		self.last_loaded_time = alarm_utils.get_epoch_time()

	def get_configs(self):
		return self.system_configs

	def update_configs(self):
		alarm_utils = AlarmUtils()
		self.last_loaded_time = alarm_utils.get_epoch_time()
		self.system_configs['system']['updated_date'] = epochtime
		with open(self.config_file, 'w') as json_file:
			json_file.write(json.dumps(self.system_configs, indent=4, sort_keys=True))
		json_file.close()
                msg = "UPDATED CONFIGS - "+datetime.datetime.now().strftime("%m-%d %H:%M:%S")

	def get_configUpdateTime(self):
		return self.system_configs['system']['updated_date']

	def check_configValue(self, section, key):
		return self.system_configs[section][key]

	def set_configValue(self, section, key, value):
		self.system_configs[section][key] = value
		self.update_configs()


