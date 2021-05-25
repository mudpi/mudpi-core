""" 
    T9602 Extension
    Includes sensor interface for T9602.
    Works on i2c over linux boards (typically
    on a raspberry pi.)
"""
from mudpi.extensions import BaseExtension


class Extension(BaseExtension):
    namespace = 't9602'
    update_interval = 30

