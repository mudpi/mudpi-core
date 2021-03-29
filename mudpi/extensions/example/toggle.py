""" 
    Example Toggle Interface
    Example toggle for testing. State
    is stored in memory.
"""
from mudpi.extensions import BaseInterface
from mudpi.extensions.toggle import Toggle
from mudpi.exceptions import MudPiError, ConfigError


class Interface(BaseInterface):

    def load(self, config):
        """ Load example toggle component from configs """
        toggle = ExampleToggle(self.mudpi, config)
        if toggle:
            self.add_component(toggle)
        return True

    def validate(self, config):
        """ Validate the example config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if conf.get('key') is None:
                raise ConfigError('Missing `key` in example toggle config.')

        return config


class ExampleToggle(Toggle):
    """ Example Toggle
        Turns a boolean off and on in memory
    """

    """ Methods """
    def restore_state(self, state):
        """ This is called on start to 
            restore previous state """
        self._state = True if state.state else False
        return


    """ Actions """
    def toggle(self, data={}):
        # Toggle the state
        if self.mudpi.is_prepared:
            self.active = not self.active
            self.store_state()

    def turn_on(self, data={}):
        # Turn on if its not on
        if self.mudpi.is_prepared:
            if not self.active:
                self.active = True
                self.store_state()

    def turn_off(self, data={}):
        # Turn off if its not off
        if self.mudpi.is_prepared:
            if self.active:
                self.active = False
                self.store_state()