""" 
    Cron Trigger Interface
    Cron schedule support for triggers
    to allow scheduling.
"""
import time
import pycron
import datetime
from mudpi.exceptions import ConfigError
from mudpi.extensions import BaseInterface
from mudpi.extensions.trigger import Trigger
from mudpi.logger.Logger import Logger, LOG_LEVEL


class Interface(BaseInterface):

    # Override the update time
    update_interval = 60
    
    def load(self, config):
        """ Load cron trigger component from configs """
        trigger = CronTrigger(self.mudpi, config)
        if trigger:
            self.add_component(trigger)
        return True

    def validate(self, config):
        """ Validate the trigger config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('schedule'):
                Logger.log(
                    LOG_LEVEL["debug"],
                    'Trigger: No `schedule`, defaulting to every 5 mins'
                )
                # raise ConfigError('Missing `schedule` in Trigger config.')
            
        return config


class CronTrigger(Trigger):
    """ A trigger that resoponds to time 
        changes based on cron schedule string 
    """

    """ Properties """
    @property
    def schedule(self):
        """ Cron schedule string to check time against """
        return self.config.get('schedule', '*/5 * * * *')


    """ Methods """
    def init(self):
        """ Pass call to parent """
        super().init()

    def check(self):
        """ Check trigger schedule thresholds """
        if self.mudpi.is_running:
            try:
                if pycron.is_now(self.schedule):
                    self.trigger()
                    if not self.active:
                        self.active = True
                else:
                    if self.active:
                        self.active = False
            except Exception as error:
                Logger.log(
                    LOG_LEVEL["error"],
                    "Error evaluating time trigger schedule."
                )
        return