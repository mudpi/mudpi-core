import logging
import sys

LOG_LEVEL = {  # low effort enum
    "unknown": logging.NOTSET,
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}


class Logger:

    loggers = {}
    CONFIG = None

    def __init__(self, config: dict):
        if config is None:  # No config given, using sane defaults
            if Logger.CONFIG is None:  # not seen a config before
                config = {
                    'name': 'MudPi',
                    'log_level': logging.WARNING,
                    'log_file': '/tmp/mudpi.log'
                }
            else:
                config = Logger.CONFIG  # use previously seen config
        else:
            Logger.CONFIG = config

        self.log = logging.getLogger(config['name'])  # starting loggers
        try:
            log_level = LOG_LEVEL[config['log_level']]
        except KeyError:
            log_level = LOG_LEVEL['unknown']
        self.log.setLevel(log_level)

        try:
            open(config['log_file'], 'w').close()  # testing file path, error if not valid
            handler = logging.FileHandler(config['log_file'])
            handler.setLevel(log_level)
        except FileNotFoundError or KeyError:
            handler = logging.Handler()
            print("Not going to write log to file ...")

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.WARNING)  # only send WARNING or higher to stdout

        formatter = logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s] %(message)s")
        handler.setFormatter(formatter)

        formatter = logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s] %(message)s",
                                      "%H:%M:%S")
        stream_handler.setFormatter(formatter)

        self.log.addHandler(handler)
        self.log.addHandler(stream_handler)


    @staticmethod
    def get_logger(name: str = "Main", config: dict = None) -> logging.Logger:
        """
        Method to grab the current specified loggers instance or create one if missing
        :param name: loggers name to return, defaults to the Main loggers
        :param config:
        :return:
        """

        if name not in Logger.loggers.keys():
            Logger.loggers[name] = Logger(config).log

            if len(Logger.loggers.keys()) == 1:  # just created main/first logger
                Logger.loggers["Main"] = Logger.loggers[name]
        return Logger.loggers[name]
