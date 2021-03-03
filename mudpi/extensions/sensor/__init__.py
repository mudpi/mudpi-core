""" 
    Sensors Extension
    Sensors are components that gather data and make it 
    available to MudPi. Sensors support interfaces to 
    allow additions of new types of devices easily.
"""
import json
import redis
from mudpi.extensions import Component, BaseExtension


NAMESPACE = 'sensor'
UPDATE_INTERVAL = 30

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = UPDATE_INTERVAL

    def init(self, config):
        self.config = config[self.namespace]
        
        self.manager.init(self.config)

        self.manager.register_component_actions('force_update', action='force_update')
        return True



class Sensor(Component):
    """ Example Sensor
        Returns a random number
    """

    """ Actions """
    def force_update(self, data=None):
        """ Force an update of the component. Useful for testing """
        self.update()
        self.store_state()
        return True