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

    def get(self, key):
        """ Get an item for the specified key """
        return self._registry[key]

    def exists(self, key):
        """ Return if key exists in the registry """
        return key in self._registry

    def register(self, key, value):
        """ Registers the value into the registry """
        if key not in self._registry:
            # Emit event of new registry
            pass
        self._registry[key] = value
        return value

    @property
    def length(self):
        return len(self.all())
    


class ActionRegistry(Registry):
    """ Database of actions available to MudPi from 
        user configs or components. 
        None = global
    """
    def register(self, action_key, func, namespace=None, validator=None):
        """ Register the action under the specified namespace. """
        namespace_registry = self._registry.setdefault(namespace, {})
        if action_key not in namespace_registry:
            # Emit event new action
            pass
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
            parsed_action['action'] = parts[-1]
        else:
            parsed_action['namespace'] = None
            parsed_action['action'] = action_call
        return parsed_action

    def call(self, action_call, action_data={}):
        """ Call an action from the registry 
            Format: {namespace}.{action}
        """
        command = self.parse_call(action_call)
        action = self._registry.get(command['namespace'], {}).get(command['action'])
        if not action:
            raise MudPiError("Call to action that doesn't exists!")
        validated_data = action.validate(action_data)
        if not validated_data:
            raise MudPiError("Call to action that doesn't exists!")
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