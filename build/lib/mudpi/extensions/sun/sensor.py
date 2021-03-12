""" 
    Sun Sensor Interface
    Connects to sun api to get 
    sunset and sunrise times. 
"""
import time
import json
import requests
from mudpi.utils import decode_event_data
from mudpi.extensions import BaseInterface
from mudpi.extensions.sensor import Sensor
from mudpi.exceptions import MudPiError, ConfigError


class Interface(BaseInterface):

    # Override the update interval due to event handling
    update_interval = 1

    # Duration tracking
    _duration_start = time.perf_counter()

    def load(self, config):
        """ Load mqtt sensor component from configs """
        sensor = MQTTSensor(self.mudpi, config)
        if sensor:
            sensor.connect(self.extension)
            self.add_component(sensor)
        return True

    def validate(self, config):
        """ Validate the mqtt sensor config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('key'):
                raise ConfigError('Missing `key` in MQTT sensor config.')

            expires = conf.get('expires')
            if not expires:
                conf['expires'] = 0
            else:
                conf['expires'] = int(conf['expires'])

        return config


class SunSensor(Sensor):
    """ Sun Sensor
        Returns a sunset and sunset from api
    """

    # Track state change
    _prev_state = None

    # Connection to mqtt
    _conn = None

    # For duration tracking
    _duration_start = time.perf_counter()

    """ Properties """
    @property
    def id(self):
        """ Return a unique id for the component """
        return self.config['key']

    @property
    def name(self):
        """ Return the display name of the component """
        return self.config.get('name') or f"{self.id.replace('_', ' ').title()}"
    
    @property
    def state(self):
        """ Return the state of the component (from memory, no IO!) """
        return self._state

# url = 'https://api.sunrise-sunset.org/json'

# response = requests.get(url,
#   params={'lat': 42.526, 'lng': -89.043},)

# if response.status_code == 200:
#     print('Success!')
# elif response.status_code == 404:
#     print('Not Found.')

# print(response.json())