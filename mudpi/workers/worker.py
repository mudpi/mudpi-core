import sys
import time
import json
import redis
import datetime
import threading

from mudpi import constants
from mudpi.logger.Logger import Logger, LOG_LEVEL


class Worker:
    """Base Worker Class

    A worker is responsible for handling its set of operations and
    running on a thread
    """

    def __init__(self, config, main_thread_running, system_ready):
        self.config = config
        # Threading Events to Keep Everything in Sync
        self.main_thread_running = main_thread_running
        self.system_ready = system_ready
        self.worker_available = threading.Event()

        self.components = []
        return

    def init(self):
        # print('Worker...\t\t\t\033[1;32m Initializing\033[0;0m'.format(**control))
        return

    def run(self):
        t = threading.Thread(target=self.work, args=())
        t.start()
        return t

    def work(self):
        while self.main_thread_running.is_set():
            if self.system_ready.is_set():
                time.sleep(self.sleep_duration)
        # This is only ran after the main thread is shut down
        Logger.log(LOG_LEVEL["info"],
                   "Worker Shutting Down...\t\033[1;32m Complete\033[0;0m")

    def elapsed_time(self):
        self.time_elapsed = time.perf_counter() - self.time_start
        return self.time_elapsed

    def reset_elapsed_time(self):
        self.time_start = time.perf_counter()
        pass

    def dynamic_import(self, name):
        # Split path of the class folder structure:
        # {sensor name}_sensor . {SensorName}Sensor
        components = name.split('.')
        # Dynamically import root of component path
        module = __import__(components[0])
        # Get component attributes
        for component in components[1:]:
            module = getattr(module, component)
        return module

    def decode_message_data(self, message):
        if isinstance(message, dict):
            # print('Dict Found')
            return message
        elif isinstance(message.decode('utf-8'), str):
            try:
                temp = json.loads(message.decode('utf-8'))
                # print('Json Found')
                return temp
            except:
                # print('Json Error. Str Found')
                return {'event': 'Unknown', 'data': message}
        else:
            # print('Failed to detect type')
            return {'event': 'Unknown', 'data': message}
