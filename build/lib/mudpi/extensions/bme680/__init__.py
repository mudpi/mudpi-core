""" 
    BME680 Extension
    Includes sensor interface for BME680.
    Works on i2c over linux boards.
"""
from mudpi.extensions import BaseExtension


class Extension(BaseExtension):
    namespace = 'bme680'
    update_interval = 30

