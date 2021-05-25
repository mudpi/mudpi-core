""" 
    I2C Extension
    Supports I2C protocol and
    provides interfaces for components.
"""
from mudpi.extensions import  BaseExtension


class Extension(BaseExtension):
    namespace = 'i2c'
    update_interval = 0.5
