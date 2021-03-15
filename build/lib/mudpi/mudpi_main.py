""" MudPi Core
Author: Eric Davisson (@theDavisson) [EricDavisson.com]
https://mudpi.app

MudPi Core is a python library to gather sensor readings,
control components, and manage devices using a Raspberry Pi 
on an event based system.
"""

import time
import json
import redis
import socket
import threading
import datetime

from adafruit_platformdetect import Detector

from . import constants
from action import Action

from server.mudpi_server import MudpiServer
from workers.linux.lcd_worker import LcdWorker
from workers.trigger_worker import TriggerWorker
from workers.sequence_worker import SequenceWorker
from workers.linux.relay_worker import RelayWorker
from workers.linux.i2c_worker import LinuxI2CWorker
from workers.linux.sensor_worker import LinuxSensorWorker
from workers.linux.control_worker import LinuxControlWorker

try:
    from workers.arduino.arduino_worker import ArduinoWorker

    NANPY_ENABLED = True
except ImportError:
    NANPY_ENABLED = False

try:
    from workers.adc_worker import ADCMCP3008Worker

    MCP_ENABLED = True
except (ImportError, AttributeError):
    MCP_ENABLED = False

from logger.Logger import Logger, LOG_LEVEL

detector = Detector()
if detector.board.any_raspberry_pi:
    from workers.linux.camera_worker import CameraWorker

PROGRAM_RUNNING = True

# Variables and LOAD CONFIG
# TODO: REPLACE WITH THE NEW LOGIC HERE

# Print a display logo for startup

# Load Configs

# Debug Check

# Load the Logger

try:
    # Prepare Core and Threads

    # Worker for Camera
    try:
        if len(CONFIGS["camera"]) > 0:
            CONFIGS["camera"]["redis"] = r
            c = CameraWorker(
                CONFIGS['camera'],
                main_thread_running,
                system_ready,
                camera_available
            )
            Logger.log(
                LOG_LEVEL["info"],
                'Camera...\t\t\t\033[1;32m Initializing\033[0;0m'
            )
            workers.append(c)
            camera_available.set()
    except KeyError:
        Logger.log(
            LOG_LEVEL["info"],
            'Pi Camera...\t\t\t\t\033[1;31m Disabled\033[0;0m'
        )

    # Workers for board (Sensors, Controls, Relays, I2C)
    try:
        if len(CONFIGS["workers"]) > 0:

            for worker in CONFIGS['workers']:
                # Create worker for worker
                worker["redis"] = r

                if worker['type'] == "sensor":
                    pw = LinuxSensorWorker(
                        worker,
                        main_thread_running,
                        system_ready
                    )
                    Logger.log(
                        LOG_LEVEL["info"],
                        'Sensors...\t\t\t\t\033[1;32m Initializing\033[0;0m'
                    )

                elif worker['type'] == "control":
                    pw = LinuxControlWorker(
                        worker,
                        main_thread_running,
                        system_ready
                    )
                    Logger.log(
                        LOG_LEVEL["info"],
                        'Controls...\t\t\t\t\033[1;32m Initializing\033[0;0m'
                    )

                elif worker['type'] == "i2c":
                    pw = LinuxI2CWorker(worker, main_thread_running, system_ready)
                    Logger.log(
                        LOG_LEVEL["info"],
                        'I2C Comms...\t\t\t\t\033[1;32m Initializing\033[0;0m'
                    )

                elif worker['type'] == "display":
                    for display in worker['displays']:
                        display["redis"] = r
                        pw = LcdWorker(
                            display,
                            main_thread_running,
                            system_ready,
                            lcd_available
                        )
                        lcd_available.set()
                        Logger.log(
                            LOG_LEVEL["info"],
                            'LCD Displays...\t\t\t\t\033[1;32m Initializing\033[0;0m'
                        )

                elif worker['type'] == "relay":
                    # Add Relay Worker Here for Better Config Control
                    Logger.log(LOG_LEVEL["info"],
                               'Relay...\t\t\t\033[1;32m Initializing\033[0;0m')

                else:
                    Logger.log(
                        LOG_LEVEL["warning"],
                        "Exception raised due to unknown Worker Type: {0}".format(
                            worker['type']))
                    raise Exception("Unknown Worker Type: " + worker['type'])
                workers.append(pw)

    except KeyError as e:
        Logger.log(
            LOG_LEVEL["info"],
            'Pi Workers...\t\t\t\t\033[1;31m Disabled\033[0;0m'
        )
        print(e)



    # Worker for nodes attached to board via serial or wifi[esp8266, esp32]
    # Supported nodes: arduinos, esp8266, ADC-mcp3xxx, probably others
    # (esp32 with custom nanpy fork)
    try:
        if len(CONFIGS["nodes"]) > 0:
            for node in CONFIGS['nodes']:
                node["redis"] = r

                if node['type'] == "arduino":
                    if NANPY_ENABLED:
                        Logger.log(
                            LOG_LEVEL["info"],
                            'MudPi Arduino Workers...\t\t\033[1;32m Initializing\033[0;0m'
                        )
                        t = ArduinoWorker(node, main_thread_running,
                                          system_ready)
                    else:
                        Logger.log(
                            LOG_LEVEL["error"],
                            'Error Loading Nanpy library. Did you pip3 install -r requirements.txt?'
                        )

                elif node['type'] == "ADC-MCP3008":
                    if MCP_ENABLED:
                        Logger.log(
                            LOG_LEVEL["info"],
                            'MudPi ADC Workers...\t\t\033[1;32m Initializing\033[0;0m'
                        )
                        t = ADCMCP3008Worker(node, main_thread_running,
                                             system_ready)
                    else:
                        Logger.log(
                            LOG_LEVEL["error"],
                            'Error Loading mcp3xxx library. Did you pip3 install -r requirements.txt;?'
                        )

                else:
                    Logger.log(
                        LOG_LEVEL["warning"],
                        "Exception raised due to unknown Node Type: {0}".format(
                            node['type'])
                    )
                    raise Exception("Unknown Node Type: " + node['type'])
                nodes.append(t)
    except KeyError as e:
        Logger.log(
            LOG_LEVEL["info"],
            'MudPi Node Workers...\t\t\t\033[1;31m Disabled\033[0;0m'
        )

    # try:
    #     if (CONFIGS['server'] is not None):
    #         Logger.log(LOG_LEVEL["info"], 'MudPi Server...\t\t\t\t\033[1;33m Starting\033[0;0m', end='\r', flush=True)
    #         time.sleep(1)
    #         server = MudpiServer(main_thread_running, CONFIGS['server']['host'], CONFIGS['server']['port'])
    #         s = threading.Thread(target=server_worker)  # TODO where is server_worker supposed to be initialized?
    #         threads.append(s)
    #         s.start()
    # except KeyError:
    #     Logger.log(LOG_LEVEL["info"], 'MudPi Socket Server...\t\t\t\033[1;31m Disabled\033[0;0m')

    Logger.log(
        LOG_LEVEL["info"],
        'MudPi Garden Controls...\t\t\033[1;32m Initialized\033[0;0m'
    )
    Logger.log(
        LOG_LEVEL["info"],
        'Engaging MudPi Workers...\t\t\033[1;32m \033[0;0m'
    )

    for worker in workers:
        t = worker.run()
        threads.append(t)
        time.sleep(.5)
    for node in nodes:
        t = node.run()
        threads.append(t)
        time.sleep(.5)

    time.sleep(.5)

    Logger.log(
        LOG_LEVEL["info"],
        'MudPi Garden Control...\t\t\t\033[1;32m Online\033[0;0m'
    )
    Logger.log(
        LOG_LEVEL["info"],
        '_________________________________________________'
    )
    # Workers will not process until system is ready
    system_ready.set()
    # Store current time to track uptime
    r.set('started_at', str(datetime.datetime.now()))
    system_message = {'event': 'SystemStarted', 'data': 1}
    r.publish('mudpi', json.dumps(system_message))

    # Hold the program here until its time to graceful shutdown
    while PROGRAM_RUNNING:
        # Main program loop
        # add logging or other system operations here...
        time.sleep(0.1)

except KeyboardInterrupt:
    PROGRAM_RUNNING = False
finally:
    Logger.log(LOG_LEVEL["info"], 'MudPi Shutting Down...')
    # Perform any cleanup tasks here...

    try:
        server.sock.shutdown(socket.SHUT_RDWR)
    except Exception:
        pass

    # Clear main running event to signal threads to close
    main_thread_running.clear()

    # Shutdown the camera loop
    camera_available.clear()

    # Join all our threads for shutdown
    for thread in threads:
        thread.join()

    Logger.log(
        LOG_LEVEL["info"],
        "MudPi Shutting Down...\t\t\t\033[1;32m Complete\033[0;0m"
    )
    Logger.log(
        LOG_LEVEL["info"],
        "Mudpi is Now...\t\t\t\t\033[1;31m Offline\033[0;0m"
    )
