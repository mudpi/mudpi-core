""" 
    Example Character Display
    Stores Message in Memory.
"""

from mudpi.extensions import BaseInterface
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.extensions.char_display import CharDisplay


class Interface(BaseInterface):

    def load(self, config):
        """ Load example display component from configs """
        display = ExampleDisplay(self.mudpi, config)

        # Check for test messages to fill the queue with
        if config.get('messages'):
            _count = 0
            while(_count < display.message_limit):
                for msg in config['messages']:
                    display.add_message({'message': msg})
                    _count +=1

        if display:
            self.add_component(display)
        return True

    
    def validate(self, config):
        """ Validate the display configs """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('key'):
                raise ConfigError('Missing `key` in example display config.')

        return config


class ExampleDisplay(CharDisplay):
    """ Example Character Display
        Test display that keeps messages in memory.
    """

    """ Properties """
    @property
    def default_duration(self):
        """ Default message display duration """
        return int(self.config.get('default_duration', 10))


    """ Actions """
    def clear(self, data=None):
        """ Clear the display screen """
        self.current_message = ''

    def show(self, data={}):
        """ Show a message on the display """
        if not isinstance(data, dict):
            data = {'message': data}

        self.current_message = data.get('message', '')
            