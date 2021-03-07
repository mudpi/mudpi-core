""" 
    Group Trigger Interface
    Allows triggers to be grouped
    together for complex conditions.
"""
from mudpi.exceptions import ConfigError
from mudpi.extensions import BaseInterface
from mudpi.extensions.trigger import Trigger
from mudpi.logger.Logger import Logger, LOG_LEVEL


class Interface(BaseInterface):

    def load(self, config):
        """ Load group trigger component from configs """
        trigger = GroupTrigger(self.mudpi, config)
        if trigger:
            self.add_component(trigger)
        return True

    def validate(self, config):
        """ Validate the trigger config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('triggers'):
                raise ConfigError('Missing `triggers` keys in Trigger Group')
            
        return config


class GroupTrigger(Trigger):
    """ A Group to allow complex combintations 
        between multiple trigger types. 
    """

    # List of triggers to monitor
    _triggers = []

    """ Properties """
    @property
    def triggers(self):
        """ Keys of triggers to group """
        return self.config.get('triggers', [])

    @property
    def trigger_states(self):
        """ Keys of triggers to group """
        return [trigger.active for trigger in self._triggers]


    """ Methods """
    def init(self):
        """ Load in the triggers for the group """
        # Doesnt call super().init() because that is for non-groups
        self.cache = self.mudpi.cache.get('trigger', {})
        self.cache.setdefault('groups', {})[self.id] = self

        for _trigger in self.triggers:
            _trig = self.cache.get('triggers', {}).get(_trigger)
            if _trig:
                self.add_trigger(_trig)
        return True

    def add_trigger(self, trigger):
        """ Add a trigger to monitor """
        self._triggers.append(trigger)

    def check(self):
        """ Check if trigger should fire """
        if all(self.trigger_states):
            self.active = True
            if self._previous_state != self.active:
                # Trigger is reset, Fire
                self.trigger()
            else:
                # Trigger not reset check if its multi fire
                if self.frequency == 'many':
                    self.trigger()
        else:
            self.active = False
        self._previous_state = self.active
