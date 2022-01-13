"""
    DS18B20 Sensor Interface
    Connects to a DS18B20 device to get
    temperature readings.
"""
import os
import glob
import time

from mudpi.constants import METRIC_SYSTEM
from mudpi.extensions import BaseInterface
from mudpi.extensions.sensor import Sensor
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.exceptions import MudPiError, ConfigError

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')


#device_folder = '/sys/bus/w1/devices/28-01206308503c'
#device_folder = glob.glob(base_dir + '/28*')[0]
#device_file = device_folder + '/w1_slave'

class Interface(BaseInterface):
    
    def load(self, config):
        """ Load DS18B20 sensor component from configs """
        sensor = ds18b20(self.mudpi, config)
        self.add_component(sensor)
        return True

    def validate(self, config):
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            """ See if 1-wire ID was passed by the user in the config file """
            if not conf.get('onewireID'):
                Logger.log(
                    LOG_LEVEL["debug"],
                    'DS18B20 onewireID not set. Will search for device.'
                )         
               
        return config

class ds18b20(Sensor):
    """ DS18B20 Sensor get readings temperature. """

    """ Properties """
    @property
    def id(self):
        """ Return a unique id for the component """
        return self.config['key']

    @property
    def name(self):
        """ Return the display name of the component """
        return self.config.get('name') or f"{self.id.replace('_', ' ').title()}"

    @property
    def state(self):
        """ Return the state of the component (from memory, no IO!) """
        return self._state

    @property
    def classifier(self):
        """ Classification further describing it, effects the data formatting """
        return 'temperature'

    @property
    def onewireID(self):
        return self.config['onewireID']


    """ Methods """
    def init(self):
        """To support multiple 1-wire devices check to see if the ID is set in the config.
        If the ID is not set, there should only be a single 28-xxxxxxxxx directory in the base directory, so we use that. """

        base_dir = '/sys/bus/w1/devices'

        if self.config.get('onewireID') and os.path.isdir(base_dir + '/' + self.config.get('onewireID')):
            self.device_file = base_dir + '/' + self.config.get('onewireID') + '/w1_slave'
            Logger.log(
                LOG_LEVEL["debug"],
                'Setting device file to ' + self.device_file
            )
        else:
            Logger.log(
                LOG_LEVEL["debug"],
                'DS18B20 onewireID not set or not found.'
            )
            """ Make sure 1-wire device directory exists """
            try:
                device_folder = glob.glob(base_dir + '/28*')[0]
            except:
                Logger.log(
                    LOG_LEVEL["error"],
                    'Failed to find 1-wire device directory. Ensure device is connected and onewireID corret..'
                    )
            else:
                self.device_file = device_folder + '/w1_slave'        
        return True

    def update(self):

        def read_temp_raw():
            f = open(self.device_file, 'r')
            lines = f.readlines()
            f.close()
            return lines

        lines = read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temperature_c = float(temp_string) / 1000.0
            temperature_f = temperature_c * 9.0 / 5.0 + 32.0
            _temperature = round(temperature_c if self.mudpi.unit_system == METRIC_SYSTEM else temperature_f, 2)
            readings = {
                'temperature': _temperature,
            }
            self._state = readings
            return readings
        else:
            Logger.log(
                LOG_LEVEL["error"],
                'Failed to get reading [DS18B20]. Try again!'
            )
        return None
