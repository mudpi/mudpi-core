class Adaptor:
	""" Base adaptor for pubsub event system """

	# This key should represent key in configs that it will load form
	key = None

	adaptors = {}

	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		cls.adaptors[cls.key] = cls

	def __init__(self, config={}):
		self.config = config

	def connect(self):
		""" Authenticate to system and cache connections """
		raise NotImplementedError()

	def disconnect(self):
		""" Close active connections and cleanup subscribers """
		raise NotImplementedError()

	def subscribe(self, topic, callback):
		""" Listen on a topic and pass event data to callback """
		raise NotImplementedError()

	def unsubscribe(self, topic):
		""" Stop listening for events on a topic """
		raise NotImplementedError()

	def publish(self, topic, data=None):
		""" Publish an event on the topic """
		raise NotImplementedError()

	""" No need to override this unless necessary """
	def subscribe_once(self, topic, callback):
		""" Subscribe to topic for only one event """
		def handle_once(data):
			""" Wrapper to unsubscribe after event handled """
			self.unsubscribe(topic)
			if callable(callback):
				# Pass data to real callback
				callback(data)

		return self.subscribe(topic, handle_once)

	def get_message(self):
		""" Some protocols need to initate a poll for new messages """
		pass

# Import adaptors
from . import redis, mqtt

