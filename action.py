import time
import json
import redis
import subprocess
import sys
sys.path.append('..')
import variables

class Action():

	def __init__(self, config):
		self.config = config
		self.name = config.get("name", "Action")
		self.type = config.get("type", "event")
		self.key = config.get("key", None).replace(" ", "_").lower() if config.get("key") is not None else self.name.replace(" ", "_").lower()
		# Actions will be either objects to publish for events or a command string to execute
		self.action = config.get("action")
		return

	def init_action(self):
		if self.type == 'event':
			self.topic = self.config.get("topic", "mudpi")
		elif self.type == 'command':
			self.shell = self.config.get("shell", False)

	def trigger(self, value=None):
		if self.type == 'event':
			self.emitEvent()
		elif self.type == 'command':
			self.runCommand(value)
		return

	def emitEvent(self):
		variables.r.publish(self.topic, json.dumps(self.action))
		return

	def runCommand(self, value=None):
		if value is None:
			completed_process = subprocess.run([self.action], shell=self.shell)
		else:
			completed_process = subprocess.run([self.action, json.dumps(value)], shell=self.shell)
		return