""" 
    DHT Extension
    Includes sensor interface for DHT.
    Works with DHT11, DHT22, DHT2203
"""
from mudpi.extensions import BaseExtension


NAMESPACE = 'dht'
UPDATE_INTERVAL = 30

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = UPDATE_INTERVAL

