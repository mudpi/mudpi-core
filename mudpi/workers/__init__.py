import time
import redis
import threading
from uuid import uuid4

from mudpi import constants
from mudpi.logger.Logger import Logger, LOG_LEVEL


class Worker:
    """ Base Worker Class

    A worker is responsible for managing components,
    updating component state, configurations ,etc.
    
    A worker runs on a thread with an interruptable sleep 
    interaval between update cycles. 
    """
    def __init__(self, mudpi, config):
        self.mudpi = mudpi
        self.config = config
        self.components = {}

        if self.key is None:
            self.config['key'] = f'{self.__class__.__name__}-{uuid4()}'

        self._worker_available = threading.Event()
        self._thread = None
        self.init()
        self.mudpi.workers.register(self.key, self)

    """ Properties """
    @property
    def key(self):
        return self.config.get('key')

    @property
    def update_interval(self):
        return self.config.get('update_interval', constants.DEFAULT_UPDATE_INTERVAL)
    
    @property
    def is_available(self):
        return self._worker_available.is_set()

    @is_available.setter
    def is_available(self, value):
        if bool(value):
            self._worker_available.set()
        else:
            self._worker_available.clear()
    
    """ Methods """
    def init(self):
        """ Called at end of __init__ for additonal setup """
        pass

    def run(self, func=None):
        if not self._thread:
            self._thread = threading.Thread(target=self.work, args=(func,))
            Logger.log_formatted(LOG_LEVEL["debug"],
                   f"Worker {self.key} ", "Starting", "notice")
            self._thread.start()
            Logger.log_formatted(LOG_LEVEL["info"],
                   f"Worker {self.key} ", "Started", "success")
        return self._thread

    def work(self, func=None):
        """ Perform work each cycle like checking devices,
            polling sensors, or listening to events. 
            Worker should sleep based on `update_interval`
        """
        while self.mudpi.is_prepared:
            if self.mudpi.is_running:
                if callable(func):
                    func()
                for key, component in self.components.items():
                    if component.should_update:
                        component.update()
                        component.store_state()

                self._wait(self.update_interval)
        # # MudPi Shutting Down, Perform Cleanup Below
        Logger.log_formatted(LOG_LEVEL["debug"],
                   f"Worker {self.key} ", "Stopping", "notice")
        for key, component in self.components.items():
            component.unload()
        Logger.log_formatted(LOG_LEVEL["info"],
                   f"Worker {self.key} ", "Offline", "error")

    def _wait(self, duration=0):
        """ Sleeps for a given duration 
            This allows the worker to be interupted 
            while waiting. 
        """
        time_remaining = duration
        while time_remaining > 0 and self.mudpi.is_prepared:
            time.sleep(0.001)
            time_remaining -= 0.001

    """ Should be moved to Timer util """
    @property
    def elapsed_time(self):
        self.time_elapsed = time.perf_counter() - self.time_start
        return self.time_elapsed

    def reset_elapsed_time(self):
        self.time_start = time.perf_counter()
        pass
