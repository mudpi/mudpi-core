""" 
    MQTT Sensor Interface
    Connects to a mqtt to get data 
    from an incoming event. 
"""
import time
import json
from mudpi.utils import decode_event_data
from mudpi.extensions import BaseInterface
from mudpi.extensions.sensor import Sensor
from mudpi.logger.Logger import Logger, LOG_LEVEL
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


class MQTTSensor(Sensor):
    """ MQTT Sensor
        Returns a reading from events
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

    @property
    def classifier(self):
        """ Classification further describing it, effects the data formatting """
        return self.config.get('classifier', 'general')

    @property
    def topic(self):
        """ Return the topic to listen on for event sensors """
        return str(self.config.get('topic', f'sensor/{self.id}'))

    @property
    def expires(self):
        """ Return the time in which state becomes stale """
        return int(self.config.get('expires', 0))

    @property
    def expired(self):
        """ Return if current data is expired """
        if self.expires > 0:
            return time.perf_counter() - self._duration_start > self.expires
        else:
            return False


    """ Methods """
    def init(self):
        """ Connect to the device """
        # Perform inital state fetch
        # self.update()
        # self.store_state()

        return True

    def connect(self, extension):
        """ Connect the sensor to mqtt """
        _conn_key = self.config['connection']
        self._conn = extension.connections[_conn_key]['client']
        extension.subscribe(_conn_key, self.topic, self.handle_event)
        
        
    def update(self):
        """ Get data from memory or wait for event """
        if self._conn:
            if self.expired:
                self.mudpi.events.publish('sensor', {
                    'event': 'StateExpired', 
                    'component_id': self.id,
                    'expires': self.expires,
                    'previous_state': self.state,
                    'type': self.type})
                self._state = None
            if self._prev_state != self._state:
                self.reset_duration()
            self._prev_state = self._state
        return self._state

    def handle_event(self, data={}):
        """ Handle event from mqtt broker """
        if data is not None:
            try:
                # _event_data = self.last_event = decode_event_data(data)
                self._state = data
            except:
                Logger.log(
                    LOG_LEVEL["info"],
                    f"Error Decoding Event for MQTT Sensor {self.id}"
                )

    def reset_duration(self):
        """ Reset the duration of the current state """
        self._duration_start = time.perf_counter()
        return True