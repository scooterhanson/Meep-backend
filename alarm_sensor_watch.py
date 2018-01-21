import datetime
import subprocess
import os
import thread
import time
import json
import calendar
import ConfigParser
import RPi.GPIO as GPIO
from twilio.rest import TwilioRestClient
from pymongo import MongoClient
#import sys
#import stat
#import requests

class AlarmNotifier:
	def __init__(self, configs):
		self.account = 'ACd724d29b05d588c9f8b14d1cc3e85747'
		self.token = '2085003d7b7a0b16300aa49dad588caf'
		self.from_num = '2407822119'
		self.to_num = '2403940229'
		self.configs = configs

	def launch_player(self, sound_file):
		self.set_volume_max()
		subprocess.call(["aplay",sound_file])

	def set_volume_max(self):
		subprocess.call(["amixer","set","PCM","100%"])

	def play_sound(self, sensor, pin, state):
		alert_audio_path = '/home/pi/bin/alarm/audio/'
		sound_file=''
		if((('DOOR' in sensor or 'BAY' in sensor) and configs['beep_on_door']) or ('MOTION' in sensor and configs['beep_on_motion'])):
			if(state == 'OPEN' or state == 'MOTION DETECTED'):
				sound_file = alert_audio_path+'alert-'+sensor.replace(' ','_').lower()+'.wav'
			elif(state == 'NOT-CLOSED'):
				sound_file=alert_audio_path+'alert-door_not_closed.wav'
		elif(sensor == 'ALARM' and state == 'ON'):
			sound_file = alert_audio_path+'alert-armed.wav'
		elif(sensor == 'ALARM' and state == 'OFF'):
			sound_file = alert_audio_path+'alert-disarmed.wav'
		elif(sensor == 'STARTING'):
			sound_file= alert_audio_path+'starting_alarm.wav'
		elif('PANEL' in sensor):
			sound_file = alert_audio_path+'alert-alarm_panel.wav'
		if(sound_file != ''):
			print('playing sound for %s - %s' %(sensor,state))
			#thread.start_new_thread( self.launch_player, (sound_file, ) )
			self.launch_player(sound_file)



	def send_sms_alert(self, msg, sensor, pin, state):
		if((('DOOR' in sensor or 'BAY' in sensor or 'PANEL' in sensor) and configs['notify_on_door']) or ('MOTION' in sensor and configs['notify_on_motion']) or ('CONFIG' in sensor)):
			client = TwilioRestClient(account=self.account,
				token=self.token)
			client.messages.create(from_=self.from_num,
				to=self.to_num,
				body=('%s' %(msg)))



class AlarmSiren:
	def play_siren(self, sensor, pin, state):
		pass
		#print('PLAY SIREN')
	def stop_siren(self):
		pass
		#print('STOP SIREN')


class AlarmLogger:
	def log_alert(self, msg, sensor, pin, state):
		dateNow = datetime.datetime.now().strftime("%m-%d-%y %H:%M:%S")
		params = {}
		params.update({'msg': msg, 'state': state, 'sensor': sensor, 'pin': pin, 'date': dateNow})
		jsonParams = json.dumps(params)
		client = MongoClient('localhost',27017)
		db = client.alarm
		items = db.items
		print('inserting %s' %(params))
		item_id = items.insert(params)
		client.close()
		self.log_prune()

	def log_prune(self):
		client = MongoClient('localhost',27017)
		db = client.alarm
		items = db.items
		s = "10 days ago"
		parsed_s = [s.split()[:2]]
		time_dict = dict((fmt,float(amount)) for amount,fmt in parsed_s)
		dt = datetime.timedelta(**time_dict)
		past_time = datetime.datetime.now() - dt
		parsed_past_time = str(past_time)[:9]
		fmt_past_time = past_time.strftime("%m-%d-%y 00:00:00")
		items = db.items.remove({"date": {'$lt' : fmt_past_time}})
		client.close() 






###########
# UTILITIES
###########
def configToBool(config,section, key):
	sval = config.get(section,key)
	if(sval == ''):
	  sval = 0
	bval = bool(int(sval))
	return bval

def getConfigs(fpath):
	config = ConfigParser.ConfigParser()
	config.readfp(open(fpath))
	configs = {}
	time.sleep(1.7) #try to avoid a race with the alarmUpdater endpoint
	configs.update({'notify_on_door': configToBool(config,'Notify','door')})
	configs.update({'notify_on_motion': configToBool(config,'Notify', 'motion')})
	configs.update({'beep_on_door': configToBool(config,'Beep', 'door')})
	configs.update({'beep_on_motion': configToBool(config,'Beep', 'motion')})
	configs.update({'siren_on_door': configToBool(config,'Siren', 'door')})
	configs.update({'siren_on_motion': configToBool(config,'Siren', 'motion')})
	configs.update({'updated_date': config.get('System', 'updated_date')})
	configs.update({'alarm_running': config.get('Alarm', 'running')})
	configs.update({'update_interval_sec': 3.3})
	return configs

def updateConfigs(fpath, section, name, value):
	config = ConfigParser.RawConfigParser()
	config.readfp(open(fpath))
	config.set(section, name, value)
	with open(fpath, 'wb') as configfile:
		config.write(configfile)
	configs = {}
	configs = getConfigs(fpath)
	cfgNotifier = AlarmNotifier(configs)
	msg = "Configs updated - "+datetime.datetime.now().strftime("%m-%d %H:%M:%S")
	cfgNotifier.send_sms_alert(msg, "CONFIG", 0, "0")
	return configs


def updateHeartbeatFile(fpath, contents):
	file = open(fpath, "w")
	file.write(contents)
	file.close()

heartbeat_path = "/var/www/html/alarm_heartbeat.html"
alarm_config_path = "/etc/alarm.cfg"
#sensor_config_path = "/etc/alarm-sensors.cfg"
configs = getConfigs(alarm_config_path)
GPIO.setmode(GPIO.BCM)
#sensors = {'18':'PATIO DOOR', '23':'FRONT DOOR', '25':'GARAGE DOOR', '24':'SIDE DOOR'}
#sensors = {'18':'FRONT DOOR', '23':'PATIO DOOR', '25':'GARAGE DOOR', '24':'SIDE DOOR', '20':'LIVING ROOM MOTION', '21':'FAMILY ROOM MOTION'}
sensors = {'12':'ALARM PANEL','18':'PATIO DOOR', '23':'FRONT DOOR', '25':'GARAGE DOOR', '24':'SIDE DOOR', '20':'GARAGE BAY 1', '21':'GARAGE BAY 2'}
status = ""
alarm_running = 0

print('CONFIGS LOADED')

notifier = AlarmNotifier(configs)
log = AlarmLogger()
siren = AlarmSiren()

def handle_event(alert_sensor, pin, alert_state, alert_msg):
	global log
	global notifier
	global siren
	log.log_alert(alert_msg, alert_sensor, pin, alert_state)
	if(alert_state != 'CLOSED'):
		notifier.send_sms_alert(alert_msg, alert_sensor, pin, alert_state)
	notifier.play_sound(alert_sensor, pin, alert_state)
	siren.play_siren(alert_sensor, pin, alert_state)
	print ('handle_event: '+alert_msg)



def thread_watch_status():
	global status
	global configs
	global alarm_running
	default_sleep = 1.2 

#	check alarm running status
	prev_config_mtime = os.stat(alarm_config_path).st_mtime
	prev_alarm_running = configs['alarm_running']
	alert_date = datetime.datetime.now().strftime("%m-%d %H:%M:%S")
	alarm_running = configs['alarm_running']

	while 1:
		#print('watching status')
		time.sleep(default_sleep)
		epoch_time = calendar.timegm(time.gmtime())
		cur_config_mtime = os.stat(alarm_config_path).st_mtime
		updateHeartbeatFile(heartbeat_path, str(epoch_time))
		if(int(cur_config_mtime) != int(prev_config_mtime)):
			configs = updateConfigs(alarm_config_path,'System','updated_date', epoch_time)
			prev_config_mtime = os.stat(alarm_config_path).st_mtime

			# Check to see if the alarm has been turned off
			# configs = getConfigs(alarm_config_path)
			alarm_running = configs['alarm_running']
			if(alarm_running != prev_alarm_running):
				prev_alarm_running = alarm_running
				if(alarm_running != "1"):
					notifier.play_sound('ALARM',0,'OFF')
					print('Disarmed')
					continue
				elif(alarm_running == "1"):
					notifier.play_sound('ALARM',0,'ON')
					print('Armed')
			elif(configs['alarm_running'] != "1"):
				continue
			print('Refreshed Configs - %s' %(epoch_time))

def thread_watch_pin( thread_name, pin):
	global sensors
	global configs
	global alarm_config_path
	global alarm_running

	log = AlarmLogger()
	alert_sensor = sensors['%s' %(pin)]
	GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	prev_state = GPIO.input(pin)
	pin_state = GPIO.input(pin)
	alert_date_raw = datetime.datetime.now()
	alert_date = alert_date_raw.strftime("%m-%d %H:%M:%S")
	time_since_last_alert = 0
	sensor_open_threshold_sec = 120 #2 minutes until reminder goes off

	if(pin_state == GPIO.HIGH):
		alert_state = 'OPEN'
	elif(pin_state == GPIO.LOW):
		alert_state = 'CLOSED'
	alert_msg = 'INITIALIZING - %s - %s - %s' %(alert_sensor, alert_state, alert_date)
	log.log_alert(alert_msg, alert_sensor, pin, alert_state)
	while 1:
		time.sleep(1.5)
		time_since_last_alert = time_since_last_alert+1
		#print(thread_name+" - active");
		try:
			if(not bool(alarm_running)):
				continue
			#print('running %s' %(alarm_running))
			pin_state = GPIO.input(pin)
			#if(pin == 21):
			# print(thread_name+' - pin: '+str(pin)+' -- state: '+str(pin_state)+' -- prev state: '+str(prev_state))
			if(prev_state == GPIO.LOW and pin_state == GPIO.HIGH):
				alert_date = datetime.datetime.now().strftime("%m-%d %H:%M:%S")
				if('DOOR' in alert_sensor or 'BAY' in alert_sensor or 'PANEL' in alert_sensor):
					alert_state = 'OPEN'
				elif('MOTION' in alert_sensor):
					alert_state = 'MOTION DETECTED'
				alert_msg = '%s - %s - %s' %(alert_sensor, alert_state, alert_date)
				handle_event(alert_sensor, pin, alert_state, alert_msg)
				prev_state = GPIO.HIGH
				time_since_last_alert = 0
				if('MOTION' in alert_sensor):
					prev_state = GPIO.LOW
					time.sleep(30)
				continue
			elif(prev_state == GPIO.HIGH and pin_state == GPIO.LOW):
				alert_date = datetime.datetime.now().strftime("%m-%d %H:%M:%S")
				if('DOOR' in alert_sensor or 'BAY' in alert_sensor or 'PANEL' in alert_sensor):
					alert_state = 'CLOSED'
					alert_msg = '%s - %s - %s' %(alert_sensor, alert_state, alert_date)
					handle_event(alert_sensor, pin, alert_state, alert_msg)
				prev_state = GPIO.LOW
				time_since_last_alert = 0
				continue
			elif(prev_state == pin_state):
				#if(pin == 21):
				#	 print('SENSOR: %s -- STATE: %s -- TIME SINCE LAST ALERT: %s' %(alert_sensor, alert_state, time_since_last_alert))
				if(prev_state == GPIO.HIGH):
					#if(pin == 21):
		  				#print('prev state was high.	still high')
					#print('WAITING TO TRIGGER DOOR STILL OPEN ALERT  --  %s / %s' %(time_since_last_alert, sensor_open_threshold_sec))
					if((int(time_since_last_alert) == int(sensor_open_threshold_sec)) or (int(time_since_last_alert) == int(sensor_open_threshold_sec * 3))):
						print('DOOR OPEN TOO LONG')
						alert_date = datetime.datetime.now().strftime("%m-%d %H:%M:%S")
						notifier = AlarmNotifier(configs)
						msg = "%s HAS BEEN OPEN FOR AT LEAST %s MINUTES... - %s" %(alert_sensor,(sensor_open_threshold_sec/60), alert_date)
						notifier.send_sms_alert(msg, alert_sensor, 0, "0")
						notifier.play_sound('DOOR',0,'NOT-CLOSED')
				continue
		except KeyboardInterrupt:
		   GPIO.cleanup()		# clean up GPIO on CTRL+C exit
		   GPIO.wait_for_edge(pin, GPIO.FALLING)
		   print "\nResetting"
		   continue



try:
	#print('playing sound for starting up')
	notifier.play_sound('STARTING',0,'ON')
	print(str(len(sensors)) + ' SENSORS TO LOAD')
	for key,val in sensors.iteritems():
		thread_name = 'thread_%s' %(key)
		thread_pin = int(key)
		print ("STARTING SENSOR ON %s" %(val))
		time.sleep(1.1)
		thread.start_new_thread( thread_watch_pin, (thread_name, thread_pin, ) )
	thread.start_new_thread( thread_watch_status, () )
except KeyboardInterrupt:
	GPIO.cleanup()
except Exception as e:
	#print "Error: unable to start thread"
	print str(e)
while 1:
	pass
GPIO.cleanup()			 # clean up GPIO on normal exit
