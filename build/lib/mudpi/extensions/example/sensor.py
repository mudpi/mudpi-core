""" 
    Example Sensor Interface
    Returns a random number between one
    and ten with each update. 
"""
import random
from mudpi.extensions import BaseInterface
from mudpi.extensions.sensor import Sensor


class Interface(BaseInterface):

    def load(self, config):
        """ Load example sensor component from configs """
        sensor = ExampleSensor(self.mudpi, config)
        self.add_component(sensor)
        return True


class ExampleSensor(Sensor):
    """ Example Sensor
        Returns a random number
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
        return self.config.get('classifier', "general")


    """ Methods """
    def update(self):
        """ Get Random data """
        self._state = random.randint(1, self.config.get('data', 10))
        return True

