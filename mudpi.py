"""MudPi Core
Author: Eric Davisson (@theDavisson) [EricDavisson.com]
https://mudpi.app
MudPi Core is a python library to gather sensor readings,
control components,
and manage devices using a Raspberry Pi on an event based system
using redis.
"""

import RPi.GPIO as GPIO
import threading
import datetime
import socket
import redis
import time
import json
import sys

# TODO: This might not be needed and could be deleted
sys.path.append('..')
from action import Action
from config_load import load_config_json
from server.mudpi_server import MudpiServer
from workers.linux.lcd_worker import LcdWorker
from workers.linux.i2c_worker import PiI2CWorker
from workers.linux.relay_worker import RelayWorker
from workers.linux.camera_worker import CameraWorker
from workers.linux.sensor_worker import PiSensorWorker
# from workers.pi.control_worker import PiControlWorker
from workers.trigger_worker import TriggerWorker
from workers.sequence_worker import SequenceWorker
try:
    from workers.arduino.arduino_worker import ArduinoWorker
    NANPY_ENABLED = True
except ImportError:
    NANPY_ENABLED = False
try:
    from workers.adc_worker import ADCMCP3008Worker
    MCP_ENABLED = True
except ImportError:
    MCP_ENABLED = False

from logger.Logger import Logger, LOG_LEVEL
import variables

CONFIGS = {}
PROGRAM_RUNNING = True
threads = []
actions = {}
sequences = {}
relays = []
relayEvents = {}
relay_index = 0
sequenceEvents = {}
sequence_index = 0
workers = []
nodes = []

print(chr(27) + "[2J")
print('Loading MudPi Configs...\r', end="", flush=True)
CONFIGS = load_config_json()
# Singleton redis to prevent connection conflicts
try:
    r = redis.Redis(host=CONFIGS['redis'].get('host', '127.0.0.1'),
                    port=int(CONFIGS['redis'].get('port', 6379)))
except KeyError:
    r = redis.Redis(host='127.0.0.1', port=6379)
# Waiting for redis and services to be running
time.sleep(5)
print('Loading MudPi Configs...\t\033[1;32m Complete\033[0;0m')
print(chr(27) + "[2J")
# Print a display logo for startup
print("\033[1;32m")
print(r' __  __           _ _____ _ ')
print(r'|  \/  |         | |  __ (_)')
print(r'| \  / |_   _  __| | |__) | ')
print(r'| |\/| | | | |/ _` |  ___/ | ')
print(r'| |  | | |_| | (_| | |   | | ')
print(r'|_|  |_|\__,_|\__,_|_|   |_| ')
print('_________________________________________________')
print('')
print('Eric Davisson @theDavisson')
print('https://mudpi.app')
print('Version: ', CONFIGS.get('version', '0.9.1'))
print('\033[0;0m')

if CONFIGS['debug'] is True:
    print('\033[1;33mDEBUG MODE ENABLED\033[0;0m')
    print("Loaded Config\n--------------------")
    for index, config in CONFIGS.items():
        if config != '':
            print('%s: %s' % (index, config))
    time.sleep(10)

try:
    print('Initializing Logger \r', end="", flush=True)
    Logger.logger = Logger(CONFIGS)
    time.sleep(0.05)
    Logger.log(
        LOG_LEVEL["info"],
        'Initializing Logger...\t\t\t\033[1;32m Complete\033[0;0m'
    )
    Logger.log_to_file(LOG_LEVEL["debug"], "Dumping the config file: ")
    for index, config in CONFIGS.items():
        Logger.log_to_file(LOG_LEVEL["debug"], '%s: %s' % (index, config))
    Logger.log_to_file(LOG_LEVEL["debug"], "End of config file dump!\n")
except Exception as e:
    Logger.log(
        LOG_LEVEL["info"],
        'Initializing Logger...\t\t\t\033[1;31m Disabled\033[0;0m'
    )

try:
    print('Initializing Garden Control \r', end="", flush=True)
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()
    # Pause for GPIO to finish
    time.sleep(0.1)
    Logger.log(
        LOG_LEVEL["info"],
        'Initializing Garden Control...\t\t\033[1;32m Complete\033[0;0m'
    )
    print('Preparing Threads for Workers\r', end="", flush=True)

    # Event to signal LCD to pull new messages
    new_messages_waiting = threading.Event()
    # Event to signal workers to close
    main_thread_running = threading.Event()
    # Event to tell workers to begin working
    system_ready = threading.Event()
    # Event to signal if camera can be used
    camera_available = threading.Event()
    # Event to signal if lcd displays can be used
    lcd_available = threading.Event()

    # Main event to tell workers to run/shutdown
    main_thread_running.set()
    time.sleep(0.1)
    Logger.log(
        LOG_LEVEL["info"],
        'Preparing Threads for Workers...\t\033[1;32m Complete\033[0;0m'
    )

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

    # Workers for pi (Sensors, Controls, Relays, I2C)
    try:
        if len(CONFIGS["workers"]) > 0:

            for worker in CONFIGS['workers']:
                # Create worker for worker
                worker["redis"] = r

                if worker['type'] == "sensor":
                    pw = PiSensorWorker(
                        worker,
                        main_thread_running,
                        system_ready
                    )
                    Logger.log(
                        LOG_LEVEL["info"],
                        'Sensors...\t\t\t\t\033[1;32m Initializing\033[0;0m'
                    )

                elif worker['type'] == "control":
                    pw = PiControlWorker(
                        worker,
                        main_thread_running,
                        system_ready
                    )
                    Logger.log(
                        LOG_LEVEL["info"],
                        'Controls...\t\t\t\t\033[1;32m Initializing\033[0;0m'
                    )

                elif worker['type'] == "i2c":
                    pw = PiI2CWorker(worker, main_thread_running, system_ready)
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

    # Worker for relays attached to pi
    try:
        if len(CONFIGS["relays"]) > 0:
            for relay in CONFIGS['relays']:
                relay["redis"] = r

                relayState = {
                    # Event to allow relay to activate
                    "available": threading.Event(),
                    # Event to signal relay to open/close
                    "active": threading.Event()
                }
                relayEvents[relay.get("key", relay_index)] = relayState
                rw = RelayWorker(
                    relay,
                    main_thread_running,
                    system_ready,
                    relayState['available'],
                    relayState['active']
                )
                workers.append(rw)
                # Make the relays available, this event is toggled off
                # elsewhere if we need to disable relays
                relayState['available'].set()
                relay_index += 1
    except KeyError:
        Logger.log(
            LOG_LEVEL["info"],
            'Relays Workers...\t\t\033[1;31m Disabled\033[0;0m'
        )

    # Load in Actions
    try:
        if len(CONFIGS["actions"]) > 0:
            for action in CONFIGS["actions"]:
                action["redis"] = r
                a = Action(action)
                a.init_action()
                actions[a.key] = a
            Logger.log(
                LOG_LEVEL["info"],
                '{0} Actions...\t\t\t\t\033[1;32m Initializing\033[0;0m'.format(
                    len(CONFIGS['actions'])))
    except KeyError:
        Logger.log(LOG_LEVEL["info"],
                   'Actions...\t\t\t\t\033[1;31m Disabled\033[0;0m')

    # Worker for Sequences
    try:
        if len(CONFIGS["sequences"]) > 0:
            for sequence in CONFIGS["sequences"]:
                sequence["redis"] = r
                sequenceState = {
                    "available": threading.Event(),
                    # Event to allow sequence to activate
                    "active": threading.Event()
                    # Event to signal sequence to open/close
                }
                sequenceEvents[
                    sequence.get("key", sequence_index)] = sequenceState
                s = SequenceWorker(
                    sequence,
                    main_thread_running,
                    system_ready,
                    sequenceState['available'],
                    sequenceState['active'],
                    actions
                )
                workers.append(s)
                sequences[s.key] = s
                sequenceState['available'].set()
                sequence_index += 1
        Logger.log(
            LOG_LEVEL["info"],
            '{0} Sequences...\t\t\t\t\033[1;32m Initializing\033[0;0m'.format(
                len(CONFIGS["sequences"]))
        )
    except KeyError:
        Logger.log(
            LOG_LEVEL["info"],
            'Sequences...\t\t\t\t\033[1;31m Disabled\033[0;0m'
        )

    # Worker for Triggers
    try:
        if len(CONFIGS["triggers"]) > 0:
            for trigger in CONFIGS["triggers"]:
                trigger["redis"] = r
            t = TriggerWorker(
                CONFIGS['triggers'],
                main_thread_running,
                system_ready,
                actions,
                sequences
            )
            Logger.log(
                LOG_LEVEL["info"],
                'Triggers...\t\t\t\t\033[1;32m Initializing\033[0;0m'
            )
            workers.append(t)
    except KeyError:
        Logger.log(
            LOG_LEVEL["info"],
            'Triggers...\t\t\t\t\033[1;31m Disabled\033[0;0m'
        )

    # Worker for nodes attached to pi via serial or wifi[esp8266, esp32]
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
    # 	if (CONFIGS['server'] is not None):
    # 		Logger.log(LOG_LEVEL["info"], 'MudPi Server...\t\t\t\t\033[1;33m Starting\033[0;0m', end='\r', flush=True)
    # 		time.sleep(1)
    # 		server = MudpiServer(main_thread_running, CONFIGS['server']['host'], CONFIGS['server']['port'])
    # 		s = threading.Thread(target=server_worker)  # TODO where is server_worker supposed to be initialized?
    # 		threads.append(s)
    # 		s.start()
    # except KeyError:
    # 	Logger.log(LOG_LEVEL["info"], 'MudPi Socket Server...\t\t\t\033[1;31m Disabled\033[0;0m')

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
