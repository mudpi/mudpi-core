import redis
import threading
import json

class Listener(threading.Thread):
	def __init__(self, r, channels):
		threading.Thread.__init__(self)
		self.redis = r
		self.pubsub = self.redis.pubsub()
		self.pubsub.subscribe(channels)
		
	def check_type(self, item):
		if isinstance(item, dict):
			return item
		elif isinstance(item, str):
			try:
				temp = json.loads(item)
				return temp
			except:
				return {'value':item}
		else:
			return {'value':item}

	def work(self, item):
		for val, key in item.items():
			print(val, ":", key)
	
	def run(self):
		for item in self.pubsub.listen():
			payload = {}
			if item['type'] == 'message' or item['type'] == 'pmessage':
				payload = self.check_type(item['data'])
			if payload.get('EXIT', False):
				self.pubsub.unsubscribe()
				print(self, 'Redis Listener Shutdown...\t\t\033[1;32m Complete\033[0;0m')
				break
			else:
				print('--------- New Message ---------')
				#print(item)
				print('channel: ', item['channel'])
				print('type: ', item['type'])
				self.work(payload)
				print('-------------------------------\n')
