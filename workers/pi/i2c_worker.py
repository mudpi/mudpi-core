import time
import datetime
import json
import redis
import threading
import sys

sys.path.append('..')
from .worker import Worker
from sensors.pi.i2c.bme680_sensor import (Bme680Sensor)

from logger.Logger import Logger, LOG_LEVEL


class PiI2CWorker(Worker):
    def __init__(self, config, main_thread_running, system_ready):
        super().__init__(config, main_thread_running, system_ready)
        self.topic = config.get('topic', 'i2c').replace(" ", "_").lower()
        self.sleep_duration = config.get('sleep_duration', 30)

        self.sensors = []
        self.init()
        return

    def init(self):
        for sensor in self.config['sensors']:
            if sensor.get('type', None) is not None:
                # Get the sensor from the sensors folder
                # {sensor name}_sensor.{SensorName}Sensor
                sensor_type = 'sensors.pi.i2c.' + sensor.get(
                    'type').lower() + '_sensor.' + sensor.get(
                    'type').capitalize() + 'Sensor'

                imported_sensor = self.dynamic_import(sensor_type)

                # Define default kwargs for all sensor types,
                # conditionally include optional variables below if they exist
                sensor_kwargs = {
                    'name': sensor.get('name', None),
                    'address': int(sensor.get('address', 00)),
                    'key': sensor.get('key', None)
                }

                # Optional sensor variables
                # Model is specific to DHT modules to
                # specify DHT11 DHT22 or DHT2302
                if sensor.get('model'):
                    sensor_kwargs['model'] = str(sensor.get('model'))

                new_sensor = imported_sensor(**sensor_kwargs)
                new_sensor.init_sensor()

                # Set the sensor type and determine if the readings
                # are critical to operations
                new_sensor.type = sensor.get('type').lower()

                self.sensors.append(new_sensor)
            # print('{type} Sensor (Pi) {address}...\t\t\033[1;32m Ready\033[0;0m'.format(**sensor))
        return

    def run(self):
        Logger.log(
            LOG_LEVEL["info"],
            'Pi I2C Sensor Worker [' + str(
                len(
                    self.sensors)) + ' Sensors]...\t\033[1;32m Online\033[0;0m')
        return super().run()

    def work(self):
        while self.main_thread_running.is_set():
            if self.system_ready.is_set():

                message = {'event': 'PiSensorUpdate'}
                readings = {}

                for sensor in self.sensors:
                    result = sensor.read()
                    readings[sensor.key] = result
                    self.r.set(sensor.key, json.dumps(result))

                message['data'] = readings
                Logger.log(LOG_LEVEL["debug"], readings);
                self.r.publish(self.topic, json.dumps(message))
                time.sleep(self.sleep_duration)

            time.sleep(2)
        # This is only ran after the main thread is shut down
        Logger.log(
            LOG_LEVEL["info"],
            "Pi I2C Sensor Worker Shutting Down...\t\033[1;32m Complete\033[0;0m"
        )
