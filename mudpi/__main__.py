""" MudPi Main Run File
Author: Eric Davisson (@theDavisson) [EricDavisson.com]
https://mudpi.app

This is the main entry point for running MudPi.
"""
import os
import sys
import time
import argparse
import threading
from mudpi import utils, boot, importer
from .constants import __version__, PATH_CONFIG, DEFAULT_CONFIG_FILE, FONT_RESET_CURSOR, FONT_RESET, YELLOW_BACK, GREEN_BACK, FONT_GREEN, FONT_RED, FONT_YELLOW, FONT_PADDING
from .exceptions import ConfigNotFoundError, ConfigFormatError
from .core import MudPi
from .logger.Logger import Logger, LOG_LEVEL


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
        mudpi = MudPi()
        if os.path.exists(config_location) and not arguments.overwrite:
            print(f'{FONT_RED}{"File already exists and `--overwrite` was not set."}{FONT_RESET}')
            return
        mudpi.config.save_to_file(config_location)
        return


    ### Configurations ###
    config_path = os.path.abspath(os.path.join(os.getcwd(), arguments.config))

    print('Loading MudPi Configs \r', end="", flush=True)

    print(chr(27) + "[2J")
    display_greeting()

    mudpi = MudPi()
    boot.mudpi_from_config(mudpi, config_path)

    print(f'{"Loading MudPi Configs ":.<{FONT_PADDING+1}} {FONT_GREEN}Complete{FONT_RESET}')


    ### Bootstrapping ###
    
    if arguments.debug:
        print(f'{YELLOW_BACK}DEBUG MODE ENABLED{FONT_RESET}')
        mudpi.config.config["mudpi"]["debug"] = True
        print(arguments) #DEBUG
        print(f'Config path: {config_path}') #DEBUG
        print(f'Current Directory: {os.getcwd()}')
        # print(f'Config keys {mudpi.config.keys()}')
        time.sleep(1)

    # Logging Module
    try:
        print('Initializing Logger \r', end='', flush=True)
        boot.initialize_logging(mudpi)
    except Exception as e:
        print(f'{"Initializing Logger  ":.<{FONT_PADDING}} {FONT_RED}Disabled{FONT_RESET}')

    boot.load_mudpi_core(mudpi)

    Logger.log_formatted(
        LOG_LEVEL["warning"], "Initializing Core ", "Complete", 'success'
    )

    loaded_extensions = boot.load_all_extensions(mudpi)

    Logger.log_formatted(
        LOG_LEVEL["warning"], f"Loaded {len(loaded_extensions)} Prepared Extensions ", "Complete", 'success'
    )


    # #########################
    # ### Register Workers ###
    #     for worker in mudpi.config.workers:
    #         worker_type = f'linux.{worker["type"]}_worker'
    #         wrker = importer.get_worker(worker_type)
    #         # Worker import magic
    #         if wrker:
    #             clss = [item for item in utils.get_module_classes(wrker.__name__) if 'Worker' in item[0] and item[0] is not "Worker"]
    #             worker_instance = clss[0][1](mudpi, worker)
    #             registered_worker_count += 1
    #         else:  
    #             # Unable to import module
    #             Logger.log(
    #                 LOG_LEVEL["error"],
    #                 f'{f"Failed Loading {worker_type} ":.<{FONT_PADDING}} {FONT_RED}Failed{FONT_RESET}'
    #             )
    #     

    Logger.log_formatted(
        LOG_LEVEL["warning"],
        "Booting MudPi ", 'Complete', 'success'
    )


    #########################
    ### Start All Systems ###
    Logger.log_formatted(
        LOG_LEVEL["info"],
        "Signaling All Workers to Start ", 'Pending', 'notice'
    )
    # for worker in mudpi.worker_registry:
    #     t = mudpi.worker_registry[worker].run()
    #     mudpi.threads.append(t)
    
    mudpi.start()
    Logger.log_formatted(
        LOG_LEVEL["info"],
        "Signaling All Workers to Start  ", 'Complete', 'success'
    )
    print(f'{"":_<{FONT_PADDING+8}}')
    print('')


    """ Debug Mode Dump After System Online """
    if arguments.debug:
        debug_dump(mudpi)


    """ PROGRAM SHUTDOWN """
    time.sleep(5)
    mudpi.shutdown()

    for thread in mudpi.threads:
        thread.join()

    # Check the config
    # 
    # Check other options before running
    # 
    # Boot Up MudPi
    #  - MudPi Set to LOADING
    #  - Load the Config from Conf Path
    #  - Load the MudPi Core Components
    #       - Load the Event Bus (redis)
    #       - Load the State Manager (redis)
    #  - Load all Workers and Register Them
    #       - Workers initalize components
    #  
    #  - MudPi Set to STARTING
    #  - Set Threading Event for Core
    #  - Start Up all Registered Workers
    #  
    #  - MudPi Set to RUNNING
    

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


def debug_dump(mudpi):
    """ Dump important data from MudPi instance for debugging mode """
    Logger.log(
        LOG_LEVEL["debug"],
        f'{YELLOW_BACK}MUDPI CACHE DUMP{FONT_RESET}'
    )
    for key in mudpi.cache.keys():
        Logger.log(
            LOG_LEVEL["debug"],
            f"{FONT_YELLOW}{key}:{FONT_RESET} {mudpi.cache[key]}"
        )

    Logger.log(
        LOG_LEVEL["debug"],
        f'{YELLOW_BACK}MUDPI LOADED EXTENSIONS{FONT_RESET}'
    )
    for ext in mudpi.extensions.all():
        ext = mudpi.cache.get("extension_importers", {}).get(ext)
        Logger.log(
            LOG_LEVEL["debug"],
            f"Namespace: {FONT_YELLOW}{ext.namespace}{FONT_RESET}\n{ext.description}\n{ext.documentation}"
        )      

    if mudpi.components.all():
        Logger.log(
            LOG_LEVEL["debug"],
            f'{YELLOW_BACK}MUDPI REGISTERED COMPONENTS{FONT_RESET}'
        )
        Logger.log(
            LOG_LEVEL["debug"],
            f"{'COMPONENT':<10}   {'ID':<20}   NAME\n{'':-<60}"
        )
        for comp in mudpi.components.all():
            comp = mudpi.components.get(comp)
            Logger.log(
                LOG_LEVEL["debug"],
                f"{comp.__class__.__name__:<10} | {comp.id:<20} | {comp.name}"
            )

    if mudpi.actions.all():
        Logger.log(
            LOG_LEVEL["debug"],
            f'{YELLOW_BACK}MUDPI REGISTERED ACTIONS{FONT_RESET}'
        )
        Logger.log(
            LOG_LEVEL["debug"],
            f"{'ACTION CALL':<24}   {'ACTION':<20}   NAMESPACE\n{'':-<60}"
        )
        for namespace, actions in mudpi.actions.items():
            for key, action in actions.items():
                action_command = f"{namespace}.{key}" if namespace else key
                Logger.log(
                    LOG_LEVEL["debug"],
                    f"{action_command:<24} | {key:<20} | {namespace}"
                )                         

if __name__ == "__main__":
    sys.exit(main())
