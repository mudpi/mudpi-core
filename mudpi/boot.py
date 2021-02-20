""" 
MudPi Boot Functions

These are the functions used to prepare resources for 
the MudPi system before booting. All the functions
take a MudPi core instance to perform operations.
"""

import os
import sys
import time
import redis
from mudpi import importer, utils
from importlib import import_module
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.exceptions import ExtensionNotFound, RecursiveDependency, ConfigError, MudPiError
from mudpi.constants import FONT_RESET, FONT_GREEN, FONT_RED, FONT_YELLOW, \
                    RED_BACK, FONT_PADDING


def mudpi_from_config(mudpi, config_path):
    """ Load the MudPi Core from a validated config """
    validate_config(config_path)

    # Config valid, attempt to parse in the data
    mudpi.load_config(config_path=config_path)

    return mudpi


def initialize_logging(mudpi, config=None):
    """ Enable logging module and attach to MudPi """
    config = config or mudpi.config.to_dict()
    Logger.logger = mudpi.logger = Logger(config)
    time.sleep(0.05)
    Logger.log_formatted(
        LOG_LEVEL["info"], "Initializing Logger ", "Complete", 'success'
    )
    Logger.log_to_file(LOG_LEVEL["debug"], "Dumping the config file: ")
    for index, config_item in config.items():
        Logger.log_to_file(LOG_LEVEL["debug"], f'{index}: {config_item}')
    Logger.log_to_file(LOG_LEVEL["debug"], "End of config file dump!\n")


def load_all_extensions(mudpi, config=None):
    """ Import extensions for MudPi based on loaded Config """
    config = config or mudpi.config.config

    if not import_config_dir(mudpi):
        raise ConfigError("Could not import the config_path and load extensions")


    Logger.log_formatted(
        LOG_LEVEL["warning"], "Detecting Extensions with Configurations", "Pending", 'notice'
    )

    core_extensions = ['mudpi', 'logging']
    # Get all the non-core extensions to load
    extensions_to_load = [ 
        key 
        for key in config.keys() 
        if key not in core_extensions
    ]
    Logger.log_formatted(
        LOG_LEVEL["warning"], f"Detected {len(extensions_to_load)} Extensions with Configurations", "Complete", 'success'
    )
    
    Logger.log_formatted(
        LOG_LEVEL["warning"], f"Preparing {len(extensions_to_load)} Configured Extensions ", "Pending", 'notice'
    )
    Logger.log(
        LOG_LEVEL["debug"],
        f'Preparing extensions: {FONT_YELLOW}{", ".join(extensions_to_load)}{FONT_RESET}'
    )

    extension_count = len(extensions_to_load)
    extension_error_count = 0
    extensions_with_errors = []
    _extensions_needing_load = extensions_to_load
    _importer_cache = {}
    # A loop to fetch all extensions and their dependencies 
    while _extensions_needing_load:
        _extension_load_list = _extensions_needing_load.copy()
        _extensions_needing_load = []

        extension_importers = []

        # Load extension importers for detected configs
        for key in _extension_load_list:
            try:
                extension_importer = importer.get_extension_importer(mudpi, key)
            except ExtensionNotFound as error:
                extension_importer = None
                extensions_to_load.remove(key)
                extension_error_count += 1
                extensions_with_errors.append(key)

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
            LOG_LEVEL["warning"], f"Errors Preparing {extension_error_count} Extensions ", "Errors", 'error'
        )
        Logger.log(
            "debug",
            f'Failed to prepare: {FONT_YELLOW}{", ".join(extensions_with_errors)}{FONT_RESET}'
        )

    if len(extensions_to_load):
        Logger.log_formatted(
            LOG_LEVEL["warning"], f"Preparing {len(extensions_to_load)} Configured Extensions ", "Complete", 'success'
        )

        Logger.log_formatted(
            LOG_LEVEL["warning"], f"Loading {len(extensions_to_load)} Successfully Prepared Extensions ", "Pending", 'notice'
        )
        Logger.log(
            LOG_LEVEL["debug"],
            f'Loading extensions: {FONT_YELLOW}{", ".join(extensions_to_load)}{FONT_RESET}'
        )

    #  Import and setup the extensions
    init_extensions(mudpi, extensions_to_load, config)

    return mudpi.extensions.all()


def init_extensions(mudpi, extensions, config):
    """ Initialize a list of extensions with provided config """

    #  Import and setup the extensions
    for extension in extensions:
        try:
            extension_importer = importer.get_extension_importer(mudpi, extension)
            extension_importer.import_extension(config)
        except Exception as error:
            # Ignore errors
            Logger.log(
                LOG_LEVEL["debug"], error
            )
            continue
    return True

def import_config_dir(mudpi):
    """ Add config dir to sys path so we can import extensions """
    if mudpi.config_path is None:
        Logger.log(
            LOG_LEVEL["error"],
            f'{RED_BACK}Could not import config_path - No path was set.{FONT_RESET}'
        )
        return False
    if mudpi.config_path not in sys.path:
        sys.path.insert(0, mudpi.config_path)
    return True

def load_mudpi_core(mudpi):
    """ Load the Core systems for MudPi """
    mudpi.load_core()
    time.sleep(0.1)
    return True

def validate_config(config_path):
    """ Validate that config path was provided and a file """
    if not os.path.exists(config_path):
        raise ConfigNotFoundError(f"Config File Doesn't Exist at {config_path}")
        return False
    else: 
        # No config file provided just a path
        pass

    return True