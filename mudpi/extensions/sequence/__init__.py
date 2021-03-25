""" 
    Sequence Extension
    Enabled actions to be grouped into
    automations that can be fired in 
    a sequenctial order.
"""
import json
import time
import datetime
import threading
from mudpi.utils import decode_event_data
from mudpi.constants import FONT_RESET, FONT_CYAN
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.extensions import BaseExtension, Component
from mudpi.exceptions import MudPiError, ConfigError

NAMESPACE = 'sequence'

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = 0.05

    def init(self, config):
        self.config = config

        if not isinstance(config, list):
            config = [config]

        for conf in config:
            sequence = Sequence(self.mudpi, conf)
            if sequence:
                self.manager.add_component(sequence)
                self.manager.register_component_actions('start', action='start')
                self.manager.register_component_actions('stop', action='stop')
                self.manager.register_component_actions('previous_step', action='previous_step')
                self.manager.register_component_actions('reset_step', action='reset_step')
                self.manager.register_component_actions('next_step', action='advance_step')
                self.manager.register_component_actions('skip_step', action='skip_step')
                self.manager.register_component_actions('reset', action='reset')
                self.manager.register_component_actions('restart', action='restart')
        return True

    def validate(self, config):
        """ Validate the Sequence configs """
        config = config[self.namespace]
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            key = conf.get('key')
            if key is None:
                raise ConfigError('Seqeunce missing a `key` in config')

            sequence = conf.get('sequence')
            if sequence is None:
                raise ConfigError('Sequence missing a `sequence` list of actions in config')
        return config


class Sequence(Component):
    """ Automation Sequence
        Performs sequence of actions with delays
        and conditions inbetween each phase.  
    """

    """ Properties """
    @property
    def id(self):
        """ Unique id or key """
        return self.config.get('key')

    @property
    def name(self):
        """ Friendly name of control """
        return self.config.get('name') or f"{self.id.replace('_', ' ').title()}"

    @property
    def sequence(self):
        """ List of actions and delays """
        return self.config.get('sequence', [])

    @property
    def current_step(self):
        """ Current step from sequence list """
        return self.sequence[self._current_step]

    @property
    def step_delay(self):
        """ Returns the current step's delay 
            Delays happen before actions
        """
        return self.sequence[self._current_step].get('delay')

    @property
    def step_duration(self):
        """ Returns the current step's duration 
            Durations are delays after actions 
        """
        return self.sequence[self._current_step].get('duration')

    @property
    def total_steps(self):
        """ List of actions and delays """
        return len(self.sequence)

    @property
    def active(self):
        """ Thread save active boolean """
        return self._active.is_set()

    @active.setter
    def active(self, value):
        """ Allows `self.active = False` while still being thread safe """
        if bool(value):
            self._active.set()
        else:
            self._active.clear()

    @property
    def duration(self):
        """ Return how long the current state has been applied in seconds """
        self._current_duration = time.perf_counter() - self._duration_start
        return round(self._current_duration, 4)

    @property
    def topic(self):
        """ Return the topic to listen on """
        return self.config.get('topic', '').replace(" ", "/").lower() if self.config.get(
            'topic') is not None else f'{NAMESPACE}/{self.id}'
    
    @property
    def state(self):
        """ Current state of sequence """
        return {
            "active": self.active,
            "current_step": self.current_step,
            "step_delay": self.step_delay,
            "step_duration": self.step_duration,
            "delay_complete": self._delay_complete,
            "step_triggered": self._step_triggered,
            "step_complete": self._step_complete
        }

    """ Methods """
    def init(self):
        """ Init hook to subscribe to events """
        # Current step of the automation (0 index)
        self._current_step = 0

        # True if current step delay finished
        self._delay_complete = False

        # True if current step is completed and delay done
        self._step_complete = False

        # True if step triggered to advanced
        self._step_triggered = False

        # Thread safe bool for if sequence is active
        self._active = threading.Event()

        # Used for duration tracking
        self._duration_start = time.perf_counter()

        # Tracking delay config vs actual delay duration
        self._delay_actual = 0

        # Tracking duration config vs actual step duration
        self._duration_actual = 0
        
        self.mudpi.events.subscribe(self.topic, self.handle_event)

    def update(self):
        """ Main run loop for sequence to check
            time past and if it should fire actions """
        if self.mudpi.is_prepared:
            try:
                if self.active:
                    if not self._step_complete:
                        if not self._delay_complete:
                            if self.step_delay is not None:
                                if self.duration > self.step_delay:
                                    self._delay_complete = True
                                    self._delay_actual = self.duration
                                    self.reset_duration()
                                else:
                                    # Waiting break early
                                    return
                            else:
                                self._delay_complete = True
                                self.reset_duration()

                        if self._delay_complete:
                            if not self._step_triggered:
                                if self.evaluate_thresholds():
                                    self.trigger()
                                else:
                                    if self.current_step.get('thresholds') is not None:
                                        # Thresholds failed skip step without trigger
                                        self._step_triggered = True
                                        self._step_complete = True

                        if self.step_duration is not None and not self._step_complete:
                            if self.duration > self.step_duration:
                                self._step_complete = True
                                self._duration_actual = self.duration
                                self.reset_duration()
                            else:
                                # Waiting break early
                                return
                        else:
                            # No duration set meaning step only advances
                            # manualy by calling actions and events. RTM
                            pass

                    if self._step_complete:
                        self.fire({"event": "SequenceStepEnded"})
                        # Logger.log(
                        #     LOG_LEVEL["debug"],
                        #     f'Sequence {FONT_CYAN}{self.name}{FONT_RESET} Step {self._current_step+1} Debug\n' \
                        #     f'Delay: {self.step_delay} Actual: {self._delay_actual} Duration: {self.step_duration} Actual: {self._duration_actual}'
                        # )
                        return self.next_step()
                else:
                    # Sequence is not active.
                    self.reset_duration()
            except Exception as e:
                    Logger.log_formatted(LOG_LEVEL["error"],
                               f'Sequence {self.id}', 'Unexpected Error', 'error')
                    Logger.log(LOG_LEVEL["critical"], e)

    def fire(self, data={}):
        """ Fire a control event """
        event_data = {
            'event': 'SequenceUpdated',
            'component_id': self.id,
            'name': self.name,
            'updated_at': str(datetime.datetime.now().replace(microsecond=0)),
            'state': self.active,
            'step': self._current_step,
            'total_steps': self.total_steps
        }
        event_data.update(data)
        self.mudpi.events.publish(NAMESPACE, event_data)

    def reset_duration(self):
        """ Reset the duration of the current state """
        self._duration_start = time.perf_counter()
        return True

    def restart(self, event_data=None):
        """ Restart the entire sequence from begining """
        self._current_step = 0
        self.reset_step()
        self.active = True
        self.fire({
            "event": "SequenceRestarted"
        })
        Logger.log(
            LOG_LEVEL["info"],
            f'Sequence {FONT_CYAN}{self.name}{FONT_RESET} Restarted'
        )

    def reset(self, event_data=None):
        """ Reset the entire sequence """
        self._current_step = 0
        self.reset_step()
        self.fire({
            "event": "SequenceReset"
        })
        Logger.log(
            LOG_LEVEL["info"],
            f'Sequence {FONT_CYAN}{self.name}{FONT_RESET} Reset'
        )

    def reset_step(self, event_data=None):
        """ Reset the current step progress """
        self._delay_complete = False
        self._step_triggered = False
        self._step_complete = False
        self.reset_duration()

    def start(self, event_data=None):
        """ Start the sequence """
        if not self.active:
            self._current_step = 0
            self.active = True
            self.reset_step()
            self.fire({
                "event": "SequenceStarted"
            })
            Logger.log(
                LOG_LEVEL["info"],
                f'Sequence {FONT_CYAN}{self.name}{FONT_RESET} Started'
            )

    def stop(self, event_data=None):
        """ Stop the sequence """
        if self.active:
            self._current_step = 0
            self.active = False
            self.reset_step()
            self.fire({
                "event": "SequenceStopped"
            })
            Logger.log(
                LOG_LEVEL["info"],
                f'Sequence {FONT_CYAN}{self.name}{FONT_RESET} Stopped'
            )

    def next_step(self, event_data=None):
        """ Advance to the next sequnce step
            Makes sure any delays and durations are done """

        # Step must be flagged complete to advance
        if self._step_complete:
            if self.active:
                # If skipping steps trigger unperformed actions
                if not self._step_triggered:
                    if self.evaluate_thresholds():
                        self.trigger()
                # Sequence is already active, advance to next step
                if self._current_step < self.total_steps - 1:
                    self.reset_step()
                    self._current_step += 1
                    self.fire({"event": "SequenceStepStarted"})
                    Logger.log_formatted(
                        LOG_LEVEL["info"],
                        f'Sequence: {FONT_CYAN}{self.name}{FONT_RESET}', f'Step {self._current_step+1}/{self.total_steps}'
                    )
                else:
                    # Last step of sequence completed
                    self.active = False
                    self.fire({"event": "SequenceEnded"})
                    Logger.log(
                        LOG_LEVEL["info"],
                        f'Sequence {FONT_CYAN}{self.name}{FONT_RESET} Completed'
                    )
                self.reset_duration()

    def previous_step(self, event_data=None):
        """ Go to the previous step """
        if self._current_step > 0:
            self._current_step -= 1
            self.fire({"event": "SequenceStepStarted" })
        self.reset_step()
        self.reset_duration()

    def advance_step(self, event_data=None):
        """ Advances the next step non-forcefully
            only if delays/duration are completed. 
        """
        if not self.active:
            self.start()
            return

        if self.step_duration is None and self._delay_complete:
            self._step_complete = True

        self.next_step()

    def skip_step(self, event_data=None):
        """ Skips the current step without triggering """
        self._step_complete = True
        self._step_triggered = True

    def handle_event(self, message):
        """ Process event data for the sequnce """
        data = message['data']
        if data is not None:
            _event_data = self.last_event = decode_event_data(data)
            try:
                if _event_data['event'] == 'SequenceNextStep':
                    self.advance_step()
                    Logger.log(
                        LOG_LEVEL["info"],
                        f'Sequence {self.name} Next Step Triggered'
                    )
                elif _event_data['event'] == 'SequencePreviousStep':
                    self.previous_step()
                    Logger.log(
                        LOG_LEVEL["info"],
                        f'Sequence {self.name} Previous Step Triggered'
                    )
                elif _event_data['event'] == 'SequenceStart':
                    self.start()
                    Logger.log(
                        LOG_LEVEL["info"],
                        f'Sequence {self.name} Start Triggered'
                    )
                elif _event_data['event'] == 'SequenceSkipStep':
                    self.skip_step()
                    Logger.log(
                        LOG_LEVEL["info"],
                        f'Sequence {self.name} Skip Step Triggered'
                    )
                elif _event_data['event'] == 'SequenceStop':
                    self.stop()
                    Logger.log(
                        LOG_LEVEL["info"],
                        f'Sequence {self.name} Stop Triggered'
                    )
            except:
                Logger.log(
                    LOG_LEVEL["info"],
                    f"Error Decoding Event for Sequence {self.id}"
                )

    def trigger(self, value=None):
        """ Trigger all the actions for the current step """
        if self._step_triggered:
            return

        try:
            for action in self.current_step.get('actions', []):
                if self.mudpi.actions.exists(action):
                    _data = value or {}
                    self.mudpi.actions.call(action, action_data=_data)
        except Exception as e:
            Logger.log(
                LOG_LEVEL["error"],
               f"Error triggering sequence action {self.id} ", e)
        self._step_triggered = True
        return

    def evaluate_thresholds(self):
        """ Check critera if step should activate """
        thresholds_passed = False
        if self.current_step.get('thresholds') is not None:
            for threshold in self.current_step.get('thresholds', []):
                key = threshold.get("source")
                # Get state object from manager
                state = self.mudpi.states.get(key)
                if state is not None:
                    _state = json.loads(state.state)
                    if threshold.get("nested_source") is not None:
                        nested_source = threshold['nested_source'].lower()
                        try:
                            value = _state.get(nested_source)
                        except:
                            value = _state
                    else:
                        value = _state
                        # state = json.loads(state.decode('utf-8'))
                    comparison = threshold.get("comparison", "eq")
                    if comparison == "eq":
                        if value == threshold["value"]:
                            thresholds_passed = True
                        else:
                            thresholds_passed = False
                    elif comparison == "ne":
                        if value != threshold["value"]:
                            thresholds_passed = True
                        else:
                            thresholds_passed = False
                    elif comparison == "gt":
                        if value > threshold["value"]:
                            thresholds_passed = True
                        else:
                            thresholds_passed = False
                    elif comparison == "gte":
                        if value >= threshold["value"]:
                            thresholds_passed = True
                        else:
                            thresholds_passed = False
                    elif comparison == "lt":
                        if value < threshold["value"]:
                            thresholds_passed = True
                        else:
                            thresholds_passed = False
                    elif comparison == "lte":
                        if value <= threshold["value"]:
                            thresholds_passed = True
                        else:
                            thresholds_passed = False
                    elif comparison == "ex":
                        if value is not None:
                            thresholds_passed = True
                        else:
                            thresholds_passed = False
                else:
                # Data was null 
                    comparison = threshold.get("comparison", "eq")
                    # Comparison if data not exists
                    if comparison == "nex":
                        thresholds_passed = True
                    else:
                        # Threshold set but data not found and
                        # not checking for 'not exists'
                        thresholds_passed = False
        else:
            # No thresholds for this step, proceed.
            thresholds_passed = True
        return thresholds_passed