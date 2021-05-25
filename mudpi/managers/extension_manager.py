import inspect
from mudpi import importer, extensions
from mudpi.exceptions import MudPiError
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.constants import DEFAULT_UPDATE_INTERVAL

class ExtensionManager:
    """ Extension Manager

        Controls components and interfaces for an extensions.
        Helps setup new interfaces and coordinate workers for
        any components. Not all extensions need the manager.
    """

    def __init__(self, extension):
        self.extension = extension
        self.mudpi = extension.mudpi
        self.namespace = extension.namespace
        self.update_interval = extension.update_interval if extension.update_interval \
            is not None else DEFAULT_UPDATE_INTERVAL
        # Config gets set in the `init()` because not all extensions have base config
        self.config = None
        self.interfaces = {}
        # Create an default interface for the extension components without interfaces 
        self.create_interface(self.namespace)
        self.importer = importer.get_extension_importer(self.mudpi, self.namespace)

        self.mudpi.cache.setdefault('extension_managers', {})[self.namespace] = self

    """ Properties """
    @property
    def components(self):
        """ Returns a list of all components for all interfaces """
        return [ component
            for interface in self.interfaces.values()
            for worker in interface.workers 
            for component in worker.components ]
    
    """ Methods """
    def init(self, config, load_interfaces=True):
        """ Parses the config and setups up any interfaces detected """
        self.config = config
        if load_interfaces:
            self.load_interfaces(config)
            self.register_interface_actions()

    def load_interfaces(self, config):
        """ Load interfaces from config """
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

            _interface = None
            try:
                _interface = self.find_or_create_interface(interface, entry)
                if not _interface:
                    raise MudPiError(f'Interface {interface} failed to load.')
            except MudPiError as error:
                Logger.log(
                    LOG_LEVEL["debug"], f"Extension Manager {self.namespace}:{interface} {error}."
                )
                continue

            if _interface.__class__.load == _interface.__class__.__bases__[0].load:
                Logger.log(
                    LOG_LEVEL["debug"], f"Notice: Extension {self.namespace} Interface {_interface_name} did not define load() method."
                )
            result = _interface.load(entry)
            if not result: 
                Logger.log(
                    LOG_LEVEL["error"], f'Interface {self.namespace}.{self.interface_name} `load()` failed to return True.'
                )
        return True

    def create_interface(self, interface_name, interface=None, update_interval=None, extension=None):
        """ Create a new interface manager and return it """
        cache = self.mudpi.cache.setdefault("interfaces", {})

        if interface:
            if not hasattr(interface, 'Interface'):
                raise MudPiError(f'No `Interface()` class to load for {self.namespace}:{interface_name}.')

        if update_interval is None:
            if interface:
                if interface.Interface.update_interval is not None:
                    update_interval = interface.Interface.update_interval
            else:
                update_interval = self.update_interval

        key = f'{self.namespace}.{interface_name}.{update_interval}'

        if key in cache:
            return cache[key]

        if interface:
            if _is_interface(interface.Interface):
                cache[key] = interface.Interface(self.mudpi, self.namespace, interface_name, update_interval)
                # Inject the extension here since its not needed in the init during validation
                cache[key].extension = extension or self.extension
                return cache[key]
            else:
                raise MudPiError(f'Interface {self.namespace}:{interface_name} does not extend BaseInterface.')

        cache[key] = extensions.BaseInterface(self.mudpi, self.namespace, interface_name, update_interval)
        # Inject the extension here since its not needed in the init during validation
        cache[key].extension = extension or self.extension
        self.interfaces[key] = cache[key]
        return cache[key]

    def find_or_create_interface(self, interface_name, interface_config = {}):
        """ Add an interface for an Extension if it isn't loaded """

        if self.config is None:
            raise MudPiError("Config was null in extension manager. Call `init(config)` first.")

        # Get the interface and extension
        interface, extension = self.importer.prepare_interface_and_import(interface_name)

        if not interface:
            raise MudPiError(f'Interface {interface_name} failed to prepare for import.')

        update_interval = interface_config.get('update_interval')

        if not update_interval:
            if hasattr(interface, 'Interface'):
                if interface.Interface.update_interval is not None:
                    update_interval = interface.Interface.update_interval

        if not update_interval:
            update_interval = self.update_interval

        # Create a composite key based on interface and update intervals
        interface_key = f'{self.namespace}.{interface_name}.{update_interval}'

        # Check if interface is already added
        if interface_key in self.interfaces:
            return self.interfaces[interface_key]
    
        self.interfaces[interface_key] = self.create_interface(interface_name, interface, update_interval, extension=extension)
        return self.interfaces[interface_key]

    def add_component(self, component, interface_name=None):
        """ Delegate register component using the specified interface. """
        interface_name = interface_name or self.namespace
        interface_key = f'{self.namespace}.{interface_name}.{self.update_interval}'
        if interface_key not in self.interfaces:
            raise MudPiError(f"Attempted to add_component to interface {interface_key} that doesn't exist.")

        return self.interfaces[interface_key].add_component(component)

    def register_component_actions(self, action_key, action):
        """ Register action for component. 
            If no components specified it calls all components
        """

        def handle_namespace_action(data=None):
            """ Wrapper for action call to delegate to components """
            _components = []
            _ids = []
            if data:
                try:
                    _ids = data.get('components', [])
                except Exception as error:
                    _ids = []
            if _ids:
                for _id in _ids:
                    component = self.mudpi.components.get(_id)
                    if component:
                        _components.append(component)
            else:
                _components = self.mudpi.components.for_namespace(self.namespace).values()

            for component in _components:
                try:
                    func = getattr(component, action)
                    if callable(func):
                        if data:
                            func(data)
                        else:
                            func()
                except Exception as error:
                    continue
            return True

        for component in self.mudpi.components.for_namespace(self.namespace).values():
            try:
                func = getattr(component, action)
                if callable(func):
                    # Register component only global action
                    self.mudpi.actions.register(f'{component.id}.{action_key}', func)
            except Exception as error:
                continue

        self.mudpi.actions.register(action_key, handle_namespace_action, self.namespace)

    def register_interface_actions(self):
        """ Register any actions on an interface level """
        for interface in self.interfaces.values():
            interface.register_actions()

    def __repr__(self):
        """ Representation of the manager. (Handy for debugging) """
        return f"<ExtensionManager {self.namespace} @ {self.update_interval}s>"


""" Helper """
def _is_interface(cls):
    """ Check if a class is a MudPi Extension.
        Accepts class or instance of class 
    """
    if not inspect.isclass(cls):
        if hasattr(cls, '__class__'):
            cls = cls.__class__
        else:
            return False
    return issubclass(cls, extensions.BaseInterface)