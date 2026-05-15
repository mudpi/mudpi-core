"""
    Open Weather API
    Includes interface for open weather api
    check current, historical, and forecated weather
"""
import requests
import json

from mudpi.exceptions import ConfigError
from mudpi.extensions import BaseExtension
from mudpi.logger.Logger import Logger, LOG_LEVEL


class Extension(BaseExtension):
    namespace = 'owmapi'
    update_interval = 300

    def init(self, config):
        self.connections = {}
        self.config = config

        if not isinstance(config, list):
            config = [config]

        for conf in config:
            api_key = conf.get('api_key')

            unit_system = conf.get('unit_system')
            if not unit_system:
                unit_system = self.mudpi.config.unit_system

            latitude = conf.get('latitude')
            if not latitude:
                latitude = self.mudpi.config.latitude
            else:
                latitude = float(conf['latitude'])

            longitude = conf.get('longitude')
            if not longitude:
                longitude = self.mudpi.config.longitude
            else:
                longitude = float(conf['longitude'])

        Logger.log(LOG_LEVEL["debug"], 'OwmapiSensor: api_key: ' + str(api_key))
        Logger.log(LOG_LEVEL["debug"], 'OwmapiSensor: unit_system: ' + str(unit_system))
        Logger.log(LOG_LEVEL["debug"], 'OwmapiSensor: lat/lon set: ' + str(latitude) + ":" + str(longitude) )

        # Override Mudpi defaults and go try to look up Lat/Long using the IP
        try:
            if latitude == 43 or longitude == -88 or latitude is None or longitude is None:
                r = requests.get('https://ipinfo.io/')
                j = json.loads(r.text)
                loc = tuple(j["loc"].split(','))
                latitude = loc[0]
                longitude = loc[1]
                Logger.log(LOG_LEVEL["debug"],
                           "OwmapiSensor: Forecast based on device location: " + j["city"] + ", " + j[
                               "region"] + ", " + j["country"])

        except Exception as e:
            Logger.log(LOG_LEVEL["error"], "OwmapiSensor: Unable to retrieve location: " + str(e))

        Logger.log(LOG_LEVEL["debug"], 'OwmapiSensor: lat/lon: ' + str(latitude) + ':' + str(longitude))

        self.connections[conf['key']] = "lat=%s&lon=%s&appid=%s&units=%s" % (latitude, longitude, api_key, unit_system)
        Logger.log(LOG_LEVEL["debug"], 'OwmapiSensor: connection: ' + str(self.connections))

        return True

    def validate(self, config):
        config = config[self.namespace]
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            key = conf.get('key')
            if key is None:
                raise ConfigError('OwmApi is missing a `key` in config')

            api_key = conf.get('api_key')
            if api_key is None:
                raise ConfigError('OwmApi is missing a `api_key` in config')

        return config