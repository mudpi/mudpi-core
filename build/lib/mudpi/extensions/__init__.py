""" 
    MudPi Components and Extensions Provided by Core
    Extensions can interact with events and add 
    components to MudPi through interfaces.  
"""
from mudpi.exceptions import MudPiError
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

    """ A unique string slug for the extension """
    namespace = None

    """ Time between component updates. Can be changed via config"""
    update_interval = DEFAULT_UPDATE_INTERVAL

    def __init__(self, mudpi):
        """ DO NOT OVERRIDE this method. Use init() instead """
        self.mudpi = mudpi
        self.config = None

        if self.namespace is not None:
            self.init_manager()

    """ Overrideable Methods to Extend """
    def init(self, config):
        """ Initialize the extension. Override this method to perform
            additional setup the extension may need. Make sure to return
            a boolean and assign the config to the extension.
        """
        self.config = config
        return True

    def validate_config(self, config):
        """ Validate the config for the extension. 
            Returns valid config or raises a ConfigError
            This gets called before `init()`.
        """
        return config


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
    def init_manager(self):
        """ Initalize a Manager for the Extension """
        self.manager = self.mudpi.cache[self.namespace] = ExtensionManager(self.mudpi, self.namespace, self.update_interval)

    def __repr__(self):
        """ Debug display of extension. """
        return f'<Extension {self.namespace} @ {self.update_interval}>'


class Component:
    """ Base class of all extension components in MudPi 

        Components will be dynamically loaded from the 
        config file. A component will either be updating
        state from device or listening/hanlding events.
    """

    """ Main MudPi Core Instance """
    mudpi = None

    """ Configuration dict passed in at init() """
    config = {}

    """ Set to true after the component completes `init()` """
    setup_complete = False

    """ Time it takes to complete one cycle, used to find slow components """
    processing_time = None

    """ Static Variable to Track Components """
    registered_components = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.registered_components[cls.__name__] = cls


    """ Base Constructor """
    def __init__(self, mudpi, config):
        """ Generally you shouldn't need to override this constructor,
            use init() instead. If you do override call `super().__init__()`
        """
        self.mudpi = mudpi
        self.config = config


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
        """ Returns a dict of additonal info about the component """
        return {}

    @property
    def available(self):
        """ Return if the component is available """
        return True

    @property
    def should_update(self):
        """ Boolean if component `update()` will be called each cycle """
        return True

    @property
    def classifier(self):
        """ Classification further describing it, effects the data formatting """
        return None


    """ Methods """
    def init(self, config):
        """ Perform component setup tasks with config """
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
    def store_state(self):
        """ Stores the current state into the MudPi state managers """
        if self.mudpi is None:
            raise MudPiError("MudPi Core instance was not provided!")

        if self.id is None:
            raise MudPiError(f"A unique id was not set on component {self.name}!")

        additional_data = {}

        if self.metadata:
            additional_data.update(self.metadata)

        if self.name:
            additional_data.update({'name': self.name})

        if self.classifier:
            additional_data.update({'classifier': self.classifier})

        data = self.mudpi.states.set(self.id, self.state, additional_data)
        print(data)

    def __repr__(self):
        """ Returns the instance representation for debugging. """
        return f'<Component {self.name}: {self.state}>'
