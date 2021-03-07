""" 
    Cron Extension
    Cron schedule support for triggers
    to allow scheduling.
"""
from mudpi.extensions import BaseExtension


class Extension(BaseExtension):
    namespace = 'cron'
    update_interval = 1
 