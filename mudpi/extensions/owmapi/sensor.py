"""
    Open Weather API
    Includes interface for open weather api
    check current, historical, and forecated weather
"""
import requests
import json
import datetime
import time
import statistics

from mudpi.exceptions import ConfigError
from mudpi.extensions import BaseInterface
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.extensions.sensor import Sensor


class Interface(BaseInterface):

    def load(self, config):
        """ Load sensor component from configs """
        sensor = OwmapiSensor(self.mudpi, config)
        if sensor:
            sensor.connect(self.extension.connections[config['connection']])
            self.add_component(sensor)

        return True

    def validate(self, config):
        """ Validate the config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('type'):
                raise ConfigError('Missing `type` in Owmapi config.')

        return config


class OwmapiSensor(Sensor):
    """ Owmapi    """

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
        return self.config.get('classifier', "general")

    @property
    def type(self):
        """ Return a type for the component """
        return self.config['type']

    @property
    def hours(self):
        """ Return a hours for the component """
        return self.config['hours']

    @property
    def measurements(self):
        """ Return a measurements for the component """
        return self.config['measurements']
    """ Methods """

    def init(self):
        """ Connect to the device and set base api request url """
        self.conn = None

        return True

    def connect(self, connection):
        """ Connect the sensor to redis """
        self.conn = connection
        if self.type in ("current", "forecast"):
            self.sensor = "https://api.openweathermap.org/data/2.5/onecall?exclude=minutely&%s" % (str(self.conn))
        elif self.type in ("historical"):
            self.sensor = "https://api.openweathermap.org/data/2.5/onecall/timemachine?%s&dt=" % (str(self.conn))
        Logger.log(LOG_LEVEL["debug"], 'OwmapiSensor: apicall: ' + str(self.sensor))

    def update(self):
        tsunix = int(time.time())
        # TODO: this might not be right (need to review hours that come back)
        ptsunix = int((datetime.datetime.fromtimestamp(tsunix) - datetime.timedelta(days=1)).timestamp())

        result = {}

        if self.type == "current":
            try:
                response = requests.get(self.sensor)
                data = json.loads(response.text)
                current = data["current"]

                # get current data for each requested measurement
                for h in data["current"]:
                    if h in self.measurements:
                        if h in ("sunrise","sunset"):
                            result[h] = current[h]
                        elif h in ('rain'):
                            result[h] = current[h]["1h"]
                        else:
                            result[h] = float(current[h])

                if "israining" in self.measurements:
                    if "rain" in current:
                        result["israining"] = 1
                    else:
                        result["israining"] = 0

                self._state = result
            except Exception as e:
                Logger.log(LOG_LEVEL["error"], "OwmapiSensor: Open Weather API call Failed: " + str(e))
                return

        elif self.type == "forecast":
            try:
                response = requests.get(self.sensor)
                data = json.loads(response.text)
                hourly = data["hourly"]

                # get forecast data for each requested measurement
                for m in self.measurements:
                    temp = []
                    # print(m)
                    for h in hourly:
                        if h["dt"] < tsunix + (self.hours * 3600) and h["dt"] > tsunix:
                            if m[3:] == "rain":
                                if "rain" in h:
                                    temp.append(h[m[3:]]["1h"])
                            else:
                                temp.append(h[m[3:]])

                    if m[:3] == "min" and len(temp) != 0:
                        result[m] = float(min(temp))
                    elif m[:3] == "max" and len(temp) != 0:
                        result[m] = float(max(temp))
                    elif m[:3] == "avg" and len(temp) != 0:
                        result[m] = float(statistics.mean(temp))
                    elif m[:3] == "sum" and len(temp) != 0:
                        result[m] = float(sum(temp))
                    else:
                        result[m] = 0.0

                self._state = result
            except Exception as e:
                Logger.log(LOG_LEVEL["error"], "OwmapiSensor: Open Weather API call Failed: " + str(e))
                return

        if self.type == "historical":
            try:
                response = requests.get(self.sensor + str(tsunix))
                hdata = json.loads(response.text)
                Logger.log(LOG_LEVEL["debug"], 'OwmapiSensor: apicall: ' + str(self.sensor + str(tsunix)))

                response = requests.get(self.sensor + str(ptsunix))
                pdata = json.loads(response.text)
                Logger.log(LOG_LEVEL["debug"], 'OwmapiSensor: apicall: ' + str(self.sensor + str(ptsunix)))

                hhourly = hdata["hourly"]
                Logger.log(LOG_LEVEL["debug"], 'OwmapiSensor: apicall: ' + str(len(hhourly)))

                phourly = pdata["hourly"]
                Logger.log(LOG_LEVEL["debug"], 'OwmapiSensor: apicall: ' + str(len(phourly)))

                # get historical data for each requested measurement
                result = {}
                for m in self.measurements:
                    temp = []
                    for h in hhourly:
                        if h["dt"] > int(tsunix) - (self.hours * 3600) and h["dt"] < tsunix:
                            if m[3:] == "rain":
                                if "rain" in h:
                                    temp.append(h[m[3:]]["1h"])
                            else:
                                temp.append(h[m[3:]])
                    for h in phourly:
                        if h["dt"] > int(tsunix) - (self.hours * 3600) and h["dt"] < tsunix:
                            if m[3:] == "rain":
                                if "rain" in h:
                                    temp.append(h[m[3:]]["1h"])
                            else:
                                temp.append(h[m[3:]])
                    if m[:3] == "min" and len(temp) != 0:
                        result[m] = float(min(temp))
                    elif m[:3] == "max" and len(temp) != 0:
                        result[m] = float(max(temp))
                    elif m[:3] == "avg" and len(temp) != 0:
                        result[m] = float(statistics.mean(temp))
                    elif m[:3] == "sum" and len(temp) != 0:
                        result[m] = float(sum(temp))
                    else:
                        result[m] = 0.0

                self._state = result

            except Exception as e:
                Logger.log(LOG_LEVEL["error"], "OwmapiSensor: Open Weather API call Failed: " + str(e))
                return

