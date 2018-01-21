import datetime
import time
import RPi.GPIO as GPIO
import os
from alarmSensorConfigs import AlarmSensorConfigs
from alarmNotifier import AlarmNotifier
from alarmLogger import AlarmLogger
from alarmSystemConfigs import AlarmSystemConfigs
from alarmHeartbeat import AlarmHeartbeat


print('')
print('******************')
print('INITIALIZING ALARM')
print('******************')
print('')

# Set GPIO pin mode
GPIO.setmode(GPIO.BCM)


heartbeat_path = "/var/www/html/alarmHeartbeat.html"
alarm_config_path = "/etc/alarm.cfg"
system_config_file = 'system.json'
notifications_config_file = 'notifiers.json'
sensors_config_file = 'sensors.json'
system_config_mtime = os.stat(system_config_file).st_mtime

sensor_configs = AlarmSensorConfigs(sensors_config_file)
sensor_dict = sensor_configs.get_sensor_dict()
sensor_states = {}
sensor_names = {}

alarm_system_configs = AlarmSystemConfigs(system_config_file)
alarm_heartbeat = AlarmHeartbeat(heartbeat_path, alarm_config_path)
alarm_logger = AlarmLogger(alarm_system_configs) #prune documents after n days
alarm_notifier = AlarmNotifier(notifications_config_file, alarm_system_configs, sensor_dict)


def setup_sensors():
    for key, s in sensor_dict.iteritems():
        pin = int(key)
        name = s.name
        sensor_names[pin] = name
        print('SETTING UP SENSOR %s FOR %s'%(pin,name))
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        sensor_states[pin] = GPIO.input(pin)
    alarm_logger.log_alert('INITIALIZING', name, pin, 'CLOSED')
    alarm_notifier.play_sound('ALARM',1,'ON')

def teardown_sensors():
    GPIO.setmode(GPIO.BCM)
    for key, s in sensor_dict.iteritems():
        pin = int(key)
        name = s.name
        print('REMOVING EVENT ON PIN %s'%pin)
        GPIO.remove_event_detect(pin)

def add_sensor_events():
    for key, s in sensor_dict.iteritems():
        pin = int(key)
        name = s.name
        name = s.name
        print('ADDING EVENT ON PIN %s FOR %s'%(pin, name))
        GPIO.add_event_detect(pin, GPIO.BOTH, callback=sensor_triggered, bouncetime=20)

def get_sensor_state_value(gpio_state):
    state_value = 'CLOSED'
    if gpio_state == 1:
        state_value = 'OPEN'
    return state_value

def sensor_triggered(pin):
    pin_state = GPIO.input(pin)
    time.sleep(.25)  #Try to eliminate false positives.  Wait slightly and double-check pin state
    if(pin_state == GPIO.input(pin)):
        prev_state = sensor_states[pin]
        sensor_name = sensor_names[pin]
        sensor_state_val = get_sensor_state_value(pin_state)
        if pin_state != prev_state:
            sensor_states[pin] = pin_state
            alert_date = datetime.datetime.now().strftime("%m-%d %H:%M:%S")
            alert_msg = '%s - %s - %s' %(sensor_name, sensor_state_val, alert_date)
            alarm_logger.log_alert(alert_msg, sensor_name, pin, sensor_state_val)
            if(sensor_state_val != 'CLOSED'):
                alarm_notifier.do_notify(sensor_name, pin, sensor_state_val, alert_msg)
    else:
        pass
    time.sleep(.5)

def poll_system_configs():
    global system_config_mtime
    current_system_config_mtime = os.stat(system_config_file).st_mtime
    if(system_config_mtime != current_system_config_mtime):
        alarm_system_configs.load_configs()
	new_system_configs = alarm_system_configs.get_configs()
	alarm_notifier.update_system_configs(new_system_configs)
	system_config_mtime = current_system_config_mtime



# Initialize the alarm sensors
setup_sensors()
add_sensor_events()



# Endless loop to keep the heartbeat pumping for webapp to monitor
try:
    while 1:
        time.sleep(5)
        alarm_heartbeat.update_heartbeat_file()
	poll_system_configs()
       # pass
except KeyboardInterrupt:
    print('')
    print('')
    print('*CAUGHT KEYBOARD INTERRUPT*')
    print('')
    print('*************')
    print('SHUTTING DOWN')
    print('*************')
    print('')
    teardown_sensors()
    alarm_notifier.play_sound('ALARM',1,'OFF')
except Exception as e:
    print str(e)


GPIO.cleanup()
print('')
print('*******')
print('EXITING')
print('*******')
print('')
