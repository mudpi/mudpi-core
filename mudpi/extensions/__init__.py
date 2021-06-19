""" 
    MudPi Components and Extensions Provided by Core
    Extensions can interact with events and add 
    components to MudPi through interfaces.  
"""
import inspect
from mudpi.workers import Worker
from mudpi.exceptions import MudPiError
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.constants import DEFAULT_UPDATE_INTERVAL
from mudpi.managers.extension_manager import ExtensionManager


class BaseExtension:
    """ Base class of all MudPi Extensions. 
        Extensions will contain components with interfaces.
        The extension is resposible for its own config setup.
    """
    registered_extensions = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.namespace:
            cls.registered_extensions[cls.namespace] = cls

    # A unique string slug for the extension 
    namespace = None

    # Time between component updates. Can be changed via config
    update_interval = None # DEFAULT_UPDATE_INTERVAL

    def __init__(self, mudpi):
        """ DO NOT OVERRIDE this method. Use init() instead """
        self.mudpi = mudpi
        self.config = None

        if self.namespace is not None:
            self.load_manager()

    """ Overrideable Methods to Extend """
    def init(self, config):
        """ Initialize the extension. Override this method to perform
            additional setup the extension may need. Make sure to return
            a boolean and assign the config to the extension.
        """
        self.config = config
        return True

    def validate(self, config):
        """ Validate the config for the extension. 
            Returns valid config or raises a ConfigError
            This gets called before `init()`.
        """
        return config

    def unload(self):
        """ Cleanup any data in memory and release 
            system resources. This is called to 
            just before removing the extension.
        """
        pass


    """ Lifecycle Function Hooks """
    def extension_imported(self, *args, **kwargs):
        """ Will be called after extension import completes 
            args: {importer}
        """
        pass

    def extension_initialized(self, *args, **kwargs):
        """ Will be called after extension `init()` completes 
            args: {importer, validated_config}
        """
        pass

    def extension_registered(self, *args, **kwargs):
        """ Will be called after extension added to MudPi """
        pass

    def extension_removed(self, *args, **kwargs):
        """ Will be called before extension is removed from MudPi """
        pass


    """ INTERNAL METHODS: DO NOT OVERRIDE! 
        These methods and properties are used internally.
    """
    def load_manager(self):
        """ Initalize a Manager for the Extension """
        self.manager = ExtensionManager(self)

    def __repr__(self):
        """ Debug display of extension. """
        return f'<Extension {self.namespace} @ {self.update_interval}>'


class BaseInterface:
    """ Base class of all MudPi Interfaces. 
        Interfaces connect to components to manage,
        monitor and collect data for the extension.
    """

    """ Time between component updates. Can be changed via config"""
    update_interval = None # DEFAULT_UPDATE_INTERVAL

    def __init__(self, mudpi, namespace, interface_name, update_interval=None):
        """ DO NOT OVERRIDE this method. Use load() instead """
        self.mudpi = mudpi
        self.namespace = namespace
        self.type = interface_name
        self.update_interval = update_interval or self.update_interval

        self.extension = None
        self.config = None
        self.worker = None

    """ Overrideable Methods to Extend """
    def load(self, config):
        """ This will be called per config entry that 
            references the interface. Process the config
            to add components, listen for events, etc. 
        """
        return True

    def validate(self, config):
        """ Validate the config for the interface. 
            Returns valid config or raises a ConfigError
            This gets called before `load()`.
        """
        return config

    def register_actions(self):
        """ Register any actions on an interface
            level. This is called after interfaces
            load to allow all components to register.
        """
        return True

    """ INTERNAL METHODS: DO NOT OVERRIDE! 
        These methods and properties are used internally.
    """
    @property
    def key(self):
        """ Create a composite key """
        return f"{self.namespace}.{self.type}.{self.update_interval}"

    def add_component(self, component):
        """ Add a component for the interface """
        if not _is_component(component):
            raise MudPiError(f"Passed non-component to add_component for {self.namesapce}.")

        # Worker is loaded here to prevent empty workers without components
        if self.worker is None:
            self.worker = self.load_worker()

        try:
            if component.id is None:
                Logger.log(
                    LOG_LEVEL["debug"], f"Interface {self.namespace}:{self.type} component did not define `id`."
                )
                return False
            if component.id in self.worker.components:
                Logger.log(
                    LOG_LEVEL["debug"], f"Interface {self.namespace}:{self.type} component id ({component.id}) already registered."
                )
                return False
            component.namespace = self.namespace
            component.interface = self.type
            self.worker.components[component.id] = self.mudpi.components.register(component.id, component, self.namespace)
            component.component_registered(mudpi=self.mudpi, interface=self)
            return True
        except Exception as error:
            Logger.log(
                LOG_LEVEL["debug"], f"Interface {self.namespace}:{self.type} unknown error adding component.\n{error}"
            )

    def load_worker(self):
        """ Load a worker for any interface components """
        return Worker(self.mudpi, {'key': self.key, 'update_interval': self.update_interval})


    def register_component_actions(self, action_key, action):
        """ Register action for component. 
            If no components specified it calls 
            all components for this interface
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
                _components = [ _comp 
                    for _comp in self.mudpi.components.for_namespace(self.namespace).values() 
                    if _comp.interface == self.type ]

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

        _comps = [ _comp 
                    for _comp in self.mudpi.components.for_namespace(self.namespace).values() 
                    if _comp.interface == self.type ]

        for component in _comps:
            try:
                func = getattr(component, action)
                if callable(func):
                    # Register component only global action
                    self.mudpi.actions.register(f'{component.id}.{action_key}', func)
            except Exception as error:
                continue

        self.mudpi.actions.register(action_key, handle_namespace_action, f'{self.namespace}.{self.type}')

    def __repr__(self):
        """ Debug display of extension. """
        return f'<Interface {self.namespace}:{self.type} @ {self.update_interval}>'


class Component:
    """ Base class of all extension components in MudPi 

        Components will be dynamically loaded by extensions
        based on configs. A component will either be updating
        state from device or listening / hanlding events.
    """

    """ Main MudPi Core Instance """
    mudpi = None

    """ Configuration dict passed in at init() """
    config = {}

    """ Static Variable to Track Components """
    registered_components = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.registered_components[cls.__name__] = cls


    """ Base Constructor """
    def __init__(self, mudpi, config={}):
        """ Generally you shouldn't need to override this constructor,
            use init() instead. If you do override call `super().__init__()`
        """
        self.mudpi = mudpi
        self.config = config

        """ Set to true after the component completes `init()` """
        self.setup_complete = False

        """ Time it takes to complete one cycle, used to find slow components """
        self.processing_time = None

        """ Variable suggestion to use for state """
        self._state = None
        
        """ Keep last event cached to prevent duplicate event fires """
        self._last_event = {}

        """ Used for component Enable/Disable """
        self._available = True

        # Developer _init so users don't need to call super().init()
        self._init()

        # Init hook for components
        self.init()

        self.component_initialized()

    """ Properties 
    Override these depending on desired component functionality
    """
    @property
    def id(self):
        """ Return a unique id for the component """
        return None

    @property
    def name(self):
        """ Return the display name of the component """
        return None
    
    @property
    def state(self):
        """ Return the state of the component (from memory, no IO!) """
        return None

    @property
    def metadata(self):
        """ Returns a dict of additonal info about the component 
            This is mainly used by the dashboard / frontend
        """
        return {}

    @property
    def available(self):
        """ Return if the component is available """
        return self._available

    @property
    def should_update(self):
        """ Boolean if component `update()` will be called each cycle """
        return True

    @property
    def classifier(self):
        """ Classification further describing it, effects the data formatting """
        return None

    @property
    def json_attributes(self):
        """ Return a list of attribute keys to export in json """
        return [
            'id',
            'name',
            'state',
            'available',
            'should_update',
            'classifier'
        ]


    """ Methods """
    def init(self):
        """ Called at end if __init__ and
            used for additional setup tasks
        """
        pass

    def update(self):
        """ Get data, run tasks, update state, called during 
            each work cycle. Don't block longer than update_interfal 
            to avoid being flagged as a slow component. """
        pass

    def reload(self):
        """ Reload the component if supported """
        pass

    def unload(self):
        """ Unload the component and cleanup """
        pass

    def restore_state(self, state):
        """ Reload the previous state from state manager """
        pass


    """ Lifecycle Function Hooks """
    def component_initialized(self, *args, **kwargs):
        """ Will be called after component `init()` completes """
        pass

    def component_registered(self, *args, **kwargs):
        """ Will be called after component added to MudPi """
        pass

    def component_removed(self, *args, **kwargs):
        """ Will be called before component is removed from MudPi """
        pass


    """ INTERNAL METHODS: DO NOT OVERRIDE! 
        These methods and properties are used internally.
    """
    def _init(self):
        """ Used for additional setup tasks. 
            This is used by developers to hook into
            __init__ instead of using the init() """
        pass

    def store_state(self):
        """ Stores the current state into the MudPi state managers """
        if self.mudpi is None:
            raise MudPiError("MudPi Core instance was not provided!")

        if self.id is None:
            raise MudPiError(f"A unique id was not set on component {self.name}!")

        additional_data = {}

        # Used for fontend
        if self.metadata:
            additional_data.update(self.metadata)

        if self.name:
            additional_data.update({'name': self.name})

        if self.classifier:
            additional_data.update({'classifier': self.classifier})

        data = self.mudpi.states.set(self.id, self.state, additional_data)

    def to_json(self):
        """ Returns a dict to be json encoded of component data """
        component_json = {}
        _core_attributes = [
            'id',
            'name',
            'state',
            'available',
            'should_update',
            'classifier'
        ]
        for attribute, data in self.config.items():
            component_json[attribute] = data

        attributes = list(set(_core_attributes + self.json_attributes))
        for attribute in attributes:
            component_json[attribute] = getattr(self, attribute)
            
        return component_json

    def __repr__(self):
        """ Returns the instance representation for debugging. """
        return f'<Component {self.name}: {self.state}>'

""" Helpers """
def _is_component(cls):
    """ Check if a class is a MudPi component.
        Accepts class or instance of class 
    """
    if not inspect.isclass(cls):
        if hasattr(cls, '__class__'):
            cls = cls.__class__
        else:
            return False
    return issubclass(cls, Component)