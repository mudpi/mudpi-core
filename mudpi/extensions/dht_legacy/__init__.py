""" 
    DHT Extension
    Includes sensor interface for DHT.
    Works with DHT11, DHT22, DHT2203.
    This uses the old depricated library
    that works better on older boards.
"""
from mudpi.extensions import BaseExtension


NAMESPACE = 'dht_legacy'
UPDATE_INTERVAL = 30

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = UPDATE_INTERVAL

