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
        Config().save_to_file(config_path)
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
    if arguments.debug:
        manager.debug_dump()
        time.sleep(1)

    ###############################
    """ MAIN PROGRAM HEARTBEAT """
    manager.mudpi.start()
    PROGRAM_RUNNING = True
    while PROGRAM_RUNNING:
        try:
            current_clock = datetime.datetime.now().replace(microsecond=0)
            manager.mudpi.events.publish('clock', {"clock":current_clock.strftime("%m-%d-%Y %H-%M-%S"), 
                "date":str(current_clock.date()), "time": str(current_clock.time())})
            time.sleep(1)
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
    manager.mudpi.shutdown()

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


if __name__ == "__main__":
    sys.exit(main())
