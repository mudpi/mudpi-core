""" 
    Trigger Extension
    Causes actions based on situations created
    by events or state changed. Thresholds can 
    be set to define more specific paramerters.
"""
import json
import datetime
import threading
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.extensions import Component, BaseExtension
from mudpi.exceptions import MudPiError


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
        self.manager.register_interface_actions() # Manually call since load_interfaces is False
        return True


class Trigger(Component):
    """ Base Trigger
        Base class for all trigger interfaces
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
        return str(self.config.get('frequency', 'once')).lower()

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
        if value:
            self._active.set()
        else:
            self._active.clear()


    """ Methods """
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
        thresholds_passed = False if len(self.thresholds) > 0 else True
        for threshold in self.thresholds:
            if threshold.get("type", None) is not None:
                _type = str(threshold["type"])
                if _type not in ["int", "float", "str", "datetime", "list", "dict", "json"]:
                    _type = "int"
                try:
                    if _type == "int":
                        _threshold_value = int(threshold["value"])
                    if _type == "float":
                        _threshold_value = float(threshold["value"])
                    if _type == "str":
                        _threshold_value = str(threshold["value"])
                    if _type == "list" or _type == "dict" or _type == "json":
                        _threshold_value = json.loads(threshold["value"])
                    if _type == "datetime":
                        _format = threshold.get("format", "%I:%M %p")
                        _threshold_value = datetime.datetime.strptime(threshold["value"], _format)
                except Exception as error:
                    Logger.log(LOG_LEVEL["error"],
                       f"Error formatting threshold value to {_type}. \n{error}")

            if threshold.get("source_type", None) is not None:
                _source_type = str(threshold["source_type"])
                if _source_type not in ["int", "float", "str", "datetime", "list", "dict", "json"]:
                    _source_type = "int"
                try:
                    if _source_type == "int":
                        value = int(value)
                    if _source_type == "float":
                        value = float(value)
                    if _source_type == "str":
                        value = str(value)
                    if _source_type == "list" or _source_type == "dict" or _source_type == "json":
                        value = json.loads(value)
                    if _source_type == "datetime":
                        _source_format = threshold.get("source_format", "%I:%M %p")
                        value = datetime.datetime.strptime(value, _source_format)
                except Exception as error:
                    Logger.log(LOG_LEVEL["error"],
                       f"Error formatting threshold value to {_source_type}. \n{error}")

            comparison = threshold.get("comparison", "eq")

            if comparison == "eq" or comparison == "==":
                if value == threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "ne" or comparison == "!=":
                if value != threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "gt" or comparison == ">":
                if value > threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "gte" or comparison == ">=":
                if value >= threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "lt" or comparison == "<":
                if value < threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "lte" or comparison == "<=":
                if value <= threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "ex":
                if value is not None:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "is":
                if value is threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "not":
                if value is not threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False
            elif comparison == "in":
                if value in threshold["value"]:
                    thresholds_passed = True
                else:
                    thresholds_passed = False

        return thresholds_passed

    def fire(self, data={}):
        """ Fire an event """
        event_data = {
            'event': 'TriggerFired',
            'data': {
                'id': self.id,
                'name': self.name,
                'updated_at': str(datetime.datetime.now().replace(microsecond=0)),
                'state': self.state,
                'source': self.source
        }}
        event_data['data'].update(data)
        self.mudpi.events.publish(NAMESPACE, event_data)

    def trigger(self, value={}):
        """ Fire off any actions or sequences """
        try:
            self.fire({'trigger_value': value})
            # Trigger the actions of the trigger
            for action in self.actions:
                if isinstance(action, str):
                    _action = action
                elif isinstance(action, dict):
                    _action = action.get('action')
                    if _action is None:
                        raise MudPiError("No `action` passed in action data.")
                    _action_data = action.get('data', {})
                    if not isinstance(_action_data, dict):
                        _action_data = {'data': _action_data} 
                    value.update(_action_data)
                if self.mudpi.actions.exists(_action):
                    _data = value or {}
                    self.mudpi.actions.call(_action, action_data=_data)

        except Exception as e:
            Logger.log(LOG_LEVEL["error"],
                       f"Error triggering action {self.id}. \n{e}")
        return

    def unload(self):
        """ Called during shutdown for cleanup operations """
        pass


    """ Internal Methods
    Do not override """
    def _init(self):
        """ Set the trigger default settings """
        self._actions = []

        # Used for trigger groups
        self.group = None

        # Thread safe active boolean 
        self._active = threading.Event()

        # Used to fire triggers `once` or `many`
        self._previous_state = False

        # Register Trigger to cache
        self.cache = self.mudpi.cache.setdefault(NAMESPACE, {})
        trigger_cache = self.cache.setdefault('triggers', {})
        trigger_cache[self.id] = self


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


""" Helper """
def is_time_between(start_time, end_time, check_time):
    if start_time < end_time:
        return check_time >= start_time and check_time <= end_time
    else: #Over midnight
        return check_time >= start_time or check_time <= end_time