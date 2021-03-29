""" 
    Toggle Extension
    Toggles (formerly 'Relays') are components
    that can be toggled i.e. turned on and off.
    Control devices like a pump using a toggle.
"""
import time
import datetime
import threading
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
        return self.config.get('key')

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
        return self._active #self._active.is_set()

    @active.setter
    def active(self, value):
        """ Allows `self.active = False` while still being thread safe """
        if bool(value):
            self._active = True #self._active.set()
        else:
            self._active = False #self._active.clear()


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
        self._state = state.state
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

    """ Internal Methods 
    Do not override """
    def _init(self):
        """ Initialize toggle default settings """
        # State should be if the toggle is active or not
        self._state = False

        # Duration tracking
        self._duration_start = time.perf_counter()

        # Thread safe bool for if sequence is active
        self._active = False #threading.Event()