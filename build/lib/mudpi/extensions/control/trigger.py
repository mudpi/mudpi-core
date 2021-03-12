""" 
    Control Trigger Interface
    Monitors control state changes and 
    checks new state against any 
    thresholds if provided.
"""
from mudpi.utils import decode_event_data
from mudpi.exceptions import ConfigError
from mudpi.extensions import BaseInterface
from mudpi.extensions.trigger import Trigger
from mudpi.logger.Logger import Logger, LOG_LEVEL


class Interface(BaseInterface):

    def load(self, config):
        """ Load control Trigger component from configs """
        trigger = ControlTrigger(self.mudpi, config)
        if trigger:
            self.add_component(trigger)
        return True

    def validate(self, config):
        """ Validate the trigger config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('source'):
                raise ConfigError('Missing `source` key in Sensor Trigger config.')
            
        return config


class ControlTrigger(Trigger):
    """ A trigger that listens to states
        and checks for new state that 
        matches any thresholds.
    """

    # Used for onetime subscribe
    _listening = False
    
    
    def init(self):
        """ Listen to the state for changes """
        super().init()
        if self.mudpi.is_prepared:
            if not self._listening:
                # TODO: Eventually get a handler returned to unsub just this listener
                self.mudpi.events.subscribe('control', self.handle_event)
                self._listening = True
        return True

    """ Methods """
    def handle_event(self, event):
        """ Handle the event data from the event system """
        _event_data = decode_event_data(event)
        if _event_data.get('event'):
            try:
                if _event_data['event'] == 'ControlUpdated':
                    if _event_data['component_id'] == self.source:
                        _value = self._parse_data(_event_data["state"])
                        if self.evaluate_thresholds(_value):
                            self.active = True
                            if self._previous_state != self.active:
                                # Trigger is reset, Fire
                                self.trigger(_event_data)
                            else:
                                # Trigger not reset check if its multi fire
                                if self.frequency == 'many':
                                    self.trigger(_event_data)
                    else:
                        self.active = False
            except Exception as error:
                Logger.log(LOG_LEVEL["error"],
                           f'Error evaluating thresholds for trigger {self.id}')
                Logger.log(LOG_LEVEL["debug"], error)
        self._previous_state = self.active

    def unload(self):
        # Unsubscribe once bus supports single handler unsubscribes
        return

    def _parse_data(self, data):
        """ Get nested data if set otherwise return the data """
        if isinstance(data, dict):
            print('dict con')
            return data if not self.nested_source else data.get(self.nested_source, None)
        return data

