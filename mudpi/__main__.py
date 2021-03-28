""" MudPi Main Run File
Author: Eric Davisson (@theDavisson) [EricDavisson.com]
https://mudpi.app

This is the main entry point for running MudPi.
"""
import os
import sys
import time
import datetime
import argparse
import threading
from mudpi.config import Config
from mudpi import utils, importer
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.managers.core_manager import CoreManager
from mudpi.constants import __version__, PATH_CONFIG, DEFAULT_CONFIG_FILE, \
    FONT_RESET_CURSOR, FONT_RESET, YELLOW_BACK, GREEN_BACK, FONT_GREEN, FONT_RED, FONT_YELLOW, FONT_PADDING
from mudpi.exceptions import ConfigNotFoundError, ConfigFormatError


def main(args=None):
    """ The main run entry. """
    if args is None:
        args = sys.argv[1:]

    arguments = get_arguments()

    ###################################
    ### Make a default config file ###
    if arguments.make_config:
        config_location = os.path.join(os.getcwd(), arguments.config)
        print(f"Generating a default config file at {config_location}")
        if os.path.exists(config_location) and not arguments.overwrite:
            print(f'{FONT_RED}{"File already exists and `--overwrite` was not set."}{FONT_RESET}')
            return
        Config().save_to_file(config_location)
        return

    ######################################
    ### Convert v0.9 configs to v0.10+ ###
    if arguments.migrate_config:
        config_location = os.path.join(os.getcwd(), arguments.config)
        print(f"Converting config file at {config_location}")
        config = Config(config_location)
        config.load_from_file(config_location)
        new_config_path = os.path.join(os.getcwd(), arguments.migrate_config)
        if os.path.exists(new_config_path) and not arguments.overwrite:
            print(f"{FONT_RED}File already exists at {new_config_path}.")
            print(f"Use `--overwrite` to save over existing file.{FONT_RESET}")
            return
        # convert the old configs
        convert_old_config(config)
        config.save_to_file(new_config_path)
        print(f"{FONT_GREEN}Successfully converted config to: {new_config_path}{FONT_RESET}")
        return

    #######################
    ### Configurations ###
    config_path = os.path.abspath(os.path.join(os.getcwd(), arguments.config))

    print('Loading MudPi Configs \r', end="", flush=True)

    print(chr(27) + "[2J")
    display_greeting()

    manager = CoreManager()
    manager.load_mudpi_from_config(config_path)

    print(f'{"Loading MudPi Configs ":.<{FONT_PADDING+1}} {FONT_GREEN}Complete{FONT_RESET}')

    #####################
    ### Bootstrapping ###
    
    if arguments.debug:
        print(f'{YELLOW_BACK}DEBUG MODE ENABLED{FONT_RESET}')
        manager.mudpi.config.config["mudpi"]["debug"] = True
        # print(arguments) #DEBUG
        print(f'Config path: {config_path}') #DEBUG
        print(f'Current Directory: {os.getcwd()}')
        # print(f'Config keys {mudpi.config.keys()}')
        time.sleep(1)

    # Logging Module
    try:
        print('Initializing Logger \r', end='', flush=True)
        manager.initialize_logging()
    except Exception as e:
        print(f'{"Initializing Logger  ":.<{FONT_PADDING}} {FONT_RED}Disabled{FONT_RESET}')

    # MudPi Core Systems
    manager.load_mudpi_core()

    Logger.log_formatted(LOG_LEVEL["warning"], "Initializing Core ", "Complete", 'success')

    Logger.log(LOG_LEVEL["debug"], f'{" Detecting Configurations ":_^{FONT_PADDING+8}}')
    # Load the Extension System
    loaded_extensions = manager.load_all_extensions()

    Logger.log_formatted(
        LOG_LEVEL["warning"], f"Loaded {len(loaded_extensions)} Extensions ", "Complete", 'success'
    )

    Logger.log_formatted(LOG_LEVEL["warning"], "MudPi Fully Loaded", 'Complete', 'success')

    #########################
    ### Start All Systems ###
    Logger.log(LOG_LEVEL["debug"], f'{" Start Systems ":_^{FONT_PADDING+8}}')
    Logger.log_formatted(LOG_LEVEL["debug"], "Starting All Workers ", 'Pending', 'notice')
    manager.mudpi.start_workers()
    Logger.log_formatted(LOG_LEVEL["info"], "Started All Workers ", 'Complete', 'success')

    # Everything should be loaded and running
    Logger.log_formatted(LOG_LEVEL["info"], "MudPi Systems  ", 'Online', 'success')
    print(f'{"":_<{FONT_PADDING+8}}\n')

    """ Debug Mode Dump After System Online """
    if arguments.debug and arguments.dump:
        manager.debug_dump(cache_dump=arguments.cache_dump)
        time.sleep(1)


    ###############################
    """ MAIN PROGRAM HEARTBEAT """
    manager.mudpi.start()
    PROGRAM_RUNNING = True
    while PROGRAM_RUNNING:
        try:
            # Keep messages being processed
            manager.mudpi.events.get_message()
            current_clock = datetime.datetime.now().replace(microsecond=0)
            manager.mudpi.events.publish('clock', {"clock":current_clock.strftime("%m-%d-%Y %H-%M-%S"), 
                "date":str(current_clock.date()), "time": str(current_clock.time())})
            for i in range(10):
                time.sleep(0.1)
                manager.mudpi.events.get_message()
        except KeyboardInterrupt as error:
            PROGRAM_RUNNING = False
        except Exception as error:
            Logger.log(
                LOG_LEVEL["error"],
                f"Runtime Error:  {error}"
            )
            PROGRAM_RUNNING = False

    """ PROGRAM SHUTDOWN """
    print(f'{"":_<{FONT_PADDING+8}}')
    Logger.log_formatted(
        LOG_LEVEL["info"],
        "Stopping All Workers for Shutdown  ", 'Pending', 'notice'
    )
    manager.shutdown()

    Logger.log_formatted(
        LOG_LEVEL["info"],
        "All MudPi Systems  ", 'Offline', 'error'
    )
    

def get_arguments():
    """ Process program arguments at runtime and decide entry """

    parser = argparse.ArgumentParser(
        description="MudPi: Private Automation for the Garden & Home."
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)
    
    parser.add_argument(
        "-c",
        "--config",
        metavar="path_to_config",
        default=os.path.join(PATH_CONFIG, DEFAULT_CONFIG_FILE),
        help="Set path of the MudPi configuration",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Start MudPi in forced debug mode"
    )
    parser.add_argument(
        "--dump", action="store_true", help="Display important system information"
    )
    parser.add_argument(
        "--cache_dump", action="store_true", help="Display cache when --dump is set"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output."
    )
    parser.add_argument(
        "--make_config", action="store_true", help="Create a default MudPi config file."
    )

    parser.add_argument(
        "--overwrite", 
        action="store_true", 
        default=False,
        help="Overwrite existing config file with [--make_config]."
    )

    parser.add_argument(
        "--migrate_config", 
        metavar="new_config_file",
        default=False,
        help="Convert v0.9 config to new format"
    )

    arguments = parser.parse_args()

    return arguments


def display_greeting():
    """ Print a header with program info for startup """
    greeting =  '███╗   ███╗██╗   ██╗██████╗ ██████╗ ██╗\n'\
                '████╗ ████║██║   ██║██╔══██╗██╔══██╗██║\n'\
                '██╔████╔██║██║   ██║██║  ██║██████╔╝██║\n'\
                '██║╚██╔╝██║██║   ██║██║  ██║██╔═══╝ ██║\n'\
                '██║ ╚═╝ ██║╚██████╔╝██████╔╝██║     ██║\n'\
                '╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝'
    print(FONT_GREEN)
    print(greeting)
    print(f'{"":_<{FONT_PADDING+8}}')
    print('')
    print('Eric Davisson @MudPiApp')
    print('https://mudpi.app')
    print('Version: ', __version__)
    print(FONT_RESET)


def convert_old_config(config):
    """ Convert old v0.9 configs to v0.10+ """
    # Core conversion
    config.config.setdefault("mudpi", {})
    config.config["mudpi"]["name"] = config.config.get("name", "Mudpi")
    config.config["mudpi"]["debug"] = config.config.get("debug", False)
    default_redis = {"host": "127.0.0.1", "port": 6379}
    config.config["mudpi"]["events"] = {"redis": config.config.get("redis", default_redis)}
    config.config["mudpi"]["location"] = {"latitude":40, "longitude":-88 } # Hello Wisconsin!

    # Worker conversion
    if config.config.get("workers"):
        for worker in list(config.config["workers"]):
            if worker["type"].lower() == "sensor":
                for sensor in worker.get('sensors', []):
                    config.config.setdefault("sensor", [])
                    new_sensor = {'key': sensor["key"], 'interface': 'gpio', 'classifier': sensor["type"].lower()}
                    if sensor['type'].lower() == 'humidity':
                        new_sensor['interface'] = 'dht'
                    if sensor.get("name"):
                        new_sensor['name']=sensor['name']
                    if sensor.get("pin"):
                        new_sensor['pin']=sensor['pin']
                    if sensor.get("model"):
                        new_sensor['model']=sensor['model']
                    if sensor.get("percent"):
                        new_sensor['percent']=sensor['percent']
                    if worker.get("sleep_duration"):
                        new_sensor['update_interval']=worker['sleep_duration']
                    config.config['sensor'].append(new_sensor)
            if worker["type"].lower() == "control":
                for control in worker.get('controls', []):
                    config.config.setdefault("control", [])
                    new_control = {'key': control["key"], 'interface': 'gpio', 'type': control["type"].lower()}
                    if control.get("name"):
                        new_control['name']=control['name']
                    if control.get("pin"):
                        new_control['pin']=control['pin']
                    if control.get("topic"):
                        new_control['topic']=control['topic']
                    if control.get("resistor"):
                        new_control['resistor']=control['resistor']
                    if control.get("edge_detection"):
                        new_control['edge_detection']=control['edge_detection']
                    if control.get("debounce"):
                        new_control['debounce']=control['debounce']
                    if worker.get("sleep_duration"):
                        new_control['update_interval']=worker['sleep_duration']
                    config.config['control'].append(new_control)
            if worker["type"].lower() == "i2c":
                for sensor in worker.get('sensors', []):
                    config.config.setdefault("sensor", [])
                    new_sensor = {'key': sensor["key"], 'interface': 'bme680'}
                    if sensor.get("name"):
                        new_sensor['name']=sensor['name']
                    if sensor.get("address"):
                        new_sensor['address']=sensor['address']
                    if sensor.get("model"):
                        new_sensor['model']=sensor['model']
                    if worker.get("sleep_duration"):
                        new_sensor['update_interval']=worker['sleep_duration']
                    config.config['sensor'].append(new_sensor)
            if worker["type"].lower() == "display":
                for display in worker.get('displays', []):
                    config.config.setdefault("char_display", [])
                    new_display = {'key': display["key"], 'interface': 'i2c'}
                    if display.get("name"):
                        new_display['name']=display['name']
                    if display.get("address"):
                        new_display['address']=display['address']
                    if display.get("model"):
                        new_display['model']=display['model']
                    if display.get("topic"):
                        new_display['topic']=display['topic']
                    if worker.get("sleep_duration"):
                        new_display['update_interval']=worker['sleep_duration']
                    config.config['char_display'].append(new_display)
            config.config['workers'].remove(worker)
        del config.config['workers']

    # Relay -> Toggle Converstion
    if config.config.get("relays"):
        for relay in list(config.config["relays"]):
            config.config.setdefault("toggle", [])
            new_toggle = {'key': relay["key"], 'interface': 'gpio'}
            if relay.get("pin"):
                new_toggle['pin']=relay['pin']
            if relay.get("name"):
                new_toggle['name']=relay['name']
            if relay.get("topic"):
                new_toggle['topic']=relay['topic']
            if relay.get("normally_open"):
                new_toggle['invert_state']= not relay['normally_open']
            config.config['toggle'].append(new_toggle)
        del config.config['relays']

    # Action conversion
    if config.config.get("actions"):
        for action in list(config.config["actions"]):
            config.config.setdefault("action", [])
            config.config['action'].append(action)
        del config.config['actions']

    # Trigger conversion
    if config.config.get("triggers"):

        def _add_trigger(_trigger):
            _type = _trigger["type"].lower()
            if _type == 'time':
                _type = 'cron'
            new_trigger = {'key': _trigger["key"], 'interface': _type}
            if _trigger.get("name"):
                new_trigger['name']=_trigger['name']
            if _trigger.get("source"):
                new_trigger['source']=_trigger['source']
            if _trigger.get("nested_source"):
                new_trigger['nested_source']=_trigger['nested_source']
            if _trigger.get("topic"):
                new_trigger['topic']=_trigger['topic']
            if _trigger.get("schedule"):
                new_trigger['schedule']=_trigger['schedule']
            if _trigger.get("frequency"):
                new_trigger['frequency']= _trigger['frequency']
            if _trigger.get("thresholds"):
                new_trigger['thresholds']= _trigger['thresholds']
            if _trigger.get("actions"):
                new_trigger.setdefault('actions', [])
                _actions = []
                for action in _trigger.get("actions", []):
                    _actions.append(f".{action}")
                new_trigger['actions'].extend(_actions)
            if _trigger.get("sequences"):
                new_trigger.setdefault('actions', [])
                _actions = []
                for sequence in _trigger.get("sequences", []):
                    _actions.append(f".{sequence}.next_step")
                new_trigger['actions'].extend(_actions)
            return new_trigger

        for trigger in list(config.config["triggers"]):
            config.config.setdefault("trigger", [])
            # Trigger groups
            if trigger.get('triggers'):
                group_trigger = {'key': trigger["group"].replace(' ', '_').lower(), 'interface': 'group', 'name': trigger['group'], 'triggers': []}
                trig_keys = []
                for trig in trigger.get('triggers', []):
                    new_trigger = _add_trigger(trig)
                    config.config['trigger'].append(new_trigger)
                    trig_keys.append(new_trigger['key'])

                if trigger.get("actions"):
                    group_trigger.setdefault('actions', [])
                    _actions = []
                    for action in trigger.get("actions", []):
                        _actions.append(f".{action}")
                    group_trigger['actions'].extend(_actions)
                if trigger.get("sequences"):
                    group_trigger.setdefault('actions', [])
                    _actions = []
                    for sequence in trigger.get("sequences", []):
                        _actions.append(f".{sequence}.next_step")
                    group_trigger['actions'].extend(_actions)
                group_trigger['triggers']=trig_keys
                config.config['trigger'].append(group_trigger) 
            else:
                config.config['trigger'].append(_add_trigger(trigger)) 
        del config.config['triggers']

    # Sequence conversion
    if config.config.get("sequences"):
        for sequence in list(config.config["sequences"]):
            config.config.setdefault("sequence", [])
            for step in sequence.get('sequence', []):
                if step.get('actions'):
                    _actions = []
                    for action in step['actions']:
                        _actions.append(f".{action}")
                    step['actions'] = _actions
            config.config['sequence'].append(sequence)
        del config.config['sequences']

    # Server socket conversion
    if config.config.get("server"):
        config.config["server"]['key'] = "socket_server"
        config.config["socket"] = [config.config["server"]]
        del config.config['server']

    # Node conversion
    if config.config.get("nodes"):
        for node in list(config.config["nodes"]):
            config.config.setdefault("nanpy", [])
            new_node = {"name": node["name"], "address": node["address"]}
            if node.get("key"):
                new_node['key']=node['key']
            else:
                new_node['key']=node['name'].replace(' ', '_').lower()
            if node.get("use_wifi"):
                new_node['use_wifi']=node['use_wifi']

            # Node sensors
            if node.get("sensors"):
                for sensor in node["sensors"]:
                    config.config.setdefault("sensor", [])
                    new_sensor = {'interface': 'nanpy', "node": new_node['key'], 'classifier': sensor["type"].lower()}
                    if sensor.get("key"):
                        new_sensor['key']=sensor['key']
                    else:
                        new_sensor['key']=sensor['name'].replace(' ', '_').lower()
                    if sensor.get("name"):
                        new_sensor['name']=sensor['name']
                    if sensor.get("pin"):
                        new_sensor['pin']=sensor['pin']
                    if sensor.get("model"):
                        new_sensor['model']=sensor['model']
                    if sensor.get("is_digital"):
                        new_sensor['analog']=not sensor['is_digital']
                    config.config['sensor'].append(new_sensor)

            # Node controls
            if node.get("controls"):
                for control in node["controls"]:
                    config.config.setdefault("control", [])
                    new_control = {'interface': 'nanpy', "node": new_node['key'], 'type': control["type"].lower()}
                    if control.get("key"):
                        new_control['key']=control['key']
                    else:
                        new_control['key']=control['name'].replace(' ', '_').lower()
                    if control.get("name"):
                        new_control['name']=control['name']
                    if control.get("pin"):
                        new_control['pin']=control['pin']
                    if control.get("is_digital"):
                        new_control['analog']=not control['is_digital']
                    if control.get("topic"):
                        new_control['topic']=control['topic']
                    config.config['control'].append(new_control)

            # Node relays
            if node.get("relays"):
                for relay in node["relays"]:
                    config.config.setdefault("toggle", [])
                    new_toggle = {'interface': 'nanpy', "node": new_node['key']}
                    if relay.get("key"):
                        new_toggle['key']=relay['key']
                    else:
                        new_toggle['key']=relay['name'].replace(' ', '_').lower()
                    if relay.get("pin"):
                        new_toggle['pin']=relay['pin']
                    if relay.get("name"):
                        new_toggle['name']=relay['name']
                    if relay.get("topic"):
                        new_toggle['topic']=relay['topic']
                    if relay.get("normally_open"):
                        new_toggle['invert_state']= not relay['normally_open']
                    config.config['toggle'].append(new_toggle)
            config.config["nanpy"].append(new_node)
        del config.config['nodes']

    del config.config['name']
    if config.config.get('redis'):
        del config.config['redis']
    del config.config['debug']

    return config
    
if __name__ == "__main__":
    sys.exit(main())
