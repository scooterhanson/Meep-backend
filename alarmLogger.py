import time
from datetime import datetime, timedelta
import json
import calendar
from alarmDbClient import AlarmDBClient

class AlarmLogger:
	def __init__(self, alarm_system_configs):
		db_host = alarm_system_configs.check_configValue("database","host")
		db_port = int(alarm_system_configs.check_configValue("database","port"))
		self.db_client = AlarmDBClient(db_host, db_port)
                self.db_items =self.db_client.get_items()
		self.alarm_system_configs = alarm_system_configs
		self.days_retained = alarm_system_configs.check_configValue("system","days_to_retain") #prune documents after n days

        def log_alert(self, msg, sensor, pin, state):
                print('')
                print('%s (PIN %s) IS %s'%(sensor ,pin,state))
                print('detected change on %s'%pin)
                print(time.time())
                print('')
                date_now = datetime.now().strftime("%m-%d-%y %H:%M:%S")
                params = {}
                params.update({'msg': msg.upper(), 'state': state.upper(), 'sensor': sensor.upper(), 'pin': pin, 'date': date_now})
                json_params = json.dumps(params)
                item_id = self.db_items.insert(params)
                self.log_prune()

        def log_prune(self):
                n = self.days_retained
		date_n_days_ago = datetime.now() - timedelta(days=n)
		fmt_date_n_days_ago = date_n_days_ago.strftime("%m-%d-%y 00:00:00")
                self.db_items.remove({"date": {'$lt' : fmt_date_n_days_ago}})
