""" 
    Sun Trigger Interface
    Checks time against sun data
    to help perform actions based on 
    the suns position.
"""
import json
import time
import datetime
from mudpi.utils import decode_event_data
from mudpi.exceptions import ConfigError
from mudpi.extensions import BaseInterface
from mudpi.extensions.trigger import Trigger
from mudpi.logger.Logger import Logger, LOG_LEVEL


class Interface(BaseInterface):

    update_interval = 1

    def load(self, config):
        """ Load Trigger component from configs """
        trigger = SunTrigger(self.mudpi, config)
        if trigger:
            self.add_component(trigger)
        return True

    def validate(self, config):
        """ Validate the trigger config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('source'):
                raise ConfigError('Missing `source` key in Sun Trigger config.')
            
        return config


class SunTrigger(Trigger):
    """ A trigger that checks time
        against sun data to perform
        actions based on sun position.
    """
    
    """ Properties """
    @property
    def actions(self):
        """ Keys of actions to call if triggered """
        return self.config.get('actions', [])

    @property
    def nested_source(self):
        """ Override the nested_source of sun trigger """
        _types = ['sunset', 'sunrise', 'solar_noon']
        _type = self.config.get('nested_source', None)
        return _type if _type in _types else None

    @property
    def offset(self):
        """ Return a timedelta offset for comparison """
        _offset = self.config.get('offset', {})
        return datetime.timedelta(hours=_offset.get('hours',0), minutes=_offset.get('minutes',0), seconds=_offset.get('seconds',0))


    """ Methods """
    def init(self):
        """ Listen to the sensors state for changes """
        super().init()
        return True

    def update(self):
        """ Main update loop to see if trigger should fire """
        self.check_time()

    def check_time(self):
        """ Checks the time to see if it is currently sunrise or sunset """

        # Get state object from manager
        state = self.mudpi.states.get(self.source)

        if state is not None:
            _state = state.state
        else:
            _state = None

        if _state:
            try:
                _value = self._parse_data(_state)
                _now = datetime.datetime.now().replace(microsecond=0)
                if _value:
                    _value = datetime.datetime.strptime(_value, "%Y-%m-%d %I:%M:%S %p").replace(microsecond=0) + self.offset
                if _now == _value:
                    self.active = True
                    if self._previous_state != self.active:
                        # Trigger is reset, Fire
                        self.trigger(_value.strftime('%Y-%m-%d %I:%M:%S %p'))
                    else:
                        # Trigger not reset check if its multi fire
                        if self.frequency == 'many':
                            self.trigger(_value.strftime('%Y-%m-%d %I:%M:%S %p'))
                else:
                    self.active = False
            except Exception as error:
                Logger.log(LOG_LEVEL["error"],
                           f'Error evaluating thresholds for trigger {self.id}')
                Logger.log(LOG_LEVEL["debug"], error)
        self._previous_state = self.active

    def unload(self):
        # Unsubscribe once bus supports single handler unsubscribes
        return

    def _parse_data(self, data):
        """ Get nested data if set otherwise return the data """
        try:
            data = json.loads(data)
        except Exception as error:
            pass
        if isinstance(data, dict):
                return data if not self.nested_source else data.get(self.nested_source, None)
        return data