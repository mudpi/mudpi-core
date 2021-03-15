import json
import threading
import sys


from mudpi.logger.Logger import Logger, LOG_LEVEL


class Trigger():

    def __init__(self, main_thread_running, system_ready, name=None, key=None,
                 source=None, thresholds=None, trigger_active=None,
                 frequency='once', actions=[], trigger_interval=1, group=None,
                 sequences=[]):

        if key is None:
            raise Exception('No "key" Found in Trigger Config')
        else:
            self.key = key.replace(" ", "_").lower()

        if name is None:
            self.name = self.key.replace("_", " ").title()
        else:
            self.name = name

        self.thresholds = thresholds
        self.source = source.lower() if source is not None else source
        self.trigger_interval = trigger_interval
        self.actions = actions
        self.sequences = sequences
        self.group = group
        self.frequency = frequency if group is None else "many"
        # Used to check if trigger already fired without reseting
        self.trigger_active = trigger_active
        self.previous_state = trigger_active.is_set()
        # Main thread events
        self.main_thread_running = main_thread_running
        self.system_ready = system_ready
        return

    def init_trigger(self):
        # Initialize the trigger here (i.e. set listeners or create cron jobs)
        pass

    def check(self):
        # Main trigger check loop to do things like
        # fetch messages or check time
        if self.group is not None:
            self.group.check_group()
        return

    def run(self):
        t = threading.Thread(target=self.check, args=())
        t.start()
        return t

    def trigger(self, value=None):
        try:
            if self.group is None:
                # Trigger the actions of the trigger
                for action in self.actions:
                    action.trigger(value)
                # Trigger the sequences of the trigger
                for sequence in self.sequences:
                    sequence.update(value)
            else:
                self.group.trigger()
        except Exception as e:
            Logger.log(LOG_LEVEL["error"],
                       "Error triggering action {0} ".format(self.key), e)
            pass
        return

    def evaluate_thresholds(self, value):
        thresholds_passed = False
        for threshold in self.thresholds:
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

        return thresholds_passed

    def decode_event_data(self, message):
        if isinstance(message, dict):
            # print('Dict Found')
            return message

        elif isinstance(message.decode('utf-8'), str):
            try:
                temp = json.loads(message.decode('utf-8'))
                # print('Json Found')
                return temp
            except:
                # print('Json Error. Str Found')
                return {'event': 'Unknown', 'data': message}

        else:
            # print('Failed to detect type')
            return {'event': 'Unknown', 'data': message}

    def shutdown(self):
        # Put any closing functions here that should be called as
        # MudPi shutsdown (i.e. close connections)
        return
