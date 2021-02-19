""" MudPi Importer
    
    Loads built in extensions and custom extensions dynamically 
    to the system. Data is cached to avoid multiple imports of the 
    same extension. Extensions will be loaded at runtime based on 
    configs with each root config key being the extension namespace.
"""
import os
import sys
import json
import pkgutil
import importlib
from mudpi import utils
from mudpi.exceptions import MudPiError, ConfigError, ExtensionNotFound, RecursiveDependency
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.constants import __version__, PATH_CONFIG, DEFAULT_CONFIG_FILE, FONT_RESET_CURSOR, FONT_RESET, YELLOW_BACK, GREEN_BACK, \
                    FONT_GREEN, FONT_RED, FONT_YELLOW, RED_BACK, FONT_PADDING


def available_extensions(mudpi, extensions_pkg):
    """ Gets a dict of available extensions in a namespace package """
    cache = mudpi.cache.get("discovered_extensions")

    if cache is not None:
        return cache

    cache = mudpi.cache["discovered_extensions"] = { name: ispkg 
        for importer, name, ispkg in
        pkgutil.iter_modules(extensions_pkg.__path__, f'{extensions_pkg.__name__}.') }
    return cache


def get_extension_importer(mudpi, extension, install_requirements=False):
    """ Find or create an extension importer, Loads it if not loaded, 
        Checks cache first.
        
        Set install_requirements to True to also have all requirements 
        checked through pip.
    """
    if install_requirements:
        extension_importer = _extension_with_requirements_installed(mudpi, extension)
        if extension_importer is not None:
                return extension_importer

    importer_cache = mudpi.cache.setdefault("extension_importers", {})

    try:
        extension_importer = importer_cache.get(extension)
        if extension_importer is not None:
            return extension_importer
    except Exception as error:
        extension_importer = None

    if extension_importer is None:
        extension_importer = _get_custom_extensions(mudpi).get(extension)
        if extension_importer is not None:
            Logger.log(
                LOG_LEVEL["warning"],
                f'{FONT_YELLOW}You are using {extension} which is not provided by MudPi.{FONT_RESET}\nIf you experience errors, remove it.'
            )
            return extension_importer

    # Component not found look in internal extensions
    from mudpi import extensions

    Logger.log_formatted(
        LOG_LEVEL["debug"], f'Initializing Importer for Extension {extension}', 
        'Pending', 'notice'
    )
    extension_importer = ExtensionImporter.create(mudpi, extension, extensions)

    if extension_importer is not None:
        importer_cache[extension] = extension_importer
        Logger.log_formatted(
            LOG_LEVEL["info"], f'Initializing Importer for Extension {extension_importer.namespace}', 
            'Success', 'success'
        )
    else:
        Logger.log(
                LOG_LEVEL["debug"],
                f'{FONT_YELLOW}Extension `{extension}` was not found.{FONT_RESET}'
            )
        Logger.log_formatted(
            "error", f'Initializing Importer for Extension {extension}', 
            'Failed', 'error'
        )
        raise ExtensionNotFound(extension)

    return extension_importer
 

class ExtensionImporter:
    """ This class prepares and loads extensions.
        An extension is dynamically loaded into MudPi 
        and contains interfaces with components for the system.
    """

    @classmethod
    def create(cls, mudpi, extension_name, extensions_module):
        """ Static method to load extension """
        for path in extensions_module.__path__:
            config_path = os.path.join(path, extension_name, "extension.json")

            if not os.path.isfile(config_path):
                continue

            try:
                with open(config_path) as f:
                    config = json.loads(f.read())
            except FileNotFoundError:
                Logger.log(
                    LOG_LEVEL["error"],
                    f'{FONT_RED}No extension.json found at {config_path}.{FONT_RESET}'
                )
                continue
            except Exception as e:
                Logger.log(
                    LOG_LEVEL["error"],
                    f'{FONT_RED}Error loading extension.json at {config_path} {error}.{FONT_RESET}'
                )
                continue

            return cls(mudpi, config, f"{extensions_module.__name__}.{extension_name}", os.path.split(config_path)[0])

        return None


    def __init__(self, mudpi, config, extension_path, file_path):
        self.mudpi = mudpi
        self.config = config
        self.extension_path = extension_path
        self.file_path = file_path

        if self.has_dependencies:
            self.loaded_dependencies = None
            self.dependencies_ready = None
        else:
            self.loaded_dependencies = {}
            self.dependencies_ready = True

        if self.has_requirements:
            self.requirements_installed = None
        else:
            self.requirements_installed = True

        self.extension = None
        self.module = None

    """ Properties """
    @property
    def name(self):
        """ Returns the extension human readable display name """
        return self.config.get('name')

    @property
    def namespace(self):
        """ Returns the extension namespace  (a-z snakecase) 
            Must be unique and the same as the extension folder name
            i.e. rpi_gpio  
        """
        return self.config.get('namespace')

    @property
    def details(self):
        """ Returns the extension details dict """
        return self.config.setdefault('details', {})

    @property
    def description(self):
        """ Returns the extension description from the details """
        return self.config.get('details', {}).get('description')

    @property
    def documentation(self):
        """ Returns the extension documentation from the details """
        return self.config.get('details', {}).get('documentation')

    @property
    def has_requirements(self):
        """ Returns if there are requirements in the extension.json """
        return bool(self.requirements)

    @property
    def requirements(self):
        """ Returns any requirements in the extension.json (list) """
        return self.config.get('requirements')

    @property
    def has_dependencies(self):
        """ Returns if there are dependencies in the extension.json """
        return bool(self.dependencies)
    
    @property
    def dependencies(self):
        """ Returns any dependencies in the extension.json """
        return self.config.get('dependencies')
    
    """ Methods """
    def prepare_for_import(self):
        """ 
        Loads all the extensions dependencies and installs
        all the requirements before we import the extension 
        """

        cache = self.mudpi.cache.setdefault('extensions_import_ready', {})
        if cache.get(self.namespace) is not None:
            # Already processed
            return cache[self.namespace]

        if self.has_dependencies:
            if not self.import_dependencies():
                # The dependencies were not able to load
                return False

        if self.has_requirements:
            if not self.install_requirements():
                # The requirements were not able to install
                return False

        cache[self.namespace] = self
        return cache[self.namespace]


    def prepare_interface_for_import(interface_name):
        """ 
        Loads all the interface dependencies and installs
        all the requirements before we import the interface.
        """

        interface_path = f'{self.namespace}.{interface_name}'

        # Check if interface is already imported
        if self.mudpi.extensions.exists(interface_path):
            return self.mudpi.extensions.get(interface_path)

        try:
            interface_importer = get_extension_importer(self.mudpi, interface_name)
            interface_importer.prepare_for_import()
        except ExtensionNotFound as error:
            Logger.log(
                LOG_LEVEL["error"],
                f'Extension {FONT_YELLOW}{interface_name}{FONT_RESET} not found.'
            )
            return False
        except Exception as error:
            Logger.log(
                LOG_LEVEL["error"],
                f'Extension {FONT_YELLOW}{interface_name}{FONT_RESET} had error while preparing to import. {error}'
            )
            return False

        try:
            interface = interface_importer.get_interface(self.mudpi, self.namespace)
        except ImportError as error:
            Logger.log(
                LOG_LEVEL["error"],
                f'Extension {interface_name} has no Interface {FONT_YELLOW}{self.namespace}{FONT_RESET}.'
            )
            return False

        if self.mudpi.extensions.exists(interface_importer.namespace):
            # Extension for interface not setup yet and needs to be
            try:
                extension = interface_importer.extension.get_module()
            except ImportError as error:
                Logger.log(
                    LOG_LEVEL["error"],
                    f'Extension {interface_name} was unable to be imported.'
                )
                return False  

            # Check if extension needs be initialized
            if hasattr(extension, 'init'):
                if not interface_importer.extension.init(config):
                    Logger.log(
                        LOG_LEVEL["error"],
                        f'Extension {interface_importer.namespace} `init()` failed or did not return a value'
                    )
                    return False

        return interface


    def import_extension(self, config):
        """ Prepare and import the actual extension module """
        if self.mudpi.extensions.exists(self.namespace):
            # Extension already loaded
            self.extension = self.mudpi.extensions.get(self.namespace)
            return self.extension

        # Load all Dependencies and install requirements
        if not self.prepare_for_import():
            # The requirements were not able to install
            return False

        # Import the actual package now that requirements and dependencies are done
        try:
            self.extension = self.get_extension()
            # Call extension post import hook
            self.extension.extension_imported(importer=self)
        except ImportError as error:
            Logger.log(
                LOG_LEVEL["error"],
                f'Error during import of extension: {FONT_YELLOW}{error}{FONT_RESET}'
            )
            return False
        except Exception as error:
            Logger.log(
                LOG_LEVEL["error"],
                f'Extension {self.namespace} error during import: {FONT_YELLOW}{error}{FONT_RESET}'
            )
            return False

        ### Config ###
        # Now we can deal with the config
        validated_config = self.validate_config(config)

        if not validated_config:
            Logger.log(
                LOG_LEVEL["error"],
                f'Extension {FONT_YELLOW}{self.namespace}{FONT_RESET} has invalid or empty configs.'
            )
            return False

        ### Init ###
        # Call the extension init with the validated configs
        if self.module.Extension.init == self.module.Extension.__bases__[0].init:
            Logger.log(
                LOG_LEVEL["debug"], f"Extension {self.namespace} did not define an `init()` method."
            )

        Logger.log_formatted(
            LOG_LEVEL["warning"], f"Extension {self.namespace}", "Initializing", 'notice'
        )
        init_result = self.extension.init(validated_config)

        if init_result:
            Logger.log_formatted(
                LOG_LEVEL["warning"], f"Extension {self.namespace}", "Initialized", 'success'
            )
            # Call extension post init hook
            self.extension.extension_initialized(importer=self, validated_config=validated_config)
        else:
            Logger.log_formatted(
                LOG_LEVEL["error"], f"Extension {self.namespace} `init()` failed to return True", 'Failed', 'error'
            )
            return False

        self.mudpi.extensions.register(self.namespace, self.extension)
        # Call extension post registry hook
        self.extension.extension_registered(importer=self, validated_config=validated_config)
        return True


    def validate_config(self, config):
        """ Validate configs for an extension 
            Returns Fasle or the validated configs
        """

        if not self.namespace:
            Logger.log(
                LOG_LEVEL["error"],
                f'Extension {FONT_YELLOW}{self.namespace}{FONT_RESET} is missing a namespace in `extension.json`'
            )
            return False

        namespace = self.namespace

        if self.extension is None:
            Logger.log(
                LOG_LEVEL["error"],
                f'Extension {FONT_YELLOW}{namespace}{FONT_RESET} is not imported. Call `import_extension()` first!'
            )
            return False


        if config is None:
            Logger.log(
                LOG_LEVEL["error"],
                f'Extension {FONT_YELLOW}{namespace}{FONT_RESET} config is None and unable to validate.'
            )
            return False


        # Check for overrided validate_config() function to determine if custom validation is set
        if self.module.Extension.validate_config != self.module.Extension.__bases__[0].validate_config:
            Logger.log_formatted(
                LOG_LEVEL["warning"],
                f'Checking Extension {namespace} Configuration',
                "Validating", 'notice'
            )
            try:
                validated_config = self.extension.validate_config(config)
                Logger.log_formatted(
                    LOG_LEVEL["warning"],
                    f'Extension {namespace} Configuration',
                    "Validated", 'success'
                )
            except (ConfigError, MudPiError) as error:
                Logger.log_formatted(
                    LOG_LEVEL["error"],
                    f'Extension {namespace} Configuration Validation',
                    "Failed", 'error'
                )
                Logger.log(
                    LOG_LEVEL["error"],
                    f'Extension {namespace} validation error: {error}'
                )
                return False
            except Exception as error:
                Logger.log(
                    LOG_LEVEL["error"],
                    f'Extension {namespace} Validator encountered unknown error. \n{error}'
                )
                return False

            return validated_config

        # Custom validator not set proceed with default validation
        # Todo: Change this to a regex match to prevent false matches (i.e. action matches action_other)
        conf_keys = [ key 
            for key in config.keys() 
            if namespace in key ]
        Logger.log_formatted(
                LOG_LEVEL["warning"],
                f'Checking Extension {namespace} Configuration',
                "Validating", 'notice'
            )

        for conf_key in conf_keys:
            for interface_config in config[conf_key]:

                # Empty configs found
                if not interface_config:
                    continue

                # List wrapper
                if not isinstance(interface_config, list):
                    interface_config = [interface_config]

                for entry in interface_config:
                    try:
                        # Search for interface property
                        interface = entry.get("interface")
                    except AttributeError as error:
                        interface = None

                # No interface to load which is ok. Not all extensions 
                # support interfaces. i.e. triggers.
                if interface is None:
                    interfaces.append(interface_config)
                    continue

                # Interface found, attempt to load in order to validate config
                try:
                    interface_importer = get_extension_importer(self.mudpi, interface, install_requirements=True)
                except Exception as error:
                    Logger.log(
                        LOG_LEVEL["error"],
                        f'Extension {FONT_YELLOW}{namespace}{FONT_RESET} interface {interface} error. \n{error}'
                    )
                    continue

                try:
                    interface = interface_importer.get_interface(namespace)
                except Exception as error:
                    Logger.log(
                        LOG_LEVEL["error"],
                        f'Extension interface {namespace} error. \n{error}'
                    )
                    continue

                validated_interface_config = interface_config

                # TODO: change to interface class
                if hasattr(interface, 'validate'):
                    Logger.log_formatted(
                        LOG_LEVEL["warning"],
                        f'Checking Extension  {interface_importer.namespace}:{namespace} Configuration',
                        "Validating", 'notice'
                    )
                    try:
                        validated_interface_config = interface.validate(self.mudpi, interface_config)
                        Logger.log_formatted(
                            LOG_LEVEL["warning"],
                            f'Successfully Validated Extension {interface_importer.namespace}:{namespace} Configuration',
                            "Validated", 'success'
                        )
                    except (ConfigError, MudPiError) as error:
                        Logger.log_formatted(
                            LOG_LEVEL["error"],
                            f'Extension {interface_importer.namespace}:{namespace} Configuration Validation',
                            "Failed", 'error'
                        )
                        Logger.log(
                            LOG_LEVEL["error"],
                            f'Extension {namespace} validation error: {error}'
                        )
                        continue
                    except Exception as error:
                        Logger.log(
                            LOG_LEVEL["error"],
                            f'Extension {interface_importer.namepsace}:validator encountered unknown error. \n{error}'
                        )
                        continue

                interfaces.append(validated_interface_config)
        Logger.log_formatted(
            LOG_LEVEL["warning"],
            f'Extension {namespace} Configuration',
            "Validated", 'success'
        )
        # Copy old config and replace old data with validated
        validated_config = validated_config.copy()
        for key in conf_keys:
            del validated_config[key]
        validated_config[namespace] = interfaces
        config = validated_config
        return validated_config


    def get_extension(self):
        """ Get the extension base module, import if not """
        module_cache = self.mudpi.cache.setdefault('extension_modules', {})
        if self.namespace not in module_cache:
            Logger.log_formatted(
                LOG_LEVEL["info"], f'Extension {self.namespace}', 
                'Importing', 'notice'
            )
            self.module = module_cache[self.namespace] = importlib.import_module(self.extension_path)

        extension_cache = self.mudpi.cache.setdefault("extensions", {})
        if self.namespace not in extension_cache:
            if not hasattr(self.module, 'Extension'):
                raise ExtensionNotFound(self.namespace)

            extension = extension_cache[self.namespace] = self.module.Extension(self.mudpi)

        return extension_cache[self.namespace]


    def get_interface(self, interface_name):
        """ Get a interface from the extension, import it if not in cache"""
        extension_cache = self.mudpi.cache.setdefault("interfaces", {})
        component_fullname = f'{self.namespace}.{interface_name}'
        if component_fullname not in extension_cache:
            Logger.log_formatted(
                LOG_LEVEL["info"], f'Extension {self.namespace} Interface:{interface_name}', 
                'Importing', 'notice'
            )
            extension_cache[component_fullname] = \
                importlib.import_module(f'{self.extension_path}.{interface_name}')
        return extension_cache[component_fullname]

    def import_dependencies(self):
        """ Import the other extensions this one depends on first to avoid errors """
        if self.dependencies_ready is not None:
            return self.dependencies_ready

        try:
            dependencies = _load_extension_dependencies(self.mudpi, self)
            dependencies.remove(self.namespace)
            self.loaded_dependencies = dependencies
            self.dependencies_ready = True
        except ExtensionNotFound as error:
            Logger.log(
                LOG_LEVEL["error"],
                f'{FONT_RED}Extension dependency not found. {error}.{FONT_RESET}'
            )
            self.dependencies_ready = False
        except RecursiveDependency as error:
            Logger.log(
                LOG_LEVEL["error"],
                f'{FONT_RED}Extension {self.namespace} recursive dependency. {error}.{FONT_RESET}'
            )
            self.dependencies_ready = False

        return self.dependencies_ready

    def install_requirements(self):
        """ Check for requirements and make sure they are installed """
        if self.requirements_installed is not None:
            return self.requirements_installed

        requirements_installed = _install_extension_requirements(self.mudpi, self)
        self.requirements_installed = bool(requirements_installed)
        return self.requirements_installed

    def __repr__(self):
        """ Debug display of importer. """
        return f'<ExtensionImporter {self.namespace}: {self.extension_path.replace("mudpi.", "")}>'


""" Internal Methods """
def _get_custom_extensions(mudpi):
    """ Returns list of custom extensions in MudPi, checks cache first """
    if mudpi is None:
        return {}

    extension_list = mudpi.cache.setdefault('custom_extension_importers', {})

    if extension_list:
        return extension_list

    try:
        import custom_extensions
    except ImportError:
        return {}

    extension_dirs = [ extension_dir
        for path in custom_extensions.__path__
        for extension_dir in os.listdir(path)
        if os.path.isdir(os.path.join(path, extension_dir)) ]

    extension_list = {}

    for extension in extension_dirs:
        extension_importer = ExtensionImporter.create(mudpi, extension, custom_extensions)
        if extension_importer is not None:
            extension_list[extension_importer.name]: extension_importer

    mudpi.cache['custom_extension_importers'] = extension_list

    return extension_list


def _extension_with_requirements_installed(mudpi, extension):
    """ Fetch an extension with all the requirements installed 
        including any requirements defined on dependencies. """

    cache = mudpi.cache.setdefault('extensions_requirements_installed', {})

    if cache.get(extension) is not None:
        # Already processed
        return cache[extension]

    extension_importer = get_extension_importer(mudpi, extension)

    if not extension_importer.install_requirements():
        # The requirements were not able to install
        return False

    cache[extension] = extension_importer
    return extension_importer


def _load_extension_dependencies(mudpi, extension, loading_extensions = [], loaded_extensions = []):
    """ Loads extension dependencies recursively """
    namespace = extension.namespace
    loading_extensions.append(namespace)

    for dependency in extension.dependencies:
        # Check if dependency is already loaded
        if dependency in loaded_extensions:
            continue

        # Check if already loading, in which we have reference loop
        if dependency in loading_extensions:
            raise RecursiveDependency(extension, dependency)
    
        dependency_extension = get_extension_importer(mudpi, dependency)

        if dependency_extension:
            loaded_extensions.append(dependency)

            if dependency_extension.has_dependencies:
                # Dependency inception level 3, any deeper we hit limbo...
                sub_dependencies = _load_extension_dependencies(mudpi, 
                    dependency_extension, loading_extensions, loaded_extensions)

                loaded_extensions.extend(sub_dependencies)

    loaded_extensions.append(namespace)
    loading_extensions.remove(namespace)

    return loaded_extensions


def _install_extension_requirements(mudpi, extension):
    """ Installs all the extension requirements """
    cache = mudpi.cache.setdefault('extensions_requirements_installed', {})

    if cache.get(extension.namespace) is not None:
        # Already processed and installed
        return cache[extension.namespace]

    # Handle all the dependencies requirements
    if extension.has_dependencies:
        if extension.import_dependencies():
            for dependency in extension.loaded_dependencies:
                try:
                    dependency_extension = get_extension_importer(mudpi, dependency)
                except Exception as error:
                    Logger.log(
                        LOG_LEVEL["error"],
                        f'Error getting extension <{extension}> dependency: {FONT_YELLOW}{dependency}{FONT_RESET}'
                    )
                if not dependency_extension.install_requirements():
                    Logger.log(
                        LOG_LEVEL["error"],
                        f'Error with extension <{extension}> dependency: {FONT_YELLOW}{dependency}{FONT_RESET} requirements.'
                    )

    if not extension.has_requirements:
        cache[extension.namespace] = extension
        return cache[extension.namespace]

    for requirement in extension.requirements:
        if not utils.is_package_installed(requirement):
            Logger.log_formatted(
                LOG_LEVEL["info"],
                f'Extension {FONT_YELLOW}{extension.namespace}{FONT_RESET} requirements', 
                'Installing', 'notice'
            )
            if not utils.install_package(requirement):
                Logger.log(
                    LOG_LEVEL["error"],
                    f'Error installing extension <{extension}> requirement: {FONT_YELLOW}{requirement}{FONT_RESET}'
                )
                return False
    # extension.requirements_installed = True
    cache[extension.namespace] = extension
    return cache[extension.namespace]