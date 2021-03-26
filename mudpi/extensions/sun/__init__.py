""" 
    Sun Extension
    Includes interfaces for getting
    sunrise and sunset.
"""
from mudpi.extensions import BaseExtension


class Extension(BaseExtension):
    namespace = 'sun'
    update_interval = (60 * 60 * 4) # Every 4 hours

    def init(self, config):
        """ Prepare the api connection and sun components """
        self.config = config

        return True

