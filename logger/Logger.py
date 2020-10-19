import logging
import sys


LOG_LEVEL = {
    "unknown": logging.NOTSET,
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARN,
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
}

class Logger:

    logger = None

    def __init__(self, config: dict):
        if "logging" in config.keys():
            logger_config = config["logging"]
        else:
            raise Exception("No Logger configs were found!")
        
        self.__log = logging.getLogger(config['name']+"_stream")
        self.__file_log = logging.getLogger(config['name'])

        try:
            file_log_level = LOG_LEVEL[logger_config["file_log_level"]] if not config["debug"] else LOG_LEVEL["debug"]
            stream_log_level = LOG_LEVEL[logger_config["terminal_log_level"]] if not config["debug"] else LOG_LEVEL["debug"]
        except KeyError:
            file_log_level = LOG_LEVEL["unknown"]
            stream_log_level = LOG_LEVEL["unknown"]
        
        self.__log.setLevel(stream_log_level)
        self.__file_log.setLevel(file_log_level)

        try:
            try:
                if len(logger_config['file']) != 0:
                    open(logger_config['file'], 'w').close()  # testing file path
                    file_handler = logging.FileHandler(logger_config['file'])
                    file_handler.setLevel(file_log_level)

                    self.WRITE_TO_FILE = True
                else:
                    self.WRITE_TO_FILE = False
            except FileNotFoundError:
                self.WRITE_TO_FILE = False
        
        except KeyError as e:
            self.WRITE_TO_FILE = False

            self.log(LOG_LEVEL["warning"], "File Handler could not be started due to a KeyError: {0}".format(e))
        
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(stream_log_level)

        file_formatter = logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s] %(message)s", "%H:%M:%S")
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
    def log(log_level: int, msg: str):  # for ease of access from outside
        """
        Logs the given message to the terminal and possibly file.
        """
        if Logger.log is not None:
            Logger.logger.log_this(log_level, msg)

    def log_this_file(self, log_level: int, msg: str):
        msg = msg.replace("\x1b[1;32m", "")
        msg = msg.replace("\x1b[0;0m", "")
        msg = msg.replace("\x1b[1;31m", "")
        self.__file_log.log(log_level, msg)
    
    def log_this(self, log_level: int, msg: str):
        self.__log.log(log_level, msg)
        if self.WRITE_TO_FILE:
            self.log_this_file(log_level, msg)
