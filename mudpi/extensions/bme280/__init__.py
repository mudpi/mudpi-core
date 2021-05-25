""" 
    BME280 Extension
    Includes sensor interface for BME280.
    Works on i2c over linux boards.
"""
from mudpi.extensions import BaseExtension


class Extension(BaseExtension):
    namespace = 'bme280'
    update_interval = 30

