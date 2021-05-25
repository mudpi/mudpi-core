""" 
    Raspberry Pi Camera Extension
    Connect to a raspberry pi camera
    through the picamera library. 
"""
from mudpi.extensions import BaseExtension


class Extension(BaseExtension):
    namespace = 'picamera'
    update_interval = 1
 