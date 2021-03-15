""" 
    Trigger Extension
    Causes actions based on situations created
    by events or state changed. Thresholds can 
    be set to define more specific paramerters.
"""
import datetime
import threading
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.extensions import Component, BaseExtension


NAMESPACE = 'trigger'

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = 0.05

    def init(self, config):
        self.config = config[self.namespace] #list of lists
        self.cache = self.mudpi.cache.setdefault(NAMESPACE, {})
        trigger_cache = self.cache.setdefault('triggers', {})

        # Manually load interfaces in order to load group triggers 
        # after all the other triggers because groups depend on 
        # all other triggers to be loaded first.
        _triggers, _groups = split_trigger_configs(self.config)
        self.manager.init(self.config, load_interfaces=False)
        if _triggers:
            self.manager.load_interfaces(_triggers)
        if _groups:
            self.manager.load_interfaces(_groups)

        self.manager.register_component_actions('trigger', action='trigger')
        return True


class Trigger(Component):
    """ Base Trigger
        Base class for all trigger interfaces
    """
    _actions = []

    # Used for trigger groups
    group = None

    # Thread safe active boolean 
    _active = threading.Event()

    # Used to fire triggers `once` or `many`
    _previous_state = False

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
    def source(self):
        """ Source key to get event data """
        return self.config.get('source', '').lower()

    @property
    def nested_source(self):
        """ If source is a dict, this is a key in it to get data """
        return self.config.get('nested_source', '').lower()

    @property
    def frequency(self):
        """ Set if should fire continuously while active 
            Options: `once` or `many`
        """
        return self.config.get('frequency', 'once')

    @property
    def thresholds(self):
        """ List of thresholds to check data against """
        return self.config.get('thresholds', [])

    @property
    def actions(self):
        """ Keys of actions to call if triggered """
        return self.config.get('actions', [])

    @property
    def active(self):
        """ Thread save active boolean """
        return self._active.is_set()

    @active.setter
    def active(self, value):
        """ Allows `self.active = False` while still being thread safe """
        if bool(value):
            self._active.set()
        else:
            self._active.clear()


    """ Methods """
    def init(self):
        """ Register Trigger to cache after __init__ """
        self.cache = self.mudpi.cache.setdefault(NAMESPACE, {})
        trigger_cache = self.cache.setdefault('triggers', {})
        trigger_cache[self.id] = self

    def check(self):
        """ Main trigger check loop to determine if 
            trigger should fire. """
        return

    def update(self):
        """ Update doesn't actually update the state 
            but is instead used for listening to events,
            tracking state / time change and triggering. """
        if self.mudpi.is_prepared:
            self.check()

    def evaluate_thresholds(self, value):
        """ Check if conditions are met to fire trigger """
        thresholds_passed = False
        for threshold in self.thresholds:
            comparison = threshold.get("comparison", "eq")
            
            if comparison == "eq":
                if value == threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "ne":
                if value != threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "gt":
                if value > threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "gte":
                if value >= threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "lt":
                if value < threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "lte":
                if value <= threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "ex":
                if value is not None:
                    thresholds_passed = True
                else:
                    thresholds_passed = False

        return thresholds_passed

    def fire(self, data={}):
        """ Fire an event """
        event_data = {
            'event': 'TriggerFired',
            'id': self.id,
            'name': self.name,
            'updated_at': str(datetime.datetime.now().replace(microsecond=0)),
            'state': self.state,
            'source': self.source,
        }
        event_data.update(data)
        self.mudpi.events.publish(NAMESPACE, event_data)

    def trigger(self, value=None):
        """ Fire off any actions or sequences """
        try:
            self.fire({'trigger_value': value})
            # Trigger the actions of the trigger
            for action in self.actions:
                if self.mudpi.actions.exists(action):
                    _data = value or {}
                    self.mudpi.actions.call(action, action_data=_data)

        except Exception as e:
            Logger.log(LOG_LEVEL["error"],
                       f"Error triggering action {self.id}. \n{e}")
        return

    def unload(self):
        """ Called during shutdown for cleanup operations """
        pass


""" Helper """
def split_trigger_configs(config):
    """ Seperate out group triggers from configs """
    _triggers = []
    _groups = []
    for conf in config:
        if not conf:
            continue
        if not isinstance(conf, list):
            conf = [conf]

        for entry in conf:
            try:
                # Search for interface property
                interface = entry.get("interface")
            except AttributeError as error:
                interface = None

        if interface is None:
            continue

        if interface == 'group':
            _groups.append(conf)
        else:
            _triggers.append(conf)

    return (_triggers, _groups)
