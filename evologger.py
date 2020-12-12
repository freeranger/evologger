#!/usr/bin/env python3

import time
from datetime import datetime
from pluginloader import PluginLoader
from config_helper import *
import sys, getopt

logging.raiseExceptions = True

config = configparser.ConfigParser(allow_no_value=True)
config.read('config.ini')

logger = None
plugins = None


def get_temperatures():
    temperatures = []
    for i in plugins.inputs:
        plugin = plugins.get(i)
        if plugin is None:
            logger.error("plugin is none!: " + i)
        else:
            logger.debug('Reading temperatures from %s', plugin.plugin_name)
            try:
                temps = plugin.read()
                if not temps:
                    continue

            except Exception as  e:
                logger.error("Error reading temps from %s: $s", plugin.plugin_name, e)
                return []

            for t in temps:
                temperatures.append(t)

    # Sort by zone name, with hot water on the end and finally 'Outside'
    temperatures = sorted(temperatures, key=lambda t: (t.zone == 'Hot Water' or t.zone == 'Outside', t.zone == 'Outside', t.zone))
    return temperatures


def main(argv):

    polling_interval = config.getint('EvoHome', 'pollingInterval')
    debug_logging = False

    try:
        opts, args = getopt.getopt(argv, "hdi:", ["help","interval", "debug="])
    except getopt.GetoptError:
        print('evologger.py -h for help')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print('evologger, version 0.2')
            print('')
            print('usage:  evologger.py [-h|--help] [-d|--debug <true|false>] [-i|--interval <interval>]')
            print('')
            print(' h|help                : display this help page')
            print(' d|debug               : turn on debug logging, regardless of the config.ini setting')
            print(' i|interval <interval> : Log temperatures every <polling interval> seconds, overriding the config.ini value')
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
    else:
        logging.basicConfig(level=logging.INFO)

    global logger
    logger = logging.getLogger('evohome-logger::')

    if polling_interval == 0:
        logger.debug('One-off run')
    else:
        logger.debug('Polling every %s seconds', polling_interval)

    logger.info("==Started==")

    global plugins
    sections = filter(lambda a: a.lower() != 'DEFAULT', config.sections())
    plugins = PluginLoader(sections)

    continue_polling = True
    try:
        while continue_polling:
            timestamp = datetime.utcnow()
            timestamp = timestamp.replace(microsecond=0)

            temperatures = get_temperatures()

            if temperatures:
                text_temperatures = '%s: ' % datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                for t in temperatures:
                    text_temperatures += "%s (%s A" % (t.zone, t.actual)
                    if t.target is not None:
                        text_temperatures += ", %s T" % t.target
                    text_temperatures += ') '

                logger.info(text_temperatures)

                for i in plugins.outputs:
                    plugin = plugins.get(i)
                    logger.debug('Writing temperatures to %s', plugin.plugin_name)
                    try:
                        plugin.write(timestamp, temperatures)
                    except Exception as e:
                        logger.error('Error trying to write to %s: %s', plugin.plugin_name, str(e))

            if polling_interval == 0:
                continue_polling = False
            else:
                logger.info("Going to sleep for %s minutes", (polling_interval/60))
                time.sleep(polling_interval)

    except Exception as e:
        logger.error('An error occurred, trying again in 15 seconds: %s', str(e))
        time.sleep(15)

    logger.info("==Finished==")


if __name__ == '__main__':
    main(sys.argv[1:])
