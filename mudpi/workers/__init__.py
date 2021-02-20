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
    registered_workers = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.registered_workers[cls.__name__] = cls

    def __init__(self, mudpi, config):
        self.mudpi = mudpi
        self.config = config
        self.components = {}

        if self.key is None:
            self.config['key'] = f'{self.__class__.__name__}-{uuid4()}'

        self._worker_available = threading.Event()

    """ Properties """
    @property
    def key(self):
        return self.config.get('key')
    
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
        """ Initalize the Worker, Finish setup tasks """
        self.register()
        return

    def run(self, func=lambda: None):
        thread = threading.Thread(target=self.work, args=(func))
        thread.start()
        return thread

    def register(self, mudpi=None):
        """ Register a Worker to MudPi """
        mudpi = mudpi or self.mudpi
        mudpi.register_worker(self, self.key)
        return True

    def work(self, func=lambda: None):
        """ Perform work each cycle like checking devices,
            polling sensors, or listening to events. 
            Worker should sleep based on `update_interval`
        """
        while self.mudpi.is_prepared:
            if self.mudpi.is_running:
                if callable(func):
                    func()
                for component in self.components:
                    if component.should_update:
                        component.update()

                self.wait(self.update_interval)
        # MudPi Shutting Down, Perform Cleanup Below
        Logger.log(LOG_LEVEL["info"],
                   f'{"Worker Shutting Down...":.<{constants.FONT_PADDING}}{constants.FONT_GREEN}Complete{constants.FONT_RESET}')

    def wait(self, duration=0):
        """ Sleeps for a given duration 
            This allows the worker to be interupted 
            while waiting. 
        """
        time_remaining = duration
        while time_remaining > 0 and self.mudpi.thread_events["mudpi_running"].is_set():
            time.sleep(1)
            time_remaining -= 1

    """ Should be moved to Timer util """
    @property
    def elapsed_time(self):
        self.time_elapsed = time.perf_counter() - self.time_start
        return self.time_elapsed

    def reset_elapsed_time(self):
        self.time_start = time.perf_counter()
        pass
