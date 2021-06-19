import os
import enum 
import time
import json
import threading

from mudpi import importer
from mudpi.config import Config
from mudpi.events import EventSystem
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.managers.state_manager import StateManager
from mudpi.exceptions import ConfigNotFoundError, ConfigFormatError
from mudpi.registry import Registry, ActionRegistry, ComponentRegistry
from mudpi.constants import DEFAULT_CONFIG_FILE, IMPERIAL_SYSTEM, METRIC_SYSTEM, __version__

class MudPi:
    """ 
    MudPi Core Class

    The core class of MudPi that holds all the important items
    to run the MudPi system.
    """
    def __init__(self, config_path=None):
        self.config_path = config_path
        self.config = None

        self.state = CoreState.not_running
        
        # Main data storage between extensions
        # eventually change this to helper and backup in redis
        self.cache = {}

        self.threads = {}
        self.thread_events = {
            # Event to signal system to shutdown
            'mudpi_running': threading.Event(),
            # Event to tell workers to begin working
            "core_running": threading.Event(),
            # Event to override MudPi and shutdown
            "shutdown_override": threading.Event()
        }

        # Setup the registries
        self.components = ComponentRegistry(self, 'components')
        self.extensions = Registry(self, 'extensions')
        self.workers = Registry(self, 'workers')
        self.actions = ActionRegistry(self, 'actions')

        # API
        self.api = None

        # System is Running
        self.thread_events['mudpi_running'].set()
        time.sleep(0.1)

    """ Properties """
    @property
    def is_prepared(self):
        """ Return if MudPi is prepared """
        return self.thread_events['mudpi_running'].is_set()

    @property
    def is_loaded(self):
        """ Return if MudPi is loaded or previously was. """
        return self.state in (CoreState.loaded, CoreState.stopped, CoreState.running)

    @property
    def is_loading(self):
        """ Return if MudPi is loaded or previously was. """
        return self.state in (CoreState.loading,)

    @property
    def is_running(self):
        """ Return if MudPi is running. """
        return self.state in (CoreState.running,)

    @property
    def is_stopping(self):
        """ Return if MudPi is stopping. """
        return self.state in (CoreState.stopping,)

    @property
    def unit_system(self):
        """ Return unit system for measurements. Default (IMPERIAL - 1) """
        return METRIC_SYSTEM if self.config.unit_system == 'metric' else IMPERIAL_SYSTEM


    """ Methods """
    def load_config(self, config_path=None):
        """ Load MudPi Configurations """
        if self.state == CoreState.preparing:
            """ Already loading """
            return

        self.state = CoreState.preparing

        config_path = config_path or self.config_path

        self.config = Config(config_path=config_path)

        if self.config.load_from_file(config_path):
            if config_path and config_path != self.config_path:
                self.config_path = config_path

            self.state = CoreState.prepared
            return True
        return False

    def save_config(self, config_path=None):
        """ Save Current MudPi Configurations """
        config_path = config_path or self.config_path

        if self.config.save_to_file(config_path):
            return True
        return False

    def load_core(self):
        """ Init the MudPi Core 
            - Load the State Machine
            - Prepare Event Bus (Drivers)
            - Prepare the Threads / Managers
            - Register Core Actions
        """
        if self.config is None:
            # Error Config not loaded call `load_config()` first
            return

        if self.is_running:
            # Error core already running
            return

        if self.state != CoreState.prepared:
            # Core is not waiting to load likely already loaded
            return

        if self.state == CoreState.loading:
            # Error core is already loading
            return

        self.state = CoreState.loading

        self.states = StateManager(self, self.config.get('mudpi', {}).get('events', {}).get('redis'))
        
        self.events = EventSystem(self.config.get('mudpi', {}).get('events', {}))
        self.events.connect()
        self.events.subscribe('action_call', self.actions.handle_call)

        self.actions.register('turn_on', self.start, 'mudpi')
        self.actions.register('turn_off', self.stop, namespace='mudpi')
        self.actions.register('shutdown', self.shutdown, namespace='mudpi')

        self.state = CoreState.loaded
        self.events.publish('core', {'event': 'Loaded'})
        return True

    def start(self, data=None):
        """ Signal MudPi to Start Once Loaded """
        if self.config is None:
            # Error Config not loaded call `load_config()` first
            return

        if self.is_running:
            # Error core already running
            return

        if not self.is_loaded:
            # Error core not loaded call `load_core()` first
            return

        self.events.publish('core', {'event': 'Starting'})
        self.state = CoreState.starting
        self.thread_events['core_running'].set()
        self.state = CoreState.running
        self.events.publish('core', {'event': 'Started'})
        return True

    def stop(self, data=None):
        """ Signal MudPi to Stop but Not UnLoad """
        self.events.publish('core', {'event': 'Stopping'})
        self.state = CoreState.stopping
        self.thread_events['core_running'].clear()
        self.state = CoreState.stopped
        self.events.publish('core', {'event': 'Stopped'})
        return True

    def shutdown(self, data=None):
        """ Signal MudPi to Stop and Unload """
        self.stop()
        self.events.publish('core', {'event': 'ShuttingDown'})
        self.unload_extensions()
        self.thread_events['mudpi_running'].clear()
        self.state = CoreState.not_running
        self.api.close()

        _closed_threads = []
        # First pass of threads to find out which ones are slower
        for thread_name, thread in self.threads.items():
            thread.join(2)
            if not thread.is_alive():
                _closed_threads.append(thread_name)
            else:
                Logger.log_formatted(LOG_LEVEL["warning"],
                   f"Worker {thread_name} is Still Stopping ", "Delayed", "notice")
                
        for _thread in _closed_threads:
            del self.threads[_thread]

        # Now attempt to clean close slow threads
        _closed_threads = []
        for thread_name, thread in self.threads.items():
            thread.join(3)
            if not thread.is_alive():
                _closed_threads.append(thread_name)
            else:
                Logger.log_formatted(LOG_LEVEL["error"],
                   f"Worker {thread_name} Failed to Shutdown ", "Not Responding", "error")


        self.events.publish('core', {'event': 'Shutdown'})
        self.events.disconnect()
        return True

    def start_workers(self):
        """ Start Workers and Create Threads """
        for key, worker in self.workers.items():
            _thread = worker.run()
            self.threads[key] = _thread
        return True

    def reload_workers(self):
        """ Reload Workers and Configurations """
        pass

    def unload_extensions(self):
        """ Cleanup all extensions for shutdown or restart """
        for key, extension in self.extensions.items():
            extension.unload()
        return True

    def restore_states(self):
        """ Restore previous components states on first boot """
        _comp_ids = self.components.ids()
        for state_id in self.states.ids():
            if state_id in _comp_ids:
                comp = self.components.get(state_id)
                comp.restore_state(self.states.get(state_id))
                Logger.log(LOG_LEVEL["debug"], f"Restored State for {state_id}")
            else:
                self.states.remove(state_id)

    def finalize_boot(self):
        """ Run post boot operations like caching data 
            and resource cleanup """
        self.cache_components()

    def cache_components(self):
        """ Cache all the current components """
        # TODO: make cache_manager
        self.states.redis.set("mudpi_component_ids", json.dumps(self.components.cache_string()))
        components = {}
        for namespace, _components in self.components.items():
            for _id, _component in _components.items():
                _json = _component.to_json()
                _json['namespace'] = namespace
                components[_component.id] = _json
        self.states.redis.set("mudpi_components", json.dumps(components))
        return components

    def core_loaded(self):
        """ Called after the core is loaded. All core systems and
            extensions are available. """
        self.api.register_route('/', self.get_mudpi)
        self.api.register_route('/config', self.get_config)
        self.api.register_route('/core/state', self.core_state)
        self.api.register_route('/core/stop', self.stop)
        self.api.register_route('/core/start', self.start)
        self.api.register_route('/core/shutdown', self.get_shutdown)
        self.api.register_route('/core/cache-components', self.cache_components)
        self.api.register_route('/components', self.get_components)
        self.api.register_route('/workers', self.get_workers)
        self.api.register_route('/states', self.get_states)
        self.api.register_route('/states/<component_id>', self.get_state)
        self.api.register_route('/actions', self.get_actions)


    """ API METHODS """
    def get_config(self):
        """ Return the config of the core. Used for api """
        return self.config.config

    def core_state(self):
        """ Return the state of the core. Used for api """
        return str(self.state)

    def get_components(self):
        """ Get all components. Used for api """
        return self.cache_components()

    def get_workers(self):
        """ Get all workers Used for api """
        _workers = {}
        for _id, worker in self.workers.items():
            _workers[_id] = worker.to_json()
        return _workers

    def get_states(self):
        """ Get all states. Used for api """
        _states = {}
        for _id, _state in self.states.states.items():
            _states[_id] = _state.to_dict()
        return _states

    def get_state(self, component_id=None):
        """ Get all states. Used for api """
        _state = None
        if component_id:
            if self.states.id_exists(component_id):
                _state = self.states.get(component_id).to_dict()
        return _state

    def get_actions(self):
        """ Get all actions. Used for api """
        actions = {}
        for _namespace, _actions in self.actions.all().items():
            for _id, _action in _actions.items():
                if _namespace:
                    actions[f".{_namespace}.{_id}"] = _id
                else:
                    actions[f".{_id}"] = _id

        return actions

    def get_shutdown(self):
        """ Override main thread and shutdown mudpi """
        self.thread_events['shutdown_override'].set()
        self.shutdown()
        self.unload_extensions()

    def get_mudpi(self):
        """ Handle the default route of the api """
        return __version__


class CoreState(enum.Enum):
    """ Enums for the current state of MudPi. """

    not_running = "NOT_RUNNING" # New MudPi instance
    preparing = "PREPARING"         # loading configs
    prepared = "PREPARED"         # configs loaded waiting to load core
    loading = "LOADING"           # core is loading
    loaded = "LOADED"           # core is loaded
    starting = "STARTING"       # core is starting
    running = "RUNNING"         # Core loaded and everying running
    stopping = "STOPPING"       # waing to shutdown
    stopped = "STOPPED"         # loaded but stopped (previously running)

    def __str__(self):
        return self.value