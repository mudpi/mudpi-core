""" 
MudPi Core Manager

Handles any functions used to prepare resources for 
the MudPi system before booting. The manager will
need a MudPi core instance to perform operations.
"""

import os
import sys
import time
import redis
import socket
from mudpi import importer, utils, core
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.exceptions import ExtensionNotFound, RecursiveDependency, ConfigError, MudPiError, ConfigNotFoundError
from mudpi.constants import FONT_RESET, FONT_GREEN, FONT_RED, FONT_YELLOW, RED_BACK, YELLOW_BACK, FONT_PADDING

class CoreManager:
    """ Core Manager Class """

    def __init__(self, mudpi=None):
        self.mudpi = mudpi or core.MudPi()

    def load_mudpi_from_config(self, config_path):
        """ Load the MudPi Core from a validated config """
        self.validate_config(config_path)
        self.config_path = config_path
        # Config valid, attempt to parse in the data
        self.mudpi.load_config(config_path=config_path)

        return self.mudpi

    def load_mudpi_core(self):
        """ Load the Core systems for MudPi """
        self.mudpi.load_core()
        time.sleep(0.1)
        return True

    def initialize_logging(self, config=None):
        """ Enable logging module and attach to MudPi """
        config = config or self.mudpi.config.to_dict()
        Logger.logger = self.mudpi.logger = Logger(config)
        time.sleep(0.05)
        Logger.log_formatted(
            LOG_LEVEL["info"], "Initializing Logger ", "Complete", 'success'
        )
        Logger.log_to_file(LOG_LEVEL["debug"], "Dumping the config file: ")
        for index, config_item in config.items():
            Logger.log_to_file(LOG_LEVEL["debug"], f'{index}: {config_item}')
        Logger.log_to_file(LOG_LEVEL["debug"], "End of config file dump!\n")

    def load_all_extensions(self, config=None):
        """ Import extensions for MudPi based on loaded Config """
        config = config or self.mudpi.config.config

        if not self.import_config_dir():
            raise ConfigError("Could not import the config_path and load extensions")


        Logger.log_formatted(
            LOG_LEVEL["warning"], "Detecting Configurations", "Pending", 'notice'
        )

        core_configs = ['mudpi', 'logging', 'debug']
        # Get all the non-core extensions to load
        extensions_to_load = [ 
            key 
            for key in config.keys() 
            if key not in core_configs
        ]
        Logger.log_formatted(
            LOG_LEVEL["warning"], f"Detected {len(extensions_to_load)} Non-Core Configurations", "Complete", 'success'
        )
        
        Logger.log_formatted(
            LOG_LEVEL["warning"], f"Preparing {len(extensions_to_load)} Configurations to be Loaded ", "Pending", 'notice'
        )

        extension_count = len(extensions_to_load)
        extension_error_count = 0
        extensions_with_errors = []
        _extensions_needing_load = extensions_to_load
        _importer_cache = {}
        disabled_cache = self.mudpi.cache.setdefault("disabled_namespaces", {})
        # A loop to fetch all extensions and their dependencies 
        while _extensions_needing_load:
            _extension_load_list = _extensions_needing_load.copy()
            _extensions_needing_load = []

            extension_importers = []

            # Load extension importers for detected configs
            for key in _extension_load_list:
                try:
                    extension_importer = importer.get_extension_importer(self.mudpi, key)
                except ExtensionNotFound as error:
                    extension_importer = None
                    extensions_to_load.remove(key)
                    extension_error_count += 1
                    extensions_with_errors.append(key)
                    disabled_cache[key] = 'Not Found'

                if isinstance(extension_importer, importer.ExtensionImporter):
                    extension_importers.append(extension_importer)

            # Loop through importers and prepare extensions for setup
            for extension_importer in extension_importers:
                # Load dependenies if there are any
                if not extension_importer.dependencies_ready:
                    extension_importer.import_dependencies()

                # Check if all the component dependencies imported
                if extension_importer.dependencies_ready:
                    _importer_cache[extension_importer.namespace] = extension_importer

                    for dependency in extension_importer.loaded_dependencies:
                        if dependency in extensions_to_load:
                            continue

                        extensions_to_load.append(dependency)
                        _extensions_needing_load.append(dependency)

        if extension_error_count > 0:
            Logger.log_formatted(
                LOG_LEVEL["warning"], f"Errors Preparing {extension_error_count} Configurations ", "Errors", 'error'
            )
            Logger.log(
                "debug",
                f'Failed to prepare: {FONT_RED}{", ".join(extensions_with_errors)}{FONT_RESET}'
            )

        if len(extensions_to_load):
            Logger.log_formatted(
                LOG_LEVEL["warning"], f"{len(extensions_to_load)} Configurations Ready to Load ", "Complete", 'success'
            )

            Logger.log(LOG_LEVEL["debug"], f'{" Load Extensions ":_^{FONT_PADDING+8}}')
            Logger.log_formatted(
                LOG_LEVEL["warning"], f"Loading {len(extensions_to_load)} Configurations into Extensions ", "Pending", 'notice'
            )
            Logger.log(
                LOG_LEVEL["debug"],
                f'Loading: {FONT_YELLOW}{", ".join(extensions_to_load)}{FONT_RESET}'
            )

        #  Import and setup the extensions
        self.load_extensions(extensions_to_load, config)

        # Cache important data like requirements installed
        self.mudpi.states.cache()

        return self.mudpi.extensions.all()

    def load_extensions(self, extensions, config):
        """ Initialize a list of extensions with provided config """

        disabled_cache = self.mudpi.cache.setdefault("disabled_namespaces", {})

        #  Import and setup the extensions
        for extension in extensions:
            if extension not in disabled_cache:
                try:
                    extension_importer = importer.get_extension_importer(self.mudpi, extension)
                    if not extension_importer.import_extension(config):
                        disabled_cache[extension] = 'Failed Import'
                except Exception as error:
                    # Ignore errors
                    Logger.log(
                        LOG_LEVEL["debug"], error
                    )
                    continue
        return True

    def import_config_dir(self):
        """ Add config dir to sys path so we can import extensions """
        if self.mudpi.config_path is None:
            Logger.log(
                LOG_LEVEL["error"],
                f'{RED_BACK}Could not import config_path - No path was set.{FONT_RESET}'
            )
            return False
        if self.mudpi.config_path not in sys.path:
            sys.path.insert(0, self.mudpi.config_path)
        return True

    def validate_config(self, config_path):
        """ Validate that config path was provided and a file """
        if not os.path.exists(config_path):
            raise ConfigNotFoundError(f"Config File Doesn't Exist at {config_path}")
            return False
        else: 
            # No config file provided just a path
            pass

        return True

    def debug_dump(self, cache_dump=False):
        """ Dump important data from MudPi instance for debugging mode """
        if cache_dump:
            Logger.log(
                LOG_LEVEL["debug"],
                f'{YELLOW_BACK}MUDPI CACHE DUMP{FONT_RESET}'
            )
            for key in self.mudpi.cache.keys():
                Logger.log(
                    LOG_LEVEL["debug"],
                    f"{FONT_YELLOW}{key}:{FONT_RESET} {self.mudpi.cache[key]}"
                )

        Logger.log(
            LOG_LEVEL["debug"],
            f'{YELLOW_BACK}MUDPI LOADED EXTENSIONS{FONT_RESET}'
        )
        for ext in self.mudpi.extensions.all():
            ext = self.mudpi.cache.get("extension_importers", {}).get(ext)
            Logger.log(
                LOG_LEVEL["debug"],
                f"Namespace: {FONT_YELLOW}{ext.namespace}{FONT_RESET}\n{ext.description}\n{ext.documentation or 'https://mudpi.app/docs'}"
            )      

        Logger.log(
            LOG_LEVEL["debug"],
            f'{YELLOW_BACK}MUDPI DISABLED EXTENSIONS{FONT_RESET}'
        )
        for key, reason in self.mudpi.cache.get('disabled_namespaces', {}).items():
            Logger.log(
                LOG_LEVEL["debug"],
                f"{FONT_YELLOW}{key:<12}{FONT_RESET} {reason}"
            )

        if self.mudpi.components.all():
            Logger.log(
                LOG_LEVEL["debug"],
                f'{YELLOW_BACK}MUDPI REGISTERED COMPONENTS{FONT_RESET}'
            )
            Logger.log(
                LOG_LEVEL["debug"],
                f"{'COMPONENT':<16}   {'ID':<16}   NAME\n{'':-<60}"
            )
            for namespace, comps in self.mudpi.components.items():
                for comp in comps.values():
                    Logger.log(
                        LOG_LEVEL["debug"],
                        f"{comp.__class__.__name__:<16} | {comp.id:<16} | {comp.name}"
                    )

        if self.mudpi.actions.all():
            Logger.log(
                LOG_LEVEL["debug"],
                f'{YELLOW_BACK}MUDPI REGISTERED ACTIONS{FONT_RESET}'
            )
            Logger.log(
                LOG_LEVEL["debug"],
                f"{'ACTION CALL':<48}   {'ACTION':<32}\n{'':-<80}"
            )
            for namespace, actions in self.mudpi.actions.items():
                for key, action in actions.items():
                    action_command = f"{namespace or ''}.{key}"
                    Logger.log(
                        LOG_LEVEL["debug"],
                        f"{action_command:<48} | {key:<32}"
                    )

        print(f'{"":_<{FONT_PADDING+8}}')

    def shutdown(self):
        """ Shutdown MudPi and cleanup """
        self.mudpi.shutdown()
        self.mudpi.unload_extensions()