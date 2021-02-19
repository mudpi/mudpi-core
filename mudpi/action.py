import sys
import json
import redis
import subprocess


class Action():
    """ Actions allow MudPi to perfrom operations,
    typically in response to a trigger.

    Emits an event or runs a command. """

    def __init__(self, config):
        self.config = config
        self.name = config.get("name", "Action")
        self.type = config.get("type", "event")
        self.key = config.get("key", None).replace(" ", "_").lower() if config.get(
            "key") is not None else self.name.replace(" ", "_").lower()

        # event data if event, command string if command
        self.action = config.get("action") 

        try:
            self.r = config["redis"] if config["redis"] is not None else redis.Redis(
                host='127.0.0.1', port=6379)
        except KeyError:
            self.r = redis.Redis(host='127.0.0.1', port=6379)
        return

    def init(self):
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

    def __call__(self, val=None):
        return self.trigger(val)
