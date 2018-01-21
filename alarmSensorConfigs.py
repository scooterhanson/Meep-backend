import json

class Sensor(object):
    def __init__(self, sensorid, name, pin, type, track_open, track_close, notify_open, notify_close, alert_open, alert_close, alert_sound, *args, **kwargs):
        self.sensorid = sensorid
        self.name = name
        self.pin = pin
	self.type = type
        self.track_open = track_open
        self.track_close = track_close
        self.notify_open = notify_open
        self.notify_close = notify_close
        self.alert_open = alert_open
        self.alert_close = alert_close
	self.alert_sound = alert_sound

class AlarmSensorConfigs:
    def __init__(self, sensor_file):
        self.sensor_file = sensor_file

    def get_sensor_dict(self):
        sensor_dict = {}
        with open(self.sensor_file, 'r') as json_file:
            data = json.load(json_file)
            sensor_configs = data['Sensors']
            for sensor_name in sensor_configs:
                sensor_config = sensor_configs[sensor_name]
                s = Sensor(**sensor_config)
		pin = s.pin
                sensor_dict[pin] = s
		print('pin: %s sound: %s'%(pin,s.alert_sound))
        return sensor_dict

