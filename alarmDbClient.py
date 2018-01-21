from pymongo import MongoClient

class AlarmDBClient:
	def __init__(self, dbhost = 'localhost', dbport = 27017):
		self.dbhost = dbhost
		self.dbport = dbport
		print ('HOST %s, PORT %s'%(dbhost,dbport))
		self.client = MongoClient(dbhost,dbport)
                self.db = self.client.alarm
                self.items = self.db.items

	def get_client(self):
		return self.client

	def get_db(self):
		return self.db

	def get_items(self):
		return self.items



