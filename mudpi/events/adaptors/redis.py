import redis
import json
from . import Adaptor


class RedisAdaptor(Adaptor):
	""" Allow MudPi events on Pubsub through Redis """
	key = 'redis'

	def connect(self):
		""" Make redis connection and setup pubsub """
		host = self.config.get('host', '127.0.0.1')
		port = self.config.get('port', 6379)
		self.connection = redis.Redis(host=host, port=port)
		self.pubsub = self.connection.pubsub()
		return True

	def disconnect(self):
		""" Close active connections and cleanup subscribers """
		self.pubsub.close()
		self.connection.close()
		return True

	def subscribe(self, topic, callback):
		""" Listen on a topic and pass event data to callback """
		return self.pubsub.subscribe(**{topic: callback})

	def unsubscribe(self, topic):
		""" Stop listening for events on a topic """
		return self.pubsub.unsubscribe(topic)

	def publish(self, topic, data=None):
		""" Publish an event on the topic """
		if data:
			return self.connection.publish(topic, json.dumps(data))

		return self.connection.publish(topic)

	def get_message(self):
		""" Check for new messages waiting """
		return self.pubsub.get_message()