import json
import datetime
import threading

from mudpi.constants import ATTR_FRIENDLY_NAME


class StateManager():
    """
     A Central Manager to Control All States in MudPi.

     It will keep a sync of state with redis so that data
     can be recovered on restart and shared with the frontend.
     """

    def __init__(self):
        self.states = {}
        self._lock = threading.Lock()

    def get(self, id):
        return self.states.get(id.lower())

    def all(self):
        with self._lock:
            return list(self.states.values())

    def remove(self, id):
        with self._lock:
            return self.states.pop(id.lower(), None)

    def id_exists(self, id):
        id = id.lower()
        return id in self.states

    def set(self, component_id, new_state, metadata=None):
        component_id = component_id.lower()
        new_state = json.dumps(new_state),
        metadata = metadata or {}

        with self._lock:
            previous_state = self.states.get(component_id)

            state_exists = previous_state is not None
            state_is_same = state_exists and previous_state.state == new_state
            metadata_is_same = state_exists and previous_state.metadata == metadata

            if state_is_same and metadata_is_same:
                return

            updated_at = previous_state.updated_at if state_is_same else None

            state = State(component_id, new_state, metadata, updated_at)
            self.states[component_id] = state

            event_data = {
                'component_id': component_id,
                'previous_state': previous_state,
                'new_state': state,
            }

            # TODO: Emit an event
            return event_data

    def ids(self):
        with self._lock:
            return [
                item.component_id 
                for item in self.states.values()
            ]


class State():
    """ 
    A Class for Stored State from Components
    """
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
        self.updated_at = updated_at if updated_at is not None else datetime.datetime.now()
        self.source_id = source_id

    @property
    def name(self):
        return self.metadata.get(ATTR_FRIENDLY_NAME, "Unknown")

    def __eq__(self, other):
        """ Provide a way to check if 'state == state'. """
        return (self.__class__ == other.__class__ and
                self.component_id == other.component_id and
                self.state == other.state and
                self.metadata == other.metadata)

    def __repr__(self):
        """ Representation of state. (Handy for debugging) """
        return f"<State {self.component_id}={self.state}{self.metadata} @ {self.updated_at}>"
