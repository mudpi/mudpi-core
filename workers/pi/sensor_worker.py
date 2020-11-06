import time
import datetime
import json
import redis
import threading
from .worker import Worker
import sys

sys.path.append('..')
from sensors.pi.float_sensor import (FloatSensor)
from sensors.pi.humidity_sensor import (HumiditySensor)
from logger.Logger import Logger, LOG_LEVEL


class PiSensorWorker(Worker):
    def __init__(self, config, main_thread_running, system_ready):
        super().__init__(config, main_thread_running, system_ready)
        self.topic = config.get('topic', 'sensors').replace(" ", "_").lower()
        self.sleep_duration = config.get('sleep_duration', 30)

        self.sensors = []
        self.init()
        return

    def init(self):
        for sensor in self.config['sensors']:
            if sensor.get('type', None) is not None:
                # Get the sensor from the sensors folder
                # {sensor name}_sensor.{SensorName}Sensor
                sensor_type = 'sensors.pi.' + sensor.get(
                    'type').lower() + '_sensor.' + sensor.get(
                    'type').capitalize() + 'Sensor'

                imported_sensor = self.dynamic_import(sensor_type)

                # Define default kwargs for all sensor types, conditionally
                # include optional variables below if they exist
                sensor_kwargs = {
                    'name': sensor.get('name', None),
                    'pin': int(sensor.get('pin', 0)),
                    'key': sensor.get('key', None)
                }

                # optional sensor variables
                # Model is specific to DHT modules to specify DHT11 DHT22
                # or DHT2302
                if sensor.get('model'):
                    sensor_kwargs['model'] = str(sensor.get('model'))

                new_sensor = imported_sensor(**sensor_kwargs)
                new_sensor.init_sensor()

                # Set the sensor type and determine if the readings are
                # critical to operations
                new_sensor.type = sensor.get('type').lower()
                if sensor.get('critical', None) is not None:
                    new_sensor.critical = True
                else:
                    new_sensor.critical = False

                self.sensors.append(new_sensor)
            # print('{type} Sensor (Pi) {pin}...\t\t\033[1;32m Ready\033[0;0m'.format(**sensor))
        return

    def run(self):
        Logger.log(
            LOG_LEVEL["info"], 'Pi Sensor Worker [' + str(
            len(self.sensors)) + ' Sensors]...\t\t\033[1;32m Online\033[0;0m'
        )
        return super().run()

    def work(self):
        while self.main_thread_running.is_set():
            if self.system_ready.is_set():
                message = {'event': 'PiSensorUpdate'}
                readings = {}
                for sensor in self.sensors:
                    result = sensor.read()
                    if result is not None:
                        readings[sensor.key] = result
                        self.r.set(sensor.key, json.dumps(result))
                # print(sensor.name, result)

                if bool(readings):
                    print(readings)
                    message['data'] = readings
                    self.r.publish(self.topic, json.dumps(message))
                time.sleep(self.sleep_duration)

            time.sleep(2)

        # This is only ran after the main thread is shut down
        Logger.log(
            LOG_LEVEL["info"],
                   "Pi Sensor Worker Shutting Down...\t\033[1;32m Complete\033[0;0m"
        )
