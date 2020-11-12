import json
import sys
import threading
import time

import redis

from logger.Logger import Logger, LOG_LEVEL

class Worker:
    """
    Base Worker Class responsible for handling its set of operations
    and running on a thread

    """
    def __init__(self, config, main_thread_running, system_ready):
        self.config = config
        try:
            self.r = config["redis"]
        except KeyError:
            self.r = redis.Redis(host='127.0.0.1', port=6379)
        self.topic = config.get('topic', 'mudpi').replace(" ", "_").lower()
        self.sleep_duration = config.get('sleep_duration', 15)

        # Threading Events to Keep Everything in Sync
        self.main_thread_running = main_thread_running
        self.system_ready = system_ready
        self.worker_available = threading.Event()

        self.components = []
        return

    def init(self):
        # print('Worker...\t\t\t\033[1;32m Initializing\033[0;0m'.format(**control))
        pass

    def run(self):
        thread = threading.Thread(target=self.work, args=())
        thread.start()
        return thread

    def work(self):
        while self.main_thread_running.is_set():
            if self.system_ready.is_set():
                time.sleep(self.sleep_duration)
        # This is only ran after the main thread is shut down
        Logger.log(
            LOG_LEVEL["info"],
            "Worker Shutting Down...\t\033[1;32m Complete\033[0;0m"
        )

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

            except Exception:
                # print('Json Error. Str Found')
                return {'event': 'Unknown', 'data': message}
        else:
            # print('Failed to detect type')
            return {'event': 'Unknown', 'data': message}
