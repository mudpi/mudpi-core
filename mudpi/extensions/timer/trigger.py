""" 
    Timer Trigger Interface
    Calls actions after a
    configurable elapsed time.
"""
import time
from . import NAMESPACE
from mudpi.utils import decode_event_data
from mudpi.extensions import BaseInterface
from mudpi.extensions.trigger import Trigger
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.constants import FONT_RESET, FONT_MAGENTA


class Interface(BaseInterface):

    def load(self, config):
        """ Load timer trigger component from configs """
        trigger = TimerTrigger(self.mudpi, config)
        self.add_component(trigger)
        return True

    def validate(self, config):
        """ Validate the trigger config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('key'):
                raise ConfigError('Missing `key` in Timer Trigger config.')
            
        return config

    def register_actions(self):
        """ Register any interface actions """
        self.register_component_actions('start', action='start')
        self.register_component_actions('stop', action='stop')
        self.register_component_actions('pause', action='pause')
        self.register_component_actions('reset', action='reset')
        self.register_component_actions('restart', action='restart')


class TimerTrigger(Trigger):
    """ Timer Trigger
        Calls actions after 
        set elapsed time
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
    def max_duration(self):
        """ Return the max_duration of the timer """
        return self.config.get('duration', 10)

    @property
    def active(self):
        """ Return if the timer is active or not """
        return self._active

    @property
    def duration(self):
        if self.active:
            self.time_elapsed = (time.perf_counter() - self.time_start) + self._pause_offset
        return round(self.time_elapsed, 2)


    """ Methods """
    def init(self):
        """ Init the timer component """
        self._listening = False
        self._active = False
        self.time_elapsed = 0
        self._last_event = None
        self._pause_offset = 0
        self.reset_duration()

        if self.mudpi.is_prepared:
            if not self._listening:
                # TODO: Eventually get a handler returned to unsub just this listener
                self.mudpi.events.subscribe(f'{NAMESPACE}/{self.id}', self.handle_event)
                self._listening = True

    def update(self):
        """ Get timer data """
        if self.duration >= self.max_duration:
            if self.active:
                self.stop()
                self.trigger()
        return True

    def reset_duration(self):
        """ Reset the elapsed duration """
        self.time_start = time.perf_counter()
        return self

    def handle_event(self, event):
        """ Process event data for the timer """
        _event_data = decode_event_data(event)

        if _event_data == self._last_event:
            # Event already handled
            return

        self._last_event = _event_data
        if _event_data.get('event'):
            try:
                if _event_data['event'] == 'TimerStart':
                    self.start()
                    Logger.log(
                        LOG_LEVEL["debug"],
                        f'Timer Trigger {FONT_MAGENTA}{self.name}{FONT_RESET} Started'
                    )
                elif _event_data['event'] == 'TimerStop':
                    self.stop()
                    Logger.log(
                        LOG_LEVEL["debug"],
                        f'Timer Trigger {FONT_MAGENTA}{self.name}{FONT_RESET} Stopped'
                    )
                elif _event_data['event'] == 'TimerReset':
                    self.reset()
                    Logger.log(
                        LOG_LEVEL["debug"],
                        f'Timer Trigger {FONT_MAGENTA}{self.name}{FONT_RESET} Reset'
                    )
                elif _event_data['event'] == 'TimerRestart':
                    self.restart()
                    Logger.log(
                        LOG_LEVEL["debug"],
                        f'Timer Trigger {FONT_MAGENTA}{self.name}{FONT_RESET} Restarted'
                    )
                elif _event_data['event'] == 'TimerPause':
                    self.pause()
                    Logger.log(
                        LOG_LEVEL["debug"],
                        f'Timer Triger {FONT_MAGENTA}{self.name}{FONT_RESET} Paused'
                    )
            except:
                Logger.log(
                    LOG_LEVEL["info"],
                    f"Error Decoding Event for Timer Trigger {self.id}"
                )


    """ Actions """
    def start(self, data=None):
        """ Start the timer """
        if not self.active:
            if self.frequency == 'many':
                self.reset()
            else:
                self.reset_duration()
            self._active = True
            if self._pause_offset == 0:
                Logger.log(
                    LOG_LEVEL["debug"],
                    f'Timer Trigger {FONT_MAGENTA}{self.name}{FONT_RESET} Started'
                )
            else:
                Logger.log(
                    LOG_LEVEL["debug"],
                    f'Timer Trigger {FONT_MAGENTA}{self.name}{FONT_RESET} Resumed'
                )
        return self

    def pause(self, data=None):
        """ Pause the timer """
        if self.active:
            self._active = False
            self._pause_offset = self.duration
            self.reset_duration()
        return self

    def stop(self, data=None):
        """ Stop the timer """
        if self.active:
            self.reset()
            self._active = False
            Logger.log(
                LOG_LEVEL["debug"],
                f'Timer Trigger {FONT_MAGENTA}{self.name}{FONT_RESET} Stopped'
            )
        return self

    def reset(self, data=None):
        """ Reset the timer """
        self.reset_duration()
        self._pause_offset = 0
        return self

    def restart(self, data=None):
        """ Restart the timer """
        self.reset()
        self.start()
        return self
