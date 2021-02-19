import sys
import json
import time
import redis
import threading
import digitalio

from mudpi.workers import Worker

from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.constants import __version__, PATH_CONFIG, DEFAULT_CONFIG_FILE, FONT_RESET_CURSOR, FONT_RESET, YELLOW_BACK, GREEN_BACK, FONT_GREEN, FONT_RED, FONT_YELLOW, FONT_PADDING

try:
    import board
    SUPPORTED_DEVICE = True
except:
    SUPPORTED_DEVICE = False


class RelayWorker(Worker):
    def __init__(self, mudpi, config):
        super().__init__(mudpi, config)

        if self.config.get('key', None) is None:
            raise Exception('No "key" Found in Relay Config')
        else:
            self.key = self.config.get('key', '').replace(" ", "_").lower()

        if self.config.get('name', None) is None:
            self.name = self.key.replace("_", " ").title()
        else:
            self.name = self.config['name']


        if SUPPORTED_DEVICE:
            self.pin_obj = getattr(board, self.config['pin'])

        # Events
        if self.config.get("thread_events"):
            self.relay_available = self.config["thread_events"].get("relay_available")
            self.relay_active = self.config["thread_events"].get("relay_active")
        else:
            self.config["thread_events"] = {}
            self.relay_available = self.config["thread_events"]["relay_available"] = threading.Event()
            self.relay_active = self.config["thread_events"]["relay_active"] = threading.Event()

        # Dynamic Properties based on config
        self.active = False
        self.topic = self.config.get('topic', '').replace(" ",
                                                          "/").lower() if self.config.get(
            'topic', None) is not None else 'mudpi/relays/' + self.key
        self.pin_state_off = True if self.config[
                                         'normally_open'] is not None and \
                                     self.config['normally_open'] else False
        self.pin_state_on = False if self.config[
                                         'normally_open'] is not None and \
                                     self.config['normally_open'] else True

        config = self.config

        # Pubsub Listeners
        try:
            self.r = self.config["redis"]
        except KeyError:
            self.r = redis.Redis(host='127.0.0.1', port=6379)

        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe(**{self.topic: self.handle_message})

        self.init()
        return

    def init(self):
        super().init()
        if SUPPORTED_DEVICE:
            Logger.log(
                LOG_LEVEL["info"],
                f'{f"Relay Worker {self.key}":.<{FONT_PADDING}} {FONT_YELLOW}Initializing{FONT_RESET}'
            )
            self.gpio_pin = digitalio.DigitalInOut(self.pin_obj)
            self.gpio_pin.switch_to_output()
            # Close the relay by default, we use the pin state
            # we determined based on the config at init
            self.gpio_pin.value = self.pin_state_off
            time.sleep(0.1)

            # Feature to restore relay state in case of crash
            # or unexpected shutdown. This will check for last state
            # stored in redis and set relay accordingly
            if (self.config.get('restore_last_known_state',
                                None) is not None and self.config.get(
                'restore_last_known_state', False) is True):
                if self.r.get(self.key + '_state'):
                    self.gpio_pin.value = self.pin_state_on
                    Logger.log(
                        LOG_LEVEL["info"],
                        'Restoring Relay \033[1;36m{0} On\033[0;0m'.format(
                            self.key)
                    )

            # Logger.log(
            #     LOG_LEVEL["info"],
            #     'Relay Worker {0}...\t\t\t\033[1;32m Ready\033[0;0m'.format(self.key)
            # )
        return

    def run(self):
        Logger.log(
            LOG_LEVEL["warning"],
            f'{f"Relay Worker {self.key}":.<{FONT_PADDING}} {FONT_GREEN}Working{FONT_RESET}'
        )
        return super().run()

    def handle_message(self, message):
        data = message['data']
        if data is not None:
            decoded_message = self.decode_message_data(data)

            try:
                if decoded_message['event'] == 'Switch':
                    if decoded_message.get('data', None):
                        self.relay_active.set()

                    elif decoded_message.get('data', None) == 0:
                        self.relay_active.clear()
                    Logger.log(
                        LOG_LEVEL["info"],
                        'Switch Relay \033[1;36m{0}\033[0;0m state to \033[1;36m{1}\033[0;0m'.format(
                            self.key, decoded_message['data'])
                    )

                elif decoded_message['event'] == 'Toggle':
                    state = 'Off' if self.active else 'On'

                    if self.relay_active.is_set():
                        self.relay_active.clear()

                    else:
                        self.relay_active.set()
                    Logger.log(
                        LOG_LEVEL["info"],
                        'Toggle Relay \033[1;36m{0} {1} \033[0;0m'.format(
                            self.key, state)
                    )
            except Exception:
                Logger.log(
                    LOG_LEVEL["error"],
                    'Error Decoding Message for Relay {0}'.format(
                        self.key)
                )

    def turn_on(self):
        # Turn on relay if its available
        if SUPPORTED_DEVICE:
            if self.relay_available.is_set():
                if not self.active:
                    self.gpio_pin.value = self.pin_state_on
                    message = {'event': 'StateChanged', 'data': 1}
                    self.r.set(self.key + '_state', 1)
                    self.r.publish(self.topic, json.dumps(message))
                    self.active = True
                    # This is handled by the redis listener now
                    # self.relay_active.set()
                    self.reset_elapsed_time()

    def turn_off(self):
        # Turn off volkeye to flip off relay
        if SUPPORTED_DEVICE:
            if self.relay_available.is_set():
                if self.active:
                    self.gpio_pin.value = self.pin_state_off
                    message = {'event': 'StateChanged', 'data': 0}
                    self.r.delete(self.key + '_state')
                    self.r.publish(self.topic, json.dumps(message))
                    #  This is handled by the redis listener now
                    # self.relay_active.clear()
                    self.active = False
                    self.reset_elapsed_time()

    def work(self):
        self.reset_elapsed_time()
        while self.mudpi.thread_events["mudpi_running"].is_set():
            if self.mudpi.thread_events["core_running"].is_set():

                try:
                    self.pubsub.get_message()
                    if self.relay_available.is_set():
                        if self.relay_active.is_set():
                            self.turn_on()
                        else:
                            self.turn_off()
                    else:
                        self.turn_off()
                        time.sleep(1)
                except Exception:
                    Logger.log(
                        LOG_LEVEL["error"],
                        "Relay Worker \033[1;36m{0}\033[0;0m \t\033[1;31m Unexpected Error\033[0;0m".format(
                            self.key)
                    )

            else:
                # System not ready relay should be off
                self.turn_off()
                time.sleep(1)
                self.reset_elapsed_time()

            time.sleep(0.1)

        # This is only ran after the main thread is shut down
        Logger.log(LOG_LEVEL["info"],
                   f"{f'Relay [{self.key}]...':.<{FONT_PADDING}} {FONT_YELLOW}Stopping{FONT_RESET}")
        # Close the pubsub connection
        self.pubsub.close()
        Logger.log(LOG_LEVEL["warning"],
                   f"{f'Relay [{self.key}]...':.<{FONT_PADDING}} {FONT_RED}Shutdown{FONT_RESET}")
