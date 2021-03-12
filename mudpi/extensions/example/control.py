""" 
    Example Control Interface
    Example control that randomly fires
    events for demonstration. 
"""
import random
from mudpi.extensions import BaseInterface
from mudpi.extensions.control import Control
from mudpi.exceptions import MudPiError, ConfigError


class Interface(BaseInterface):

    # Examples don't need to be ultra fast
    update_interval = 3

    def load(self, config):
        """ Load example control component from configs """
        control = ExampleControl(self.mudpi, config)
        if control:
            self.add_component(control)
        return True

    def validate(self, config):
        """ Validate the control config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if conf.get('key') is None:
                raise ConfigError('Missing `key` in example control.')

        return config



class ExampleControl(Control):
    """ Example Control
        Randomly fires active for demonstration of controls
    """

    # Default inital state
    _state = False

    # One time firing
    _fired = False

    """ Properties """
    @property
    def state(self):
        """ Return the state of the component (from memory, no IO!) """
        return self._state

    @property
    def update_chance(self):
        """ Return the chance the trigger will fire (1-100)
            Default: 25% """
        _chance = self.config.get('update_chance', 25)
        if _chance > 100 or _chance < 1:
            _chance = 25
        return _chance


    """ Methods """
    def update(self):
        """ Check if control should flip state randomly """
        _state = self._state
        if random.randint(1, 100) <= self.update_chance:
            _state = not _state
        self._state = _state
        self.handle_state()

    def handle_state(self):
        """ Control logic depending on type of control """
        if self.type == 'button':
            if self._state:
                if not self.invert_state:
                    self.fire()
            else:
                if self.invert_state:
                    self.fire()
        elif self.type == 'switch':
            # Switches use debounce ensuring we only fire once
            if self._state and not self._fired:
                # State changed since we are using edge detect
                self.fire()
                self._fired = True
            else:
                self._fired = False

