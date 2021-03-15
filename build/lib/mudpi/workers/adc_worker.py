import time
import json
import busio
import board
import redis
import digitalio
import threading
import importlib
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

from mudpi.logger.Logger import Logger, LOG_LEVEL


class ADCMCP3008Worker:
    """
    Analog-Digital-Converter Worker
    """
    PINS = {
        '4': board.D4,
        '17': board.D17,
        '27': board.D27,
        '22': board.D22,
        '5': board.D5,
        '6': board.D6,
        '13': board.D13,
        '19': board.D19,
        '26': board.D26,
        '18': board.D18,
        '23': board.D23,
        '24': board.D24,
        '25': board.D25,
        '12': board.D12,
        '16': board.D16,
        '20': board.D20,
        '21': board.D21
    }

    def __init__(self, config: dict, main_thread_running, system_ready):
        self.config = config
        self.main_thread_running = main_thread_running
        self.system_ready = system_ready
        self.node_ready = False
        try:
            self.r = redis_conn if redis_conn is not None else redis.Redis(
                host='127.0.0.1', port=6379)
        except KeyError:
            self.r = redis.Redis(host='127.0.0.1', port=6379)

        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs = digitalio.DigitalInOut(ADCMCP3008Worker.PINS[config['pin']])

        self.mcp = MCP.MCP3008(spi, cs)

        self.sensors = []
        self.init_sensors()

        self.node_ready = True

    def dynamic_sensor_import(self, path):
        components = path.split('.')

        s = ''
        for component in components[:-1]:
            s += component + '.'

        parent = importlib.import_module(s[:-1])
        sensor = getattr(parent, components[-1])

        return sensor

    def init_sensors(self):
        for sensor in self.config['sensors']:

            if sensor.get('type', None) is not None:
                # Get the sensor from the sensors folder
                # {sensor name}_sensor.{SensorName}Sensor
                sensor_type = 'sensors.mcp3xxx.' + sensor.get(
                    'type').lower() + '_sensor.' + sensor.get(
                    'type').capitalize() + 'Sensor'
                # analog_pin_mode = False if sensor.get('is_digital', False) else True
                imported_sensor = self.dynamic_sensor_import(sensor_type)
                new_sensor = imported_sensor(int(sensor.get('pin')),
                                             name=sensor.get('name',
                                                             sensor.get(
                                                                 'type')),
                                             key=sensor.get('key', None),
                                             mcp=self.mcp)
                new_sensor.init_sensor()
                self.sensors.append(new_sensor)
                Logger.log(
                    LOG_LEVEL["info"],
                    '{type} Sensor {pin}...\t\t\t\033[1;32m Ready\033[0;0m'.format(
                        **sensor)
                )

    def run(self):

        if self.node_ready:
            t = threading.Thread(target=self.work, args=())
            t.start()
            Logger.log(
                LOG_LEVEL["info"],
                str(self.config['name']) + ' Node Worker [' + str(
                    len(self.config[
                            'sensors'])) + ' Sensors]...\t\033[1;32m Online\033[0;0m'
            )
            return t

        else:
            Logger.log(
                LOG_LEVEL["warning"],
                "Node Connection...\t\t\t\033[1;31m Failed\033[0;0m"
            )
            return None

    def work(self):

        while self.main_thread_running.is_set():
            if self.system_ready.is_set() and self.node_ready:
                message = {'event': 'SensorUpdate'}
                readings = {}
                for sensor in self.sensors:
                    result = sensor.read()
                    readings[sensor.key] = result
                # r.set(sensor.get('key', sensor.get('type')), value)

                Logger.log(LOG_LEVEL["info"], readings)
                message['data'] = readings
                self.r.publish('sensors', json.dumps(message))

            time.sleep(15)
        # This is only ran after the main thread is shut down
        Logger.log(
            LOG_LEVEL["info"],
            "{name} Node Worker Shutting Down...\t\t\033[1;32m Complete\033[0;0m".format(
                **self.config)
        )
