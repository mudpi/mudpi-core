import sys
import time
import json
import redis
import datetime
import threading
import importlib
from mudpi.workers import Worker

from mudpi.triggers.time_trigger import TimeTrigger
from mudpi.triggers.trigger_group import TriggerGroup
from mudpi.triggers.sensor_trigger import SensorTrigger
from mudpi.triggers.control_trigger import ControlTrigger
from mudpi.constants import FONT_RESET, YELLOW_BACK, GREEN_BACK, FONT_GREEN, FONT_RED, FONT_YELLOW, FONT_PADDING

from mudpi.logger.Logger import Logger, LOG_LEVEL


class TriggerWorker(Worker):
    def __init__(self, mudpi, config):
        super().__init__(mudpi, config)
        self.actions = mudpi.actions
        self.sequences = mudpi.sequences

        if self.config.get('key', None) is None:
            raise Exception('No "key" Found in Trigger Config')
        else:
            self.key = self.config['key'].replace(" ", "_").lower()

        self.triggers = []
        self.trigger_threads = []
        self.trigger_events = {}
        self.init()
        return

    def init(self):
        super().init()
        trigger_index = 0
        for trigger_config in self.config.get("triggers", []):
            if trigger_config.get("triggers", False):
                # Load a trigger group

                trigger_actions = []
                if trigger_config.get('actions'):
                    for action in trigger_config.get("actions"):
                        trigger_actions.append(self.actions[action])

                new_trigger_group = TriggerGroup(name=trigger_config.get("group"),
                                                 key=trigger_config.get("key"),
                                                 actions=trigger_actions,
                                                 frequency=trigger_config.get(
                                                     "frequency", "once"))

                for trigger in trigger_config.get("triggers"):
                    new_trigger = self.init_trigger(trigger, trigger_index,
                                                    group=new_trigger_group)
                    self.triggers.append(new_trigger)
                    new_trigger_group.add_trigger(new_trigger)
                    # Start the trigger thread
                    trigger_thread = new_trigger.run()
                    self.trigger_threads.append(trigger_thread)
                    trigger_index += 1
            else:
                new_trigger = self.init_trigger(trigger, trigger_index)
                self.triggers.append(new_trigger)
                # Start the trigger thread
                trigger_thread = new_trigger.run()
                self.trigger_threads.append(trigger_thread)
                trigger_index += 1
            # print('{type} - {name}...\t\t\033[1;32m Listening\033[0;0m'.format(**trigger))
        return

    def init_trigger(self, config, trigger_index, group=None):
        if config.get('type', None) is not None:
            # Get the trigger from the triggers folder triggers/{trigger type}_trigger.py
            trigger_type = 'triggers.' + config.get(
                'type').lower() + '_trigger.' + config.get(
                'type').capitalize() + 'Trigger'

            imported_trigger = self.dynamic_import(trigger_type)

            trigger_state = {
                "active": threading.Event()
                # Event to signal if trigger is active
            }

            self.trigger_events[
                config.get("key", trigger_index)] = trigger_state

            # Define default kwargs for all trigger types, conditionally include optional variables below if they exist
            trigger_kwargs = {
                'name': config.get('name', None),
                'key': config.get('key', None),
                'trigger_active': trigger_state["active"],
                'main_thread_running': self.mudpi.thread_events["mudpi_running"],
                'system_ready': self.mudpi.thread_events["core_running"]
            }

            # optional trigger variables
            if config.get('actions'):
                trigger_actions = []
                for action in config.get("actions"):
                    trigger_actions.append(self.actions[action])
                trigger_kwargs['actions'] = trigger_actions

            if config.get('sequences'):
                trigger_sequences = []
                for sequence in config.get("sequences"):
                    trigger_sequences.append(self.sequences[sequence])
                trigger_kwargs['sequences'] = trigger_sequences

            if config.get('frequency'):
                trigger_kwargs['frequency'] = config.get('frequency')

            if config.get('schedule'):
                trigger_kwargs['schedule'] = config.get('schedule')

            if config.get('source'):
                trigger_kwargs['source'] = config.get('source')

            if config.get('nested_source'):
                trigger_kwargs['nested_source'] = config.get('nested_source')

            if config.get('topic'):
                trigger_kwargs['topic'] = config.get('topic')

            if config.get('thresholds'):
                trigger_kwargs['thresholds'] = config.get('thresholds')

            if group is not None:
                trigger_kwargs['group'] = group

            new_trigger = imported_trigger(**trigger_kwargs)
            new_trigger.init_trigger()

            new_trigger.type = config.get('type').lower()

            return new_trigger

    def run(self):
        Logger.log(LOG_LEVEL["warning"], f'{f"Trigger [{self.key}]...":.<{FONT_PADDING}} {FONT_GREEN}Working{FONT_RESET}')
        return super().run()

    def work(self):
        while self.mudpi.thread_events["mudpi_running"].is_set():
            if self.mudpi.thread_events["core_running"].is_set():
                # Main Loop
                time.sleep(1)

            time.sleep(2)
        # This is only ran after the main thread is shut down
        Logger.log(LOG_LEVEL["info"],
                   f"{f'Trigger [{self.key}]...':.<{FONT_PADDING}} {FONT_YELLOW}Stopping{FONT_RESET}")
        for trigger in self.triggers:
            trigger.shutdown()
        # Join all our sub threads for shutdown
        for thread in self.trigger_threads:
            thread.join()
        Logger.log(LOG_LEVEL["info"],
                   f"{f'Trigger [{self.key}]...':.<{FONT_PADDING}} {FONT_RED}Shutdown{FONT_RESET}")
