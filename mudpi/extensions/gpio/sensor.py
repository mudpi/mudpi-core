""" 
    GPIO Sensor Interface
    Connects to a linux board GPIO to
    take analog or digital readings. 
"""
import board
import digitalio
from mudpi.extensions import BaseInterface
from mudpi.extensions.sensor import Sensor
from mudpi.exceptions import MudPiError, ConfigError


class Interface(BaseInterface):

    def load(self, config):
        """ Load GPIO sensor component from configs """
        sensor = GPIOSensor(self.mudpi, config)
        if sensor:
            self.add_component(sensor)
        return True

    def validate(self, config):
        """ Validate the dht config """
        if not config.get('pin'):
            raise ConfigError('Missing `pin` in GPIO config.')

        if not re.match(r'D\d+$', config['pin']) and not re.match(r'A\d+$', config['pin']):
            raise ConfigError(
                "Cannot detect pin type (Digital or analog), "
                "should be D## or A## for digital or analog. "
                "Please refer to "
                "https://github.com/adafruit/Adafruit_Blinka/tree/master/src/adafruit_blinka/board"
            )
            
        return config


class GPIOSensor(Sensor):
    """ GPIO Sensor
        Returns a reading from gpio pin
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


    """ Methods """
    def init(self):
        """ Connect to the device """
        self.pin_obj = getattr(board, self.config['pin'])

        if re.match(r'D\d+$', pin):
            self.is_digital = True
        elif re.match(r'A\d+$', pin):
            self.is_digital = False

        self.gpio = digitalio

        return True
        
    def update(self):
        """ Get data from GPIO connection"""
        if self.is_digital:
            data = self.gpio.DigitalInOut(self.pin_obj).value
        else:
            data = self.gpio.AnalogIn(self.pin_obj).value
        self._state = data
        return data
