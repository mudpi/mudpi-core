import json
import redis
import datetime
import threading

from mudpi.constants import FONT_RESET, FONT_YELLOW
from mudpi.logger.Logger import Logger, LOG_LEVEL


class StateManager():
    """
     A Central Manager to Control All States in MudPi.

     It will keep a sync of state with redis so that data
     can be recovered on restart and shared with the frontend.
     """

    def __init__(self, mudpi, redis_conf=None):
        self.mudpi = mudpi
        self.states = {}
        self._lock = threading.RLock()
        host = '127.0.0.1'
        port = 6379
        try:
            if redis_conf:
                host = redis_conf.get('host', '127.0.0.1')
                port = redis_conf.get('port', 6379)
            self.redis = redis.Redis(host=host, port=port)
        except Exception as error:
            Logger.log(LOG_LEVEL["error"],
               f"State Manager Error Connecting to Redis")

        self.restore_states()

        Logger.log_formatted(LOG_LEVEL["info"],
               f"Preparing State Manager ", "Complete", "success")

    def get(self, id):
        return self.states.get(id.lower())

    def all(self):
        with self._lock:
            return list(self.states.values())

    def remove(self, id):
        with self._lock:
            return self.states.pop(id.lower(), None)

    def id_exists(self, _id):
        _id = _id.lower()
        return _id in self.states

    def set(self, component_id, new_state, metadata=None):
        if new_state is None:
            return

        component_id = component_id.lower()
        # new_state = json.dumps(new_state)
        metadata = metadata or {}

        if new_state is not None:
            self._lock.acquire()
            previous_state = self.states.get(component_id)

            state_exists = previous_state is not None
            state_is_same = (state_exists and previous_state.state == new_state)
            metadata_is_same = (state_exists and previous_state.metadata == metadata)

            if state_is_same and metadata_is_same:
                self._lock.release()
                return

            updated_at = previous_state.updated_at if state_is_same else None

            state = State(component_id, new_state, metadata, updated_at)
            self.states[component_id] = state
            self._lock.release()

            if previous_state:
                previous_state = previous_state.to_dict()
            event_data = {
                'event': 'StateUpdated',
                'data': {
                    'component_id': component_id,
                    'previous_state': previous_state,
                    'new_state': state.to_dict()
            }}

            self.mudpi.events.publish('state', event_data)
            self.redis.set(f'{component_id}.state', json.dumps(state.to_dict()))
            self.redis.set('state_keys', json.dumps(self.ids()))
            Logger.log(LOG_LEVEL["debug"],
               f"State Changed: {FONT_YELLOW}{component_id}{FONT_RESET} - {state.state} @ {state.updated_at}")
            return event_data

    def ids(self):
        """ Return the keys of all the stored states """
        return [
            item.component_id 
            for item in self.states.values()
        ]

    def restore_states(self):
        """ Restore states from Redis 
            Resumes state of previous run if system has not cleared memory. 
        """
        self.redis.set('started_at', str(datetime.datetime.now()))
        
        keys = self.redis.get('state_keys')
        if keys:
            keys = json.loads(keys)
            for key in keys:
                data = self.redis.get(f'{key}.state')
                if data:
                    try:
                        _state = State.from_json(data)
                        self.states[key] = _state
                    except Exception as error:
                        pass

        # Restore requirement cache
        _cache = self.redis.get('requirement_installed')
        if _cache:
            self.mudpi.cache['requirement_installed'] = json.loads(_cache)

    def cache(self):
        """ Cache some important states and data for MudPi """
        if self.mudpi.cache.get('requirement_installed'):
            self.redis.set('requirement_installed', json.dumps(self.mudpi.cache['requirement_installed']))


class State():
    """ 
    A Class for Stored State from Components
    """
    @classmethod
    def from_json(cls, data):
        parsed_data = json.loads(data)
        return cls(parsed_data['component_id'], parsed_data['state'], parsed_data.get('metadata'), parsed_data['updated_at'], parsed_data.get('source_id'))

    def __init__(
        self,
        component_id,
        state = {},
        metadata = {},
        updated_at = datetime.datetime.now(),
        source_id = None
        ):
        self.component_id = component_id
        self.state = state
        self.metadata = metadata # Used for UI like icons, measure units, and display names.
        self.updated_at = updated_at if updated_at is not None else datetime.datetime.now().replace(microsecond=0)
        self.source_id = source_id

    @property
    def name(self):
        return self.metadata.get('name', "Unknown")

    def to_dict(self):
        return {
            'component_id':self.component_id,
            'state': self.state,
            'metadata': self.metadata,
            'updated_at': str(self.updated_at),
            'source_id': self.source_id
        }

    def __eq__(self, other):
        """ Provide a way to check if 'state == state'. """
        return (self.__class__ == other.__class__ and
                self.component_id == other.component_id and
                self.state == other.state and
                self.metadata == other.metadata)

    def __repr__(self):
        """ Representation of state. (Handy for debugging) """
        return f"<State {self.component_id}={self.state} {', '.join(self.metadata.values())} @ {self.updated_at}>"
