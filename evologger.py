#!/usr/bin/env python3

"""
EvoHome loging application
Reads temperatures from configured input plugins and writes them to configured output plugins
"""
# pylint: disable=C0103,C0301,R0912,R0915,W0703

from datetime import datetime
import getopt
import logging
import signal
import sys
import time
import coloredlogs
from config_helper import get_config, get_string_or_default, is_debugging_enabled
from pluginloader import PluginLoader

logger = None
plugins = None
logging.raiseExceptions = True
continue_polling = True
outside_zone = get_string_or_default('DEFAULT', 'Outside', 'Outside')


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

    config = get_config()
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

    if debug_logging or is_debugging_enabled('DEFAULT'):
        logging.basicConfig(level=logging.DEBUG)
        coloredlogs.install(level='DEBUG')
    else:
        logging.basicConfig(level=logging.INFO)
        coloredlogs.install(level='INFO')

    global logger
    logger = logging.getLogger('evohome-logger::')

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
