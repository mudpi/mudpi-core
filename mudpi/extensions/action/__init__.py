""" 
    Actions Extension
    Enables MudPi to perfrom operations in response to a trigger.
    Components expose their own actions however you can also make
    actions manually through configs for more custom interactions.
"""
import json
import redis
import subprocess
from mudpi.extensions import Component, BaseExtension


NAMESPACE = 'action'
UPDATE_INTERVAL = 30

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = UPDATE_INTERVAL

    def init(self, config):
        self.config = config[self.namespace]

        for entry in self.config:
            action = Action(self.mudpi, entry)
            self.mudpi.actions.register(action.id, action)
        return True

    def validate_config(self, config):
        """ Custom Validation for Action configs
            - Requires `key`
        """
        key = None
        for item in config[self.namespace]:
            try:
                key = item.get("key")
            except Exception as error:
                key = None

            if key is None:
                raise ConfigError("Missing `key` in configs.")
        return config

    def add_components(self, components):
        pass


""" Action Templates """ 
class Action:
    """ Actions perfrom operations in response to a trigger.
        
        Can be called by MudPi typically with a trigger to
        emit an event, run a command, or query a service.
     """

    def __init__(self, mudpi, config):
        self.mudpi = mudpi
        self.config = config

        self.init()

    def init(self):
        """ Action will be different depending on type """
        # Event:    json object
        # Command:  command string
        if self.type == 'event':
            self.topic = self.config.get("topic", "mudpi")
        elif self.type == 'command':
            self.shell = self.config.get("shell", False)

        return True

    """ Properties """
    @property
    def name(self):
        """ Return a friendly name for the Action """
        return self.config.get("name", f"Action-{self.id}")

    @property
    def id(self):
        """ Returns a unique id for the Action """
        return self.config.get("key", None).replace(" ", "_").lower() if self.config.get(
            "key") is not None else self.name.replace(" ", "_").lower()

    """ Custom Properties """
    @property
    def type(self):
        """ Returns the type of action. (Event or Command) """
        return self.config.get("type", "event")

    @property
    def action(self):
        """ Returns the action to take """
        return self.config.get("action", None)
    
    """ Methods """
    def trigger(self, value=None):
        """ Trigger the action """
        if self.type == 'event':
            self._emit_event()
        elif self.type == 'command':
            self._run_command(value)
        return


    """ Internal Methods """
    def _emit_event(self):
        """ Emit an event """
        self.mudpi.bus.publish(self.topic, json.dumps(self.action))
        return

    def _run_command(self, value=None):
        """ Run the command """
        if value is None:
            completed_process = subprocess.run([self.action], shell=self.shell)
        else:
            completed_process = subprocess.run(
                [self.action, json.dumps(value)], shell=self.shell)
        return

    def __call__(self, val=None):
        """ Trigger the action when it is called """
        return self.trigger(val)