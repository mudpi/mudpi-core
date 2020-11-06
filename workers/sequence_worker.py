import time
import datetime
import json
import redis
import threading
from .worker import Worker
import sys

sys.path.append('..')

import variables
import importlib

from logger.Logger import Logger, LOG_LEVEL


class SequenceWorker(Worker):
    def __init__(self, config, main_thread_running, system_ready,
                 sequence_available, sequence_active, actions):
        super().__init__(config, main_thread_running, system_ready)

        if self.config.get('key', None) is None:
            raise Exception('No "key" Found in Sequence Config')
        else:
            self.key = self.config['key'].replace(" ", "_").lower()

        if self.config.get('name', None) is None:
            self.name = self.key.replace("_", " ").title()
        else:
            self.name = self.config.get('name', '')

        self.actions = actions
        self.sequence = self.config['sequence'] if self.config[
                                                       'sequence'] is not None else []
        self.key = self.config.get(
            'key', '').replace(" ", "_").lower() if self.config.get(
            'key', None) is not None else self.name.replace(" ", "_").lower()
        self.topic = self.config.get(
            'topic', '').replace(" ", "/").lower() if self.config.get(
            'topic', None) is not None else 'mudpi/sequences/' + self.key
        self.current_step = 0
        self.total_steps = len(self.sequence)
        self.delay_complete = False
        self.step_complete = False
        self.step_triggered = False

        # Events
        self.sequence_available = sequence_available
        self.sequence_active = sequence_active

        # PubSub
        try:
            self.r = config["redis"]
        except KeyError:
            self.r = redis.Redis(host='127.0.0.1', port=6379)

        # Pubsub Listeners
        self.pubsub = self.r.pubsub()

        self.reset_elapsed_time()
        self.init()
        return

    def init(self):
        self.pubsub.subscribe(**{self.topic: self.handle_message})
        # Logger.log(LOG_LEVEL["info"], '{type} - {name}...\t\t\033[1;32m Listening\033[0;0m'.format(**trigger))
        return

    def reset_step(self):
        self.delay_complete = False
        self.step_triggered = False
        self.step_complete = False

    def update(self, value=None):
        if not self.sequence_active.is_set():
            self.start()
        else:
            if self.sequence[self.current_step].get('duration',
                                                    None) is None and self.delay_complete:
                self.step_complete = True
            self.next_step()

    def start(self):
        if not self.sequence_active.is_set():
            self.current_step = 0
            self.sequence_active.set()
            self.reset_step()
            self.r.publish(self.topic, json.dumps({
                "event": "SequenceStarted",
                "data": {
                    "name": self.name,
                    "key": self.key
                }
            }))
            Logger.log(
                LOG_LEVEL["info"],
                'Sequence {0} Started\033[0;0m'.format(self.name)
            )

    def stop(self):
        if self.sequence_active.is_set():
            self.current_step = 0
            self.sequence_active.clear()
            self.reset_step()
            self.r.publish(self.topic, json.dumps({
                "event": "SequenceStopped",
                "data": {
                    "name": self.name,
                    "key": self.key
                }
            }))
            Logger.log(
                LOG_LEVEL["info"],
                'Sequence {0} Stopped\033[0;0m'.format(self.name)
            )

    def next_step(self):
        if self.step_complete:
            # Step must be flagged complete to advance
            if self.sequence_active.is_set():
                # If skipping steps trigger unperformed actions
                if not self.step_triggered:
                    if self.evaluate_thresholds():
                        self.trigger()
                # Sequence is already active, advance to next step
                if self.current_step < self.total_steps - 1:
                    self.reset_step()
                    self.current_step += 1
                    self.r.publish(
                        self.topic,
                        json.dumps(
                            {
                                "event": "SequenceStepStarted",
                                "data": {
                                    "name": self.name,
                                    "key": self.key,
                                    "step": self.current_step
                                }
                            }
                        )
                    )
                else:
                    # Last step of seqence completed
                    self.sequence_active.clear()
                    self.r.publish(self.topic, json.dumps({
                        "event": "SequenceEnded",
                        "data": {
                            "name": self.name,
                            "key": self.key
                        }
                    }))
                self.reset_elapsed_time()

    def previous_step(self):
        if self.current_step > 0:
            self.reset_step()
            self.current_step -= 1
            self.r.publish(self.topic, json.dumps({
                "event": "SequenceStepStarted",
                "data": {
                    "name": self.name,
                    "key": self.key,
                    "step": self.current_step
                }
            }))
        self.reset_elapsed_time()

    def handle_message(self, message):
        data = message['data']
        if data is not None:
            decoded_message = self.last_event = self.decode_message_data(data)
            try:
                if decoded_message['event'] == 'SequenceNextStep':
                    if self.sequence[self.current_step].get('duration',
                                                            None) is None and self.delay_complete:
                        self.step_complete = True
                    Logger.log(
                        LOG_LEVEL["info"],
                        'Sequence {0} Next Step Triggered\033[0;0m'.format(
                            self.name)
                    )
                elif decoded_message['event'] == 'SequencePreviousStep':
                    self.previous_step()
                    Logger.log(
                        LOG_LEVEL["info"],
                        'Sequence {0} Previous Step Triggered\033[0;0m'.format(
                            self.name)
                    )
                elif decoded_message['event'] == 'SequenceStart':
                    self.start()
                    Logger.log(
                        LOG_LEVEL["info"],
                        'Sequence {0} Start Triggered\033[0;0m'.format(
                            self.name)
                    )
                elif decoded_message['event'] == 'SequenceSkipStep':
                    self.step_complete = True
                    Logger.log(
                        LOG_LEVEL["info"],
                        'Sequence {0} Skip Step Triggered\033[0;0m'.format(
                            self.name)
                    )
                elif decoded_message['event'] == 'SequenceStop':
                    self.stop()
                    Logger.log(
                        LOG_LEVEL["info"],
                        'Sequence {0} Stop Triggered\033[0;0m'.format(
                            self.name)
                    )
            except:
                Logger.log(
                    LOG_LEVEL["info"],
                    'Error Decoding Message for Sequence {0}'.format(
                        self.config['key'])
                )

    def trigger(self, value=None):
        try:
            for action in self.sequence[self.current_step].get('actions', []):
                self.actions[action].trigger(value)
            self.step_triggered = True
        except Exception as e:
            Logger.log(LOG_LEVEL["error"],
                       "Error triggering sequence action {0} ".format(
                           self.key), e)
            pass
        return

    def evaluate_thresholds(self):
        thresholds_passed = False
        if self.sequence[self.current_step].get('thresholds',
                                                None) is not None:
            for threshold in self.sequence[self.current_step].get('thresholds',
                                                                  []):
                key = threshold.get("source", None)
                data = self.r.get(key)
                if data is not None:
                    if threshold.get("nested_source", None) is not None:
                        nested_source = threshold['nested_source'].lower()
                        data = json.loads(data.decode('utf-8'))
                    value = data.get(nested_source,
                                     None) if nested_source is not None else data
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
        else:
            # No thresholds for this step, proceed.
            thresholds_passed = True
        return thresholds_passed

    def wait(self, duration=0):
        time_remaining = duration
        while time_remaining > 0 and self.main_thread_running.is_set():
            self.pubsub.get_message()
            time.sleep(1)
            time_remaining -= 1

    def run(self):
        Logger.log(LOG_LEVEL["info"], 'Sequence Worker [' + str(
            self.name) + ']...\t\033[1;32m Online\033[0;0m')
        return super().run()

    def work(self):
        self.reset_elapsed_time()
        while self.main_thread_running.is_set():
            if self.system_ready.is_set():
                try:
                    self.pubsub.get_message()
                    if self.sequence_available.is_set():
                        if self.sequence_active.is_set():
                            while not self.step_complete:
                                if not self.delay_complete:
                                    if self.sequence[self.current_step].get(
                                            'delay', None) is not None:
                                        self.wait(int(self.sequence[
                                            self.current_step].get(
                                            'delay', 0)))
                                        self.delay_complete = True
                                    else:
                                        # No Delay for this step
                                        self.delay_complete = True
                                if not self.step_triggered:
                                    if self.delay_complete:
                                        if self.evaluate_thresholds():
                                            self.trigger()
                                        else:
                                            if self.sequence[
                                                self.current_step].get(
                                                'thresholds',
                                                None) is not None:
                                                # Thresholds failed skip step waiting
                                                self.step_complete = True
                                if self.sequence[self.current_step].get(
                                        'duration',
                                        None) is not None and not self.step_complete:
                                    self.wait(int(
                                        self.sequence[self.current_step].get(
                                            'duration', 0)))
                                    self.step_complete = True
                                time.sleep(1)
                            if self.step_complete:
                                self.r.publish(self.topic, json.dumps({
                                    "event": "SequenceStepEnded",
                                    "data": {
                                        "name": self.name,
                                        "key": self.key,
                                        "step": self.current_step
                                    }
                                }))
                                self.next_step()
                        else:
                            # Sequence not active and waiting to start
                            time.sleep(1)
                    else:
                        # Sequence Disabled
                        time.sleep(1)
                except Exception as e:
                    Logger.log(LOG_LEVEL["error"],
                               "Sequence Worker {0} \t\033[1;31m Unexpected Error\033[0;0m".format(
                                   self.key))
                    Logger.log(LOG_LEVEL["error"], e)
                    time.sleep(3)
            else:
                # System not ready
                time.sleep(1)
                self.reset_elapsed_time()

            time.sleep(0.1)

        # This is only ran after the main thread is shut down
        # Close the pubsub connection
        self.pubsub.close()
        Logger.log(LOG_LEVEL["info"],
                   "Sequence Worker Shutting Down...\t\033[1;32m Complete\033[0;0m")
