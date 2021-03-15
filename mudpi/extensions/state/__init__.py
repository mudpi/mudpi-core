""" 
    State Extension
    Gives support to interfaces with
    the MudPi internal State Manager.
"""
from mudpi.extensions import BaseExtension


class Extension(BaseExtension):
    namespace = 'state'
    update_interval = 0.2
 