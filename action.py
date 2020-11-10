import json
import subprocess
import sys

import redis




class Action():

    def __init__(self, config):
        self.config = config
        self.name = config.get("name", "Action")
        self.type = config.get("type", "event")
        self.key = config.get("key", None).replace(" ",
                                                   "_").lower() if config.get(
            "key") is not None else self.name.replace(" ", "_").lower()
        # Actions will be either objects to publish for events
        # or a command string to execute
        self.action = config.get("action")

        try:
            self.r = config["redis"] if config[
                                            "redis"] is not None else redis.Redis(
                host='127.0.0.1', port=6379)
        except KeyError:
            self.r = redis.Redis(host='127.0.0.1', port=6379)
        return

    def init_action(self):
        if self.type == 'event':
            self.topic = self.config.get("topic", "mudpi")
        elif self.type == 'command':
            self.shell = self.config.get("shell", False)

    def trigger(self, value=None):
        if self.type == 'event':
            self.emit_event()
        elif self.type == 'command':
            self.run_command(value)
        return

    def emit_event(self):
        self.r.publish(self.topic, json.dumps(self.action))
        return

    def run_command(self, value=None):
        if value is None:
            completed_process = subprocess.run([self.action], shell=self.shell)
        else:
            completed_process = subprocess.run(
                [self.action, json.dumps(value)], shell=self.shell)
        return
