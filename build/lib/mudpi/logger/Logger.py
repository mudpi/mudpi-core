import sys
import logging

from mudpi.constants import FONT_RED, FONT_YELLOW, FONT_GREEN, FONT_RESET_CURSOR, \
    FONT_RESET, FONT_PADDING, FONT_RESET, YELLOW_BACK, RED_BACK, GREEN_BACK

LOG_LEVEL = {
    "unknown": logging.NOTSET,
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARN,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


class Logger:
    logger = None

    def __init__(self, config: dict):
        if "logging" in config.keys():
            if config["logging"]:
                logger_config = config["logging"]
            else:
                logger_config = {
                    "file_log_level": "warning",
                    "file": "mudpi.log",
                    "terminal_log_level": "info"
                }
        else:
            logger_config = {
                "file_log_level": "warning",
                "file": "mudpi.log",
                "terminal_log_level": "info"
            }
            # raise Exception("No Logger configs were found!")

        self.__log = logging.getLogger(config.get('mudpi').get('name', 'mudpi') + "_stream")
        self.__file_log = logging.getLogger(config.get('mudpi').get('name', 'mudpi'))

        try:
            file_log_level = LOG_LEVEL[logger_config["file_log_level"]] if not \
            config["mudpi"]["debug"] else LOG_LEVEL["debug"]
            stream_log_level = LOG_LEVEL[
                logger_config["terminal_log_level"]] if not config["mudpi"][
                "debug"] else LOG_LEVEL["debug"]
        except KeyError:
            file_log_level = LOG_LEVEL["unknown"]
            stream_log_level = LOG_LEVEL["unknown"]

        self.__log.setLevel(stream_log_level)
        self.__file_log.setLevel(file_log_level)

        try:
            try:
                if len(logger_config['file']) != 0:
                    open(logger_config['file'],
                         'w').close()  # testing file path
                    file_handler = logging.FileHandler(logger_config['file'])
                    file_handler.setLevel(file_log_level)

                    self.WRITE_TO_FILE = True
                else:
                    self.WRITE_TO_FILE = False
            except FileNotFoundError:
                self.WRITE_TO_FILE = False

        except KeyError as e:
            self.WRITE_TO_FILE = False

            self.log(LOG_LEVEL["warning"],
                     "File Handler could not be started due to a KeyError: {0}".format(
                         e))

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(stream_log_level)

        file_formatter = logging.Formatter(
            "[%(asctime)s][%(name)s][%(levelname)s] %(message)s", "%H:%M:%S")
        stream_formatter = logging.Formatter("%(message)s")
        file_handler.setFormatter(file_formatter)
        stream_handler.setFormatter(stream_formatter)

        if self.WRITE_TO_FILE:
            self.__file_log.addHandler(file_handler)
        self.__log.addHandler(stream_handler)

    @staticmethod
    def log_to_file(log_level: int, msg: str):
        """
        Logs the given message ONLY to the log file.
        """
        if Logger.log is not None:
            Logger.logger.log_this_file(log_level, msg)

    @staticmethod
    def log(log_level, msg: str):  # for ease of access from outside
        """
        Logs the given message to the terminal and possibly file.
        """
        if Logger.log is not None:
            try:
                log_level = int(log_level)
            except ValueError:
                if log_level in LOG_LEVEL:
                    log_level = LOG_LEVEL[log_level]
                else:
                    log_level = LOG_LEVEL['unknown']
            Logger.logger.log_this(log_level, msg)

    @staticmethod
    def log_formatted(log_level, message, status='', status_level=None, padding=FONT_PADDING, spacer="."):
        """ Log a formatted message with a status level """
        status_color = ''
        if status_level == 'success':
            status_color = FONT_GREEN
        elif status_level == 'warning' or status_level == 'notice':
            status_color = FONT_YELLOW
        elif status_level == 'error' or status_level == 'critical':
            status_color = FONT_RED

        # In order to account for hidden characters we manually format message 
        # to allow fstrings to be passed in without breaking the format
        filter_strings = [ FONT_RED, FONT_GREEN, FONT_YELLOW, FONT_RESET, 
        RED_BACK, GREEN_BACK, YELLOW_BACK, FONT_PADDING, FONT_RESET_CURSOR ]

        msg_copy = message
        hidden_char_len = 0

        for filter_item in filter_strings:
            while str(filter_item) in msg_copy:
                hidden_char_len += len(filter_item)
                msg_copy = msg_copy.replace(filter_item, "")

        adjusted_padding = padding - len(message) + hidden_char_len
        msg = message + ' '
        for i in range(adjusted_padding):
            msg += spacer
        msg += ' ' + status_color + status + FONT_RESET
        
        if Logger.log is not None:
            return Logger.logger.log(log_level, msg)

            
        

    def log_this_file(self, log_level, msg):
        msg = str(msg)

        filter_strings = [ FONT_RED, FONT_GREEN, FONT_YELLOW, FONT_RESET, 
        RED_BACK, GREEN_BACK, YELLOW_BACK, FONT_PADDING, FONT_RESET_CURSOR ]

        for filter_item in filter_strings:
            while str(filter_item) in msg:
                msg = msg.replace(str(filter_item), "")

        msg = msg.replace("\x1b", "")
        msg = msg.replace("\033", "")
        msg = msg.replace("[0;0m", "")
        msg = msg.replace("[0m", "")

        self.__file_log.log(log_level, msg)

    def log_this(self, log_level: int, msg: str):
        self.__log.log(log_level, msg)
        if self.WRITE_TO_FILE:
            self.log_this_file(log_level, msg)
