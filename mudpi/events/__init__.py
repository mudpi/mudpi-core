""" The core Event System for MudPi. 
    
    Uses adaptors to provide events across 
    different protocols for internal communications. 

    Available Adaptors: 'mqtt', 'redis'
    Default: redis
"""
from uuid import uuid4
from copy import deepcopy
from datetime import datetime
from mudpi.events import adaptors
from mudpi.logger.Logger import Logger, LOG_LEVEL


class EventSystem():
    """ Main event manager that loads adaptors 
        and coordinates the bus operations. """

    def __init__(self, config={}):
        self.config = config
        self.prefix = config.get('prefix', 'mudpi_core_')
        self.topics = {}
        self.adaptors = {}
        self._load_adaptors()

    def connect(self):
        """ Setup connections for all adaptors """
        connection_data = {}
        for key, adaptor in self.adaptors.items():
            Logger.log_formatted(
                LOG_LEVEL["debug"],
                f"Preparing Event System for {key} ", 'Pending', 'notice'
            )
            connection_data[key] = adaptor.connect()
            Logger.log_formatted(
                LOG_LEVEL["info"],
                f"Event System Ready on {key}  ", 'Connected', 'success'
            )
        return connection_data

    def disconnect(self):
        """ Disconnect all adaptors """
        for key, adaptor in self.adaptors.items():
            adaptor.disconnect()
        return True

    def subscribe(self, topic, callback):
        """ Add a subscriber to an event """
        for key, adaptor in self.adaptors.items():
            adaptor.subscribe(topic, callback)
            self.topics[key].append(topic)
        return True

    def unsubscribe(self, topic):
        """ Remove a subscriber from an event """
        for key, adaptor in self.adaptors.items():
            adaptor.unsubscribe(topic)
            self.topics[key].remove(topic)
        return True

    def publish(self, topic, data=None):
        """ Publish an event on an topic 
            Format: {event: "EventName": data: {...} }
        """
        if data:
            event = {}
            if isinstance(data, dict):
                _data = deepcopy(data)
                if 'uuid' not in _data:
                    event['uuid'] = data['uuid'] = str(uuid4())
                else:
                    event['uuid'] = _data['uuid']

                if 'event' not in _data:
                    event['event'] = "Unknown"
                else:
                    event['event'] = _data['event']
                    del _data['event']

                event['updated_at'] = str(datetime.now().replace(microsecond=0))

                if 'data' not in _data:
                    event['data'] = _data
                else:
                    if isinstance(_data['data'], dict):
                        _data_data = deepcopy(_data['data'])
                    else:
                        _data_data = { 'data': _data['data'] }
                    del _data['data']
                    event['data'] = {**_data_data, **_data}
            else:
                 event['data'] = data
        else:
             event['data'] = data

        for key, adaptor in self.adaptors.items():
            adaptor.publish(topic, event)
        return True

    def subscribe_once(self, topic, callback):
        """ Listen to an event once """
        for key, adaptor in self.adaptors.items():
            adaptor.subscribe_once(topic, callback)
        return True

    def get_message(self):
        """ Request any new messages because some protocols 
            require a poll for data """
        for key, adaptor in self.adaptors.items():
            adaptor.get_message()

    def events(self):
        """ Return all the events subscribed to [List] """
        return self.topics


    def _load_adaptors(self):
        """ Load all the adaptors """
        if self.config:
            for key, config in self.config.items():
                if key in adaptors.Adaptor.adaptors:
                    self.adaptors[key] = adaptors.Adaptor.adaptors[key](config)
                    self.topics[key] = []
        else:
            # Default adaptor
            self.adaptors['redis'] = adaptors.Adaptor.adaptors['redis']({"host": "127.0.0.1", "port": 6379})
            self.topics['redis'] = []