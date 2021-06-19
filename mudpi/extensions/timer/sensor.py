""" 
    Timer Sensor Interface
    Returns a the time elapsed
    if the timer is active
"""
import time
from mudpi.extensions import BaseInterface
from mudpi.extensions.sensor import Sensor
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.constants import FONT_RESET, FONT_MAGENTA


class Interface(BaseInterface):

    update_interval = 1

    def load(self, config):
        """ Load timer sensor component from configs """
        sensor = TimerSensor(self.mudpi, config)
        self.add_component(sensor)
        return True

    def register_actions(self):
        """ Register any interface actions """
        self.register_component_actions('start', action='start')
        self.register_component_actions('stop', action='stop')
        self.register_component_actions('reset', action='reset')
        self.register_component_actions('pause', action='pause')
        self.register_component_actions('restart', action='restart')


class TimerSensor(Sensor):
    """ Timer Sensor
        Return elapsed time
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
        _state = {
            'active': self.active
        }
        if self.invert_count:
            _remaining = round(self.duration, 2)
            _state['duration_remaining'] = _remaining if _remaining > 0 else 0
            _state['duration'] = self.duration if self.duration > 0 else 0
        else:
            _remaining = round(self.max_duration - self.duration, 2)
            _state['duration_remaining'] = _remaining if _remaining > 0 else 0
            _state['duration'] = self.duration if self.duration < self.max_duration else self.max_duration
        return _state

    @property
    def max_duration(self):
        """ Return the max_duration of the timer """
        return self.config.get('duration', 10)

    @property
    def classifier(self):
        """ Classification further describing it, effects the data formatting """
        return self.config.get('classifier', "general")

    @property
    def active(self):
        """ Return if the timer is active or not """
        return self._active

    @property
    def duration(self):
        if self.active:
            self.time_elapsed = (time.perf_counter() - self.time_start) + self._pause_offset
        return round(self.time_elapsed, 2) if not self.invert_count else round((self.max_duration - self.time_elapsed), 2)

    @property
    def invert_count(self):
        """ Return true if count should count down """
        return self.config.get('invert_count', False)

    @property
    def json_attributes(self):
        """ Return a list of attribute keys to export in json """
        return [
            'max_duration',
            'invert_count'
        ]

    """ Methods """
    def init(self):
        """ Init the timer component """
        self._active = False
        self.time_elapsed = 0
        self._pause_offset = 0
        self.reset_duration()

    def update(self):
        """ Get timer data """
        if self.duration >= self.max_duration and not self.invert_count:
            self.stop()
        elif self.duration <= 0 and self.invert_count:
            self.stop()
        return True

    def reset_duration(self):
        """ Reset the elapsed duration """
        self.time_start = time.perf_counter()
        return self


    """ Actions """
    def start(self, data=None):
        """ Start the timer """
        if not self.active:
            self.reset_duration()
            self._active = True
            if self._pause_offset == 0:
                Logger.log(
                    LOG_LEVEL["debug"],
                    f'Timer Sensor {FONT_MAGENTA}{self.name}{FONT_RESET} Started'
                )
            else:
                Logger.log(
                    LOG_LEVEL["debug"],
                    f'Timer Sensor {FONT_MAGENTA}{self.name}{FONT_RESET} Resumed'
                )

    def pause(self, data=None):
        """ Pause the timer """
        if self.active:
            self._active = False
            self._pause_offset = 0
            self.reset_duration()

    def stop(self, data=None):
        """ Stop the timer """
        if self.active:
            self._active = False
            self.reset()
            Logger.log(
                LOG_LEVEL["debug"],
                f'Timer Sensor {FONT_MAGENTA}{self.name}{FONT_RESET} Stopped'
            )

    def reset(self, data=None):
        """ Reset the timer """
        self.reset_duration()
        self._pause_offset = 0

    def restart(self, data=None):
        """ Restart the timer """
        self.reset()
        self.start()
        return self

