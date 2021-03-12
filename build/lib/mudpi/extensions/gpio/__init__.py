""" 
    GPIO Extension
    Includes interfaces for linux board 
    GPIO. Supports many linux based boards.
"""
from mudpi.extensions import BaseExtension


class Extension(BaseExtension):
    namespace = 'gpio'
    update_interval = 30

