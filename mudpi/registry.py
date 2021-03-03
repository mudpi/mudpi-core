from mudpi.exceptions import MudPiError


class Registry:
    """ Key-Value database for managing object instances """
    def __init__(self, mudpi, name):
        self.mudpi = mudpi
        self.name = name
        self._registry = {}

    def all(self):
        """ Return all items in the registry """
        return self._registry

    def items(self):
        """ Dict items() helper for iteration """
        return self.all().items()

    def keys(self):
        """ Dict keys() helper for iteration """
        return self.all().keys()

    def get(self, key):
        """ Get an item for the specified key """
        return self._registry[key]

    def exists(self, key):
        """ Return if key exists in the registry """
        return key in self._registry

    def register(self, key, value):
        """ Registers the value into the registry """
        if key not in self._registry:
            self.mudpi.events.publish(self.name, {'event': 'Registered', 'action': key})
        self._registry[key] = value
        return value

    @property
    def length(self):
        return len(self.all())


class ComponentRegistry(Registry):
    """ Comopnent Database
        Stores components per namespace for MudPi
    """
    def get(self, component_id):
        """ Get an item for the specified key """
        try:
            component = [ component 
            for components in self._registry.values()
            for _id, component in components.items() 
            if _id in component_id ][0]
        except Exception as error:
            component = None
        return component

    def for_namespace(self, namespace=None):
        """ Get all the components for a given namespace """
        return self._registry[namespace]

    def exists(self, component_ids):
        """ Return if key exists in the registry """
        return any([ exists for components in self._registry.values()
            for exists in components 
            if exists in component_ids ])

    def register(self, component_id, component, namespace=None):
        """ Registers the component into the registry """
        namespace_registry = self._registry.setdefault(namespace, {})
        if component_id not in namespace_registry:
            self.mudpi.events.publish('core', {'event': 'ComponentRegistered', 'component': component_id, 'namespace': namespace})
        namespace_registry[component_id] = component
        return component

    def ids(self):
        """ Return all the registered component ids """
        return [ component.id 
            for components in self._registry.values()
            for component in components.values() ]


class ActionRegistry(Registry):
    """ Database of actions available to MudPi from 
        user configs or components. 
        None = global
    """
    def register(self, action_key, func, namespace=None, validator=None):
        """ Register the action under the specified namespace. """
        namespace_registry = self._registry.setdefault(namespace, {})
        if action_key not in namespace_registry:
            self.mudpi.events.publish('core', {'event': 'ActionRegistered', 'action': action_key, 'namespace': namespace})
        namespace_registry[action_key] = Action(func, validator)

    def for_namespace(self, namespace=None):
        """ Get all the actions for a given namespace """
        return self._registry[namespace]

    def exists(self, action_key):
        """ Return if action exists for given action command """
        action = self.parse_call(action_key)
        registry = self._registry.setdefault(action['namespace'], {})
        return action['action'] in registry

    def parse_call(self, action_call):
        """ Parse a command string and extract the namespace and action """
        parsed_action = {}
        if '.' in action_call:
            parts = action_call.split('.')
            parsed_action['namespace'] = parts[0]
            parsed_action['component'] = parts[1]
            parsed_action['action'] = parts[-1]
        else:
            parsed_action['namespace'] = None
            parsed_action['component'] = None
            parsed_action['action'] = action_call
        return parsed_action

    def call(self, action_call, namespace=None, action_data={}):
        """ Call an action from the registry 
            Format: {namespace}.{action} or 
                    {namespace}.{component}.{action}
        """
        command = self.parse_call(action_call)
        action = self._registry.get(namespace, {}).get(action_call)
        if not action:
            raise MudPiError("Call to action that doesn't exists!")
        validated_data = action.validate(action_data)
        if not validated_data and action_data:
            raise MudPiError("Action data was not valid!")
        self.mudpi.events.publish('core', {'event': 'ActionCall', 'action': action_call, 'data': action_data, 'namespace': namespace})
        action(data=validated_data)

class Action:
    """ A callback associated with a string """

    def __init__(self, func, validator):
        self.func = func
        self.validator = None

    def validate(self, data):
        if not self.validator:
            return data

        if callable(self.validator):
            return self.validator(data)

        return False

    def __call__(self, data=None, **kwargs):
        if self.func:
            if callable(self.func):
                if data:
                    return self.func(data)
                else:
                    return self.func()