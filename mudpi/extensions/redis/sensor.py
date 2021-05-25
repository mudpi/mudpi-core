""" 
    Redis Sensor Interface
    Connects to a redis to get data 
    from state or event. 
"""
import time
import json
import redis
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
        """ Load redis sensor component from configs """
        sensor = RedisSensor(self.mudpi, config)
        if sensor:
            sensor.connect(self.extension.connections[config['connection']])
            self.add_component(sensor)
        return True

    def validate(self, config):
        """ Validate the redis sensor config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('key'):
                raise ConfigError('Missing `key` in redis sensor config.')

            if not conf.get('type'):
                # Default the sensor type
                conf['type'] = 'state'

            if conf['type'].lower() == 'state':
                state_key = conf.get('state_key')
                if not state_key:
                    pass
                    # raise ConfigError(f'Missing `state_key` for `state` redis sensor type {conf["key"]} config.')
            elif conf['type'].lower() == 'event':
                expires = conf.get('expires')
                if not expires:
                    conf['expires'] = 0
                else:
                    conf['expires'] = int(conf['expires'])

        return config


class RedisSensor(Sensor):
    """ Redis Sensor
        Returns a reading from redis state or events
    """

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
    def type(self):
        """ Return the sensor type (event, state) """
        return self.config.get('type', 'state').lower()

    @property
    def topic(self):
        """ Return the topic to listen on for event sensors """
        return str(self.config.get('topic', f'sensor/{self.id}'))

    @property
    def state_key(self):
        """ Return the key to get from redis for state sensor """
        return self.config.get('state_key', self.id)

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
        
        # Track state change
        self._prev_state = None

        # Connection to redis
        self._conn = None

        # For duration tracking
        self._duration_start = time.perf_counter()

        return True

    def connect(self, connection):
        """ Connect the sensor to redis """
        self._conn = connection
        if self.type == 'event':
            self.bus = self._conn.pubsub()
            self.bus.subscribe(**{self.topic: self.handle_event})
        
    def update(self):
        """ Get data from memory or wait for event """
        if self._conn:
            if self.type == 'state':
                _data = self._conn.get(self.state_key)
                if _data:
                    self._state = _data.decode('utf-8')
            else:
                self.bus.get_message()
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

    def handle_event(self, event={}):
        """ Handle event from redis pubsub """
        data = decode_event_data(event['data'])
        if data is not None:
            try:
                # _event_data = self.last_event = decode_event_data(data)
                self._state = data
            except:
                Logger.log(
                    LOG_LEVEL["info"],
                    f"Error Decoding Event for Redis Sensor {self.id}"
                )

    def reset_duration(self):
        """ Reset the duration of the current state """
        self._duration_start = time.perf_counter()
        return True