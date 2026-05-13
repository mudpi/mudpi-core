""" 
    DHT Extension [Legacy / Deprecated]
    Includes sensor interface for DHT.
    Works with DHT11, DHT22, DHT2203.

    DEPRECATED: The Adafruit_DHT library this extension depends on
    is abandoned and incompatible with Python 3.9+. Use the 'dht'
    extension (adafruit-circuitpython-dht) instead.
"""
import warnings
from mudpi.extensions import BaseExtension


NAMESPACE = 'dht_legacy'
UPDATE_INTERVAL = 30

warnings.warn(
    "The 'dht_legacy' extension is deprecated and will be removed in a future "
    "release. It depends on the abandoned Adafruit_DHT library which is "
    "incompatible with Python 3.9+. Use the 'dht' extension instead.",
    DeprecationWarning,
    stacklevel=2
)

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = UPDATE_INTERVAL

