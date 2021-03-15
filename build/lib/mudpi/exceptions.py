""" MudPi System Exceptions
All the custom exceptions for MudPi.
"""

class MudPiError(Exception):
    """ General MudPi exception occurred. """


""" Config Errors """
class ConfigError(MudPiError):
    """ General error with configurations. """

class NoKeyProvidedError(ConfigError):
    """ When no config key is specified. """

class ConfigFormatError(ConfigError):
    """ Error with configuration formatting. """

class ConfigNotFoundError(ConfigError):
    """ Error with no config file found. """


""" State Errors """
class InvalidStateError(MudPiError):
    """ When a problem occurs with impromper state machine states. """


""" Extension Errors """
class ExtensionNotFound(MudPiError):
    """ Error when problem importing extensions """
    def __init__(self, extension):
        super().__init__(f"Extension '{extension}' not found.")
        self.extension = extension

class RecursiveDependency(MudPiError):
    """ Error when extension references anther extension in dependency loop """

    def __init__(self, extension, dependency):
        super().__init__(f'Recursive dependency loop: {extension} -> {dependency}.')
        self.extension = extension
        self.dependency = dependency