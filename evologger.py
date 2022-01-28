#!/usr/bin/env python3

"""
EvoHome loging application
Reads temperatures from configured input plugins and writes them to configured output plugins
"""
# pylint: disable=R0912,R0915,W0603

from datetime import datetime
import getopt
import http
import logging.config
import signal
import sys
import time
import requests # we need to import requests even though it is not explicitly used so we get access to http.client
import structlog
from config_helper import get_config, get_boolean_or_default, get_string_or_default, is_debugging_enabled
from pluginloader import PluginLoader


logger = None
plugins = None
logging.raiseExceptions = True
continue_polling = True
outside_zone = get_string_or_default('DEFAULT', 'Outside', 'Outside')

config = get_config()

def handle_signal(sig, _):
    """
    SIGTERM/SIGINT signal handler to flag the application to stop.
    """

    signal_name = signal.Signals(sig).name
    msg = f'Signal {signal_name} received, terminating the application.'
    if logger is not None:
        logger.info(msg)
    else:
        print(msg)
    global continue_polling
    continue_polling = False

    raise SystemExit(msg)

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def configure_logging(log_level):
    """
    Configures logging using structlog
    """
    timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
    pre_chain = [
        # Add the log level and a timestamp to the event_dict if the log entry
        # is not from structlog.
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        # Add extra attributes of LogRecord objects to the event dictionary
        # so that values passed in the extra parameter of log methods pass
        # through to log output.
        structlog.stdlib.ExtraAdder(),
        timestamper,
    ]
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                   structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                   structlog.dev.ConsoleRenderer(colors=False),
                ],
                "foreign_pre_chain": pre_chain,
            },
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                   structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                   structlog.dev.ConsoleRenderer(colors=True),
                ],
                "foreign_pre_chain": pre_chain,
            },
        },
        "handlers": {
            "default": {
                "level": logging.getLevelName(log_level),
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
            "file": {
                "level": logging.getLevelName(logging.DEBUG),
                "class": "logging.handlers.WatchedFileHandler",
                "filename": "evologger.log",
                "formatter": "plain",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default", "file"],
                "level": "DEBUG",
                "propagate": True,
            },
        }
    })

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    global logger
    logger = structlog.get_logger('evohome-logger')

    if get_boolean_or_default('DEFAULT', 'httpDebug', False) is True:
        http_logger = structlog.get_logger('http-logger')
        def print_http_debug_to_log(*args):
            http_logger.debug(" ".join(args))
        http.client.HTTPConnection.debuglevel = 5
        http.client.print = print_http_debug_to_log


def read_temperatures():
    """
    Reads the temperatures from the input plugins
    """
    temperatures = []
    for i in plugins.inputs:
        plugin = plugins.load(i)
        if plugin is None:
            logger.error("plugin is none!: %s", i)
        else:
            logger.debug("Reading temperatures from %s", plugin.plugin_name)
            try:
                temps = plugin.read()
                if not temps:
                    continue

            except Exception as  e:
                logger.exception("Error reading temps from %s: %s", plugin.plugin_name, str(e))
                return []

            for t in temps:
                temperatures.append(t)

    # Sort by zone name, with hot water on the end and finally 'Outside'
    temperatures = sorted(temperatures, key=lambda t: (t.zone in ('Hot Water', outside_zone), t.zone == outside_zone, t.zone))
    return temperatures


def publish_temperatures(temperatures):
    """
    Publishes the temperatures to the output plugins
    """

    if temperatures:
        timestamp = datetime.utcnow()
        timestamp = timestamp.replace(microsecond=0)

        text_temperatures = f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}: '
        for t in temperatures:
            text_temperatures += f'{t.zone} ({t.actual} A'
            if t.target is not None:
                text_temperatures += f', {t.target} T'
            text_temperatures += ') '

        logger.debug(text_temperatures)

        for i in plugins.outputs:
            plugin = plugins.load(i)
            logger.debug("Writing temperatures to %s", plugin.plugin_name)
            try:
                plugin.write(timestamp, temperatures)
            except Exception as e:
                logger.exception("Error trying to write to %s: %s", plugin.plugin_name, str(e))


def main(argv):
    """
    Main appliction entry point
    """

    polling_interval = config.getint('EvoHome', 'pollingInterval')
    debug_logging = False

    try:
        opts, _ = getopt.getopt(argv, "hdi:", ["help","interval", "debug="])
    except getopt.GetoptError:
        print('evologger.py -h for help')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print('evologger, version 2.0')
            print('')
            print('usage:  evologger.py [-h|--help] [-d|--debug <true|false>] [-i|--interval <interval>]')
            print('')
            print(' h|help                 : display this help page')
            print(' d|debug                : turn on debug logging, regardless of the config.ini setting')
            print(' i|interval <interval>  : Log temperatures every <polling interval> seconds, overriding the config.ini value')
            print('                         If 0 is specified then temperatures are logged only once and the program exits')
            print('')
            sys.exit()
        elif opt in ('-i', '--interval'):
            if arg.isdigit():
                polling_interval = int(arg)
        elif opt in ('-d', '--debug'):
            debug_logging = True

    configure_logging(logging.DEBUG if debug_logging or is_debugging_enabled('DEFAULT') else logging.INFO)

    logger.info("==Started==")

    global plugins
    sections = filter(lambda a: a.lower() != 'DEFAULT', config.sections())
    plugins = PluginLoader(sections, './plugins')

    if polling_interval == 0:
        logger.info('One-off run, existing after a single publish')
    else:
        logger.info(f'Polling every {(polling_interval/60):.2g} minutes...')

    try:
        global continue_polling
        while continue_polling:
            publish_temperatures(read_temperatures())

            if polling_interval == 0:
                continue_polling = False
            else:
                logger.debug(f'Going to sleep for {(polling_interval/60):.2g} minutes')
                time.sleep(polling_interval)

    except SystemExit:
        pass
    except Exception as e:
        logger.exception("An error occurred, trying again in 15 seconds: %s", str(e))
        time.sleep(15)

    logger.info("==Finished==")


if __name__ == '__main__':
    main(sys.argv[1:])
