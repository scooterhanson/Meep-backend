import json
import subprocess
from twilio.rest import TwilioRestClient
from alarmUtils import AlarmUtils
from alarmSystemConfigs import AlarmSystemConfigs
from alarmSiren import AlarmSiren



class AlarmNotifier:
        def __init__(self, config_file, alarm_system_configs, alarm_sensor_dict):
                self.config_file = config_file
                self.notification_configs = ''
                self.load_configs()
		self.sensors = alarm_sensor_dict
		self.alarm_siren = AlarmSiren()
                alarm_utils = AlarmUtils()
		self.alarm_system_configs = alarm_system_configs
                self.lastLoadedTime = alarm_utils.get_epoch_time()
		if self.notification_configs['notifiers']['sms']['enabled'] == True:
			self.account = self.notification_configs['notifiers']['sms']['account']
			self.token = self.notification_configs['notifiers']['sms']['token']
			self.from_num = self.notification_configs['notifiers']['sms']['from_num']
			self.to_num = self.notification_configs['notifiers']['sms']['to_num']

	def load_configs(self):
                with open(self.config_file, 'r') as json_file:
                        data = json.load(json_file)
                self.notification_configs = data
                json_file.close()

	def update_system_configs(self, new_system_configs):
		self.alarm_system_configs = self.alarm_system_configs.update_config_data(new_system_configs)

	def do_notify(self, sensor, pin, state, msg):
                self.send_sms_alert(msg, sensor, pin, state)
		self.play_sound(sensor, pin, state)
		self.sound_siren(sensor, pin, state)

        def launch_player(self, sound_file):
                self.set_volume_max()
		cmd_play = self.notification_configs['notifiers']['audio']['subprocess_utility']
                subprocess.call([cmd_play,sound_file])

        def set_volume_max(self):
		cmd_volume_max = self.notification_configs['notifiers']['audio']['set_volume_string']
		cmd_chunks = cmd_volume_max.split("|")
                subprocess.call(cmd_chunks)

        def play_sound(self, sensor, pin, state):
                alert_audio_path = self.notification_configs['notifiers']['audio']['path']
		sound_file = ''
		sensor_type = ''
		str_pin = str(pin)
		if(str_pin in self.sensors and state == 'OPEN'):
			sensor_type = self.sensors[str_pin].type
			if(self.alarm_system_configs.check_configValue('beep', sensor_type.lower()) == True):
				sound_file = alert_audio_path + self.sensors[str_pin].alert_sound
                elif(sensor == 'ALARM' and state == 'ON'):
                        sound_file = alert_audio_path+'alert-armed.wav'
                elif(sensor == 'ALARM' and state == 'OFF'):
                        sound_file = alert_audio_path+'alert-disarmed.wav'
                elif(sensor == 'STARTING'):
                        sound_file= alert_audio_path+'starting_alarm.wav'
                if(sound_file != ''):
                        self.launch_player(sound_file)

        def send_sms_alert(self, msg, sensor, pin, state):
		str_pin = str(pin)
		if(str_pin in self.sensors and state == 'OPEN'):
			sensor_type = self.sensors[str_pin].type
			sms_config = self.alarm_system_configs.check_configValue('notify', sensor_type.lower())
			if(sms_config == True):
				if(sms_config == True):
					self.dispatch_sms(msg)

	def sound_siren(self,sensor, pin, state):
		str_pin = str(pin)
		if(str_pin in self.sensors and state == 'OPEN'):
			sensor_type = self.sensors[str_pin].type
			if(self.alarm_system_configs.check_configValue('siren', sensor_type.lower()) == True):
				self.alarm_siren.trigger_siren()

	def dispatch_sms(self, msg):
		client = TwilioRestClient(account=self.account,
			token=self.token)
		client.messages.create(from_=self.from_num,
			to=self.to_num,
			body=('%s' %(msg)))
