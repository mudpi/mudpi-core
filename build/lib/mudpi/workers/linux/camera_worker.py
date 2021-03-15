"""
This is (for instance) a Raspberry Pi only worker!


The libcamera project (in development), aims to offer an open source stack for
cameras for Linux, ChromeOS and Android.
It will be able to detect and manage all of the exposed camera on the system.
Connected via USB or CSI (Rasperry pi camera).
libcamera developers plan to privide Python bindings:
https://www.raspberrypi.org/blog/an-open-source-camera-stack-for-raspberry-pi-using-libcamera/#comment-1528789

Not available at time of writing: 9 Nov 2020

Once available, we should look forward migrating to this library, as it would
allow our worker to support multiple boards and devices.
"""

import os
import sys
import time
import json
import datetime
import threading

from picamera import PiCamera

from mudpi.workers import Worker
from mudpi.utils import get_config_item
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.constants import __version__, PATH_CONFIG, DEFAULT_CONFIG_FILE, FONT_RESET_CURSOR, FONT_RESET, YELLOW_BACK, GREEN_BACK, FONT_GREEN, FONT_RED, FONT_YELLOW, FONT_PADDING


class CameraWorker(Worker):
    def __init__(self, mudpi, config):
        super().__init__(mudpi, config)
        self.pending_reset = False

        # Events
        if self.config.get("thread_events"):
            self.camera_available = self.config["thread_events"].get("camera_available")
        else:
            self.config["thread_events"] = {}
            self.camera_available = self.config["thread_events"]["camera_available"] = threading.Event()

        # Dynamic Properties based on config
        self.path = get_config_item(self.config, 'path', '/etc/mudpi/img/')
        self.topic = get_config_item(
            self.config, 'topic', 'mudpi/camera/', replace_char="/"
        )

        if self.config['resolution'] is not None:
            self.resolutionX = int(self.config['resolution'].get('x', 1920))
            self.resolutionY = int(self.config['resolution'].get('y', 1080))
        if self.config['delay'] is not None:
            self.hours = int(self.config['delay'].get('hours', 0))
            self.minutes = int(self.config['delay'].get('minutes', 0))
            self.seconds = int(self.config['delay'].get('seconds', 0))

        config = self.config

        self.init()
        return

    def init(self):
        try:
            Logger.log(
                LOG_LEVEL["info"],
                f'{f"Camera Worker {self.key}":.<{FONT_PADDING}} {FONT_YELLOW}Initializing{FONT_RESET}'
            )
            super().init()
            self.camera = PiCamera(
                resolution=(self.resolutionX, self.resolutionY))
            # Below we calibrate the camera for consistent imaging
            self.camera.framerate = 30
            # Wait for the automatic gain control to settle
            time.sleep(2)
            # Now fix the values
            self.camera.shutter_speed = self.camera.exposure_speed
            self.camera.exposure_mode = 'off'
            g = self.camera.awb_gains
            self.camera.awb_mode = 'off'
            self.camera.awb_gains = g
        except Exception:
            self.camera = PiCamera()

        # Pubsub Listeners
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe(**{self.topic: self.handle_event})

        return

    def run(self):
        thread = threading.Thread(target=self.work, args=())
        thread.start()
        self.listener = threading.Thread(target=self.listen, args=())
        self.listener.start()
        Logger.log(LOG_LEVEL["warning"],
                   f"{f'Camera Worker [{self.key}]...':.<{FONT_PADDING}} {FONT_GREEN}Working{FONT_RESET}")
        return thread

    def wait(self):
        # Calculate the delay
        try:
            self.next_time = (datetime.datetime.now() + datetime.timedelta(
                hours=self.hours, minutes=self.minutes,
                seconds=self.seconds)).replace(microsecond=0)
        except Exception:
            # Default every hour
            self.next_time = (
                    datetime.datetime.now() + datetime.timedelta(hours=1)
            ).replace(minute=0, second=0, microsecond=0)
        delay = (self.next_time - datetime.datetime.now()).seconds
        time.sleep(delay)

    def handle_event(self, message):
        data = message['data']
        decoded_message = None

        if data is not None:

            try:
                if isinstance(data, dict):
                    decoded_message = data

                elif isinstance(data.decode('utf-8'), str):
                    temp = json.loads(data.decode('utf-8'))
                    decoded_message = temp
                    if decoded_message['event'] == 'Timelapse':
                        Logger.log(
                            LOG_LEVEL["info"],
                            "Camera Signaled for Reset"
                        )
                        self.config["thread_events"]["camera_available"].clear()
                        self.pending_reset = True
            except Exception:
                Logger.log(LOG_LEVEL["error"],
                           'Error Handling Event for Camera')

    def listen(self):
        while self.mudpi.thread_events["mudpi_running"].is_set():
            if self.mudpi.thread_events["core_running"].is_set():
                if self.config["thread_events"]["camera_available"].is_set():
                    self.pubsub.get_message()
                    time.sleep(1)
                else:
                    delay = (
                                    self.next_time - datetime.datetime.now()
                            ).seconds + 15
                    # wait 15 seconds after next scheduled picture
                    time.sleep(delay)
                    self.config["thread_events"]["camera_available"].set()
            else:
                time.sleep(2)
        return

    def work(self):
        self.reset_elapsed_time()

        while self.mudpi.thread_events["mudpi_running"].is_set():
            if self.mudpi.thread_events["core_running"].is_set():

                if self.config["thread_events"]["camera_available"].is_set():
                    # try:
                    for i, filename in enumerate(
                            self.camera.capture_continuous(
                                self.path + 'mudpi-{counter:05d}.jpg')):

                        if not self.config["thread_events"]["camera_available"].is_set():
                            if self.pending_reset:
                                try:
                                    # cleanup previous file
                                    os.remove(
                                        filename
                                    )
                                    self.pending_reset = False
                                except Exception:
                                    Logger.log(
                                        LOG_LEVEL["error"],
                                        "Error During Camera Reset Cleanup"
                                    )
                            break
                        message = {'event': 'StateChanged', 'data': filename}
                        self.r.set('last_camera_image', filename)
                        self.r.publish(self.topic, json.dumps(message))
                        Logger.log(
                            LOG_LEVEL["debug"],
                            'Image Captured \033[1;36m%s\033[0;0m' % filename
                        )
                        self.wait()
                # except:
                #     print("Camera Worker \t\033[1;31m Unexpected Error\033[0;0m")
                #     time.sleep(30)
                else:
                    time.sleep(1)
                    self.reset_elapsed_time()
            else:
                # System not ready camera should be off
                time.sleep(1)
                self.reset_elapsed_time()

            time.sleep(0.1)

        # This is only ran after the main thread is shut down
        Logger.log(LOG_LEVEL["info"],
                   f"{f'Camera Worker [{self.key}]...':.<{FONT_PADDING}} {FONT_YELLOW}Stopping{FONT_RESET}")
        self.camera.close()
        self.listener.join()
        self.pubsub.close()
        Logger.log(LOG_LEVEL["warning"],
                   f"{f'Camera Worker [{self.key}]...':.<{FONT_PADDING}} {FONT_RED}Shutdown{FONT_RESET}")
