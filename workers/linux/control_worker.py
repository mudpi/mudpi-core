import sys
import time

from utils import get_config_item
from workers.linux.worker import Worker

from controls.linux.button_control import (ButtonControl)
from controls.linux.switch_control import (SwitchControl)

from logger.Logger import Logger, LOG_LEVEL


class LinuxControlWorker(Worker):
    def __init__(self, config, main_thread_running, system_ready):
        super().__init__(config, main_thread_running, system_ready)
        self.topic = get_config_item(self.config, 'topic', 'controls')
        self.sleep_duration = config.get('sleep_duration', 0.5)

        self.controls = []
        self.init()
        return

    def init(self):
        for control in self.config['controls']:
            if control.get('type', None) is not None:
                # Get the control from the controls folder
                # {control name}_control.{ControlName}Control
                control_type = 'controls.linux.'
                control_type += control.get('type').lower()
                control_type += '_control.'
                control_type += control.get('type').capitalize() + 'Control'

                imported_control = self.dynamic_import(control_type)

                # Define default kwargs for all control types,
                # conditionally include optional variables below if they exist
                control_kwargs = {
                    'name': control.get('name', None),
                    'pin': int(control.get('pin')),
                    'key': control.get('key', None),
                    'topic': control.get('topic', None),
                    'resistor': control.get('resistor', None),
                    'edge_detection': control.get('edge_detection', None),
                    'debounce': control.get('debounce', None)
                }

                # optional control variables
                # add conditional control vars here...

                new_control = imported_control(**control_kwargs)

                new_control.init_control()
                self.controls.append(new_control)
                Logger.log(
                    LOG_LEVEL["info"],
                    '{type} Control {pin}...\t\t\t\033[1;32m Ready\033[0;0m'.format(
                        **control)
                )
        return

    def run(self):
        Logger.log(
            LOG_LEVEL["info"],
            'Pi Control Worker [' + str(
                len(self.config['controls'])
            ) + ' Controls]...\t\033[1;32m Online\033[0;0m'
        )
        return super().run()

    def work(self):
        while self.main_thread_running.is_set():
            if self.system_ready.is_set():
                readings = {}
                for control in self.controls:
                    result = control.read()
                    readings[control.key] = result
            time.sleep(self.sleep_duration)
        # This is only ran after the main thread is shut down
        Logger.log(
            LOG_LEVEL["info"],
            "Pi Control Worker Shutting Down...\t\033[1;32m Complete\033[0;0m"
        )
