""" 
    Timer Extension
    Provides a sensor and trigger
    to do elapsed time operations.
"""
from mudpi.extensions import BaseExtension

NAMESPACE = 'timer'

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = 1

