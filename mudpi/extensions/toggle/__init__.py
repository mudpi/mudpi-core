""" 
    Toggle Extension
    Toggles (formerly 'Relays') are components
    that can be toggled i.e. turned on and off.
    Control devices like a pump using a toggle.
"""
import time
import datetime
import threading
from mudpi.utils import decode_event_data
from mudpi.extensions import Component, BaseExtension


NAMESPACE = 'toggle'

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = 0.2

    def init(self, config):
        self.config = config[self.namespace]
        
        self.manager.init(self.config)

        self.manager.register_component_actions('toggle', action='toggle')
        self.manager.register_component_actions('turn_on', action='turn_on')
        self.manager.register_component_actions('turn_off', action='turn_off')
        return True



class Toggle(Component):
    """ Base Toggle
        Base Toggle for all toggle interfaces
    """

    """ Properties """
    @property
    def id(self):
        """ Unique id or key """
        return self.config.get('key').lower()

    @property
    def name(self):
        """ Friendly name of toggle """
        return self.config.get('name') or f"{self.id.replace('_', ' ').title()}"

    @property
    def state(self):
        """ Return the state of the component (from memory, no IO!) """
        return self.active

    @property
    def invert_state(self):
        """ Set to True to make OFF state fire events instead of ON state """
        return self.config.get('invert_state', False)

    @property
    def max_duration(self):
        """ Max duration in seconds the toggle can remain active """
        return self.config.get('max_duration')

    @property
    def duration(self):
        """ Return how long the current state has been applied in seconds """
        self._current_duration = time.perf_counter() - self._duration_start
        return round(self._current_duration, 4)

    @property
    def active(self):
        """ Thread save active boolean """
        return self._active.is_set()

    @active.setter
    def active(self, value):
        """ Allows `self.active = False` while still being thread safe """
        if value:
            self._active.set()
        else:
            self._active.clear()


    """ Methods """
    def update(self):
        """ Update doesn't actually update the state 
            but is instead used for failsafe checks and 
            event detection. """
        if self.max_duration is not None:
            if self.active:
                if self.duration > self.max_duration:
                    # Failsafe cutoff duration
                    self.turn_off()

    def restore_state(self, state):
        """ This is called on start to 
            restore previous state """
        self.active = state.state
        return

    def fire(self, data={}):
        """ Fire a toggle event """
        event_data = {
            'event': 'ToggleUpdated',
            'component_id': self.id,
            'name': self.name,
            'updated_at': str(datetime.datetime.now().replace(microsecond=0)),
            'state': self.state,
            'invert_state': self.invert_state
        }
        event_data.update(data)
        self.mudpi.events.publish(NAMESPACE, event_data)

    def reset_duration(self):
        """ Reset the duration of the toggles current state """
        self._duration_start = time.perf_counter()
        return True

    def unload(self):
        """ Called during shutdown for cleanup operations """
        self.turn_off()


    """ Actions """
    def toggle(self, data={}):
        """ Toggle the device """
        self.active = not self.active
        return self.active

    def turn_on(self, data={}):
        """ Turn on the device """
        self.active = True
        return self.active

    def turn_off(self, data={}):
        """ Turn off the device """
        self.active = False
        return self.active

    def handle_event(self, event):
        """ Handle events from event system """
        _event = None
        try: 
            _event = decode_event_data(event)
        except Exception as error:
            _event = decode_event_data(event['data'])

        if _event == self._last_event:
            # Event already handled
            return

        self._last_event = _event
        if _event is not None:
            try:
                if _event['event'] == 'Switch':
                    if _event.get('data', None):
                        if _event['data'].get('state', 0):
                            self.turn_on()
                        else:
                            self.turn_off()
                elif _event['event'] == 'Toggle':
                    self.toggle()
                elif _event['event'] == 'On':
                    self.turn_on()
                elif _event['event'] == 'Off':
                    self.turn_off()
            except Exception as error:
                Logger.log(LOG_LEVEL["error"],
                           f'Error handling event for {self.id}')

    """ Internal Methods 
    Do not override """
    def _init(self):
        """ Initialize toggle default settings """
        # State should be if the toggle is active or not
        self._state = False

        # Duration tracking
        self._duration_start = time.perf_counter()

        # Thread safe bool for if sequence is active
        self._active = threading.Event()

        # Prevent double event fires
        self._last_event = None
        
        # Listen for events as well
        self.mudpi.events.subscribe(NAMESPACE, self.handle_event)