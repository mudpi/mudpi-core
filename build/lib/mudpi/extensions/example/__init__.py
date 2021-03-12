""" 
    Example Extension
    Includes some example configs for testing
    and has interfaces for core components.
"""
from mudpi.extensions import BaseExtension


class Extension(BaseExtension):
    namespace = 'example'
    update_interval = 30

