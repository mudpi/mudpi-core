""" 
    Sun Sensor Interface
    Connects to sun api to get 
    sunset and sunrise times. 
    https://sunrise-sunset.org
"""
import time
import json
import requests
import datetime
from mudpi.utils import decode_event_data
from mudpi.extensions import BaseInterface
from mudpi.extensions.sensor import Sensor
from mudpi.exceptions import MudPiError, ConfigError


class Interface(BaseInterface):
    
    update_interval = (60 * 60 * 4) # Every 4 hours

    def load(self, config):
        """ Load sensor component from configs """
        sensor = SunSensor(self.mudpi, config)
        if sensor:
            self.add_component(sensor)
        return True

    def validate(self, config):
        """ Validate the sensor config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('key'):
                raise ConfigError('Missing `key` in sun sensor config.')

            latitude = conf.get('latitude')
            if not latitude:
                conf['latitude'] = self.mudpi.config.latitude
            else:
                conf['latitude'] = float(conf['latitude'])

            longitude = conf.get('longitude')
            if not longitude:
                conf['longitude'] = self.mudpi.config.longitude
            else:
                conf['longitude'] = float(conf['longitude'])

        return config


class SunSensor(Sensor):
    """ Sun Sensor
        Returns a sunrise and sunset from api
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
    def latitude(self):
        """ Return latitude location """
        return self.config['latitude']

    @property
    def longitude(self):
        """ Return longitude location """
        return self.config['longitude']
    
    @property
    def state(self):
        """ Return the state of the component (from memory, no IO!) """
        return {
            "sunrise": self._sunrise,
            "sunset": self._sunset,
            "solar_noon": self._solar_noon,
            "day_length": self._day_length
        }

    @property
    def duration(self):
        """ Return c
        how long the current state has been applied in seconds """
        self._current_duration = time.perf_counter() - self._duration_start
        return round(self._current_duration, 4)

    """ Methods """
    def restore_state(self, state):
        """ Retstore state to prevent calls after multiple restarts """
        self._sunrise = state.state["sunrise"]
        self._sunset = state.state["sunset"]
        self._solar_noon = state.state["solar_noon"]
        self._day_length = state.state["day_length"]
        _last_update = datetime.datetime.strptime(state.updated_at, '%Y-%m-%d %H:%M:%S')
        _time = datetime.datetime.now() - _last_update
        _hours_past = _time.total_seconds() / (60 * 60)
        if _hours_past < 4:
            self._data_expired = False


    def init(self):
        """ Initialize the sun component """
        # Track state change
        self._prev_state = {}
        self._data_expired = True
        self._sunrise = '00:00:00 AM'
        self._sunset = '00:00:00 AM'
        self._solar_noon = '00:00:00 AM'
        self._day_length = '00:00:00'

        # For duration tracking
        self.reset_duration()

    def update(self):
        """ Get the data for the day """
        if self.duration > (60 * 60 * 4):
            self._data_expired = True

        if self._data_expired:
            _data = self.fetch_data()
            if _data:
                self._sunrise = self.parse_time(_data['results']['sunrise'])
                self._sunset = self.parse_time(_data['results']['sunset'])
                self._solar_noon = self.parse_time(_data['results']['solar_noon'])
                self._day_length = _data['results']['day_length']
                self._data_expired = False

    def fetch_data(self):
        """ Make an API request for updated data """
        print("Getting Sun Data...")
        url = 'https://api.sunrise-sunset.org/json'

        response = requests.get(url,
          params={'lat': self.latitude, 'lng': self.longitude},)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            pass
        return False

    def parse_time(self, timestamp):
        """ Parse a timestring to an object and localize it 
            Expected format 11:03:10 PM """
        _date = datetime.datetime.strptime(timestamp, '%I:%M:%S %p')
        _today = datetime.datetime.now()
        _date = _date.replace(day=_today.day, year=_today.year, month=_today.month)
        # .strftime('%Y-%m-%d %I:%M:%S %p')
        return _date.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None).strftime('%Y-%m-%d %I:%M:%S %p')

    def reset_duration(self):
        """ Reset the duration of the current state """
        self._duration_start = time.perf_counter()
        return self._duration_start