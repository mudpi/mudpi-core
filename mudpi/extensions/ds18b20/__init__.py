""" 
    DS18B20 Extension
    Includes sensor interface for DS18B20.
    Works for Dallas 1-wire temperature sensors.
"""
from mudpi.extensions import BaseExtension


class Extension(BaseExtension):
    namespace = 'ds18b20'
    update_interval = 60

