""" 
    Sensors Extension
    Sensors are components that gather data and make it 
    available to MudPi. Sensors support interfaces to 
    allow additions of new types of devices easily.
"""
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
    """ Base Sensor
        Base Sensor for all sensor interfaces
    """

    """ Properties """
    @property
    def id(self):
        """ Unique id or key """
        return self.config.get('key').lower()

    @property
    def name(self):
        """ Friendly name of control """
        return self.config.get('name') or f"{self.id.replace('_', ' ').title()}"

    @property
    def state(self):
        """ Return state for the sensor """
        return self._state


    """ Actions """
    def force_update(self, data=None):
        """ Force an update of the component. Useful for testing """
        self.update()
        self.store_state()
        return True