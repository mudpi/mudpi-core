""" 
    Controls Extension
    Controls are components like buttons, switches,
    potentiometers, etc. They are utilized to get 
    user input into the system.
"""
import datetime
from mudpi.extensions import Component, BaseExtension


NAMESPACE = 'control'

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = 0.5

    def init(self, config):
        self.config = config[self.namespace]
        
        self.manager.init(self.config)
        return True



class Control(Component):
    """ Base Control
        Base class for all controls. 
    """

    @property
    def id(self):
        """ Unique id or key """
        return self.config.get('key').lower()

    @property
    def name(self):
        """ Friendly name of control """
        return self.config.get('name') or f"{self.id.replace('_', ' ').title()}"

    @property
    def pin(self):
        """ The GPIO pin """
        return self.config.get('pin')

    @property
    def resistor(self):
        """ Set internal resistor to pull UP or DOWN """
        return self.config.get('resistor')

    @property
    def debounce(self):
        """ Used to smooth out ripples and false fires """
        return self.config.get('debounce')

    @property
    def type(self):
        """ Button, Switch, Potentiometer """
        return self.config.get('type', 'button').lower()

    @property
    def edge_detection(self):
        """ Return if edge detection is used """
        _edge_detection = self.config.get('edge_detection')
        if _edge_detection is not None:
            if _edge_detection == "falling" or _edge_detection == "fell":
                _edge_detection = "fell"
            elif _edge_detection == "rising" or _edge_detection == "rose":
                _edge_detection = "rose"
            elif _edge_detection == "both":
                _edge_detection = "both"
        return _edge_detection

    @property
    def invert_state(self):
        """ Set to True to make OFF state fire events instead of ON state """
        return self.config.get('invert_state', False)
    

    """ Methods """
    def fire(self):
        """ Fire a control event """
        event_data = {
            'event': 'ControlUpdated',
            'component_id': self.id,
            'type': self.type,
            'name': self.name,
            'updated_at': str(datetime.datetime.now().replace(microsecond=0)),
            'state': self.state,
            'invert_state': self.invert_state
        }
        self.mudpi.events.publish(NAMESPACE, event_data)